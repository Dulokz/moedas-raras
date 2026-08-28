import io
import math
import numpy as np
import cv2
from PIL import Image
from typing import Tuple, List, Dict, Optional

from backend.config import NORM_SIZE, CONFIDENCE_STRONG, CONFIDENCE_MEDIUM
from backend.services.catalog import catalog_service
from backend.models.schema import IdentifyResponse, Candidate, CatalogItem


class VisionEngine:
    def __init__(self):
        self.orb = cv2.ORB_create(nfeatures=1200, scaleFactor=1.2, nlevels=8)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self.reference_index: Dict[str, Dict[str, List[Dict]]] = {}

    def decode_image(self, image_bytes: bytes) -> np.ndarray:
        """Decodes raw byte string to OpenCV BGR numpy array."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Não foi possível decodificar a imagem fornecida.")
        return img

    def balance_white(self, img_bgr: np.ndarray) -> np.ndarray:
        """Applies Gray World white-balance algorithm to neutralize room lighting color casts (purple, blue, yellow)."""
        b, g, r = cv2.split(img_bgr)
        b_avg, g_avg, r_avg = np.mean(b), np.mean(g), np.mean(r)
        if b_avg == 0 or g_avg == 0 or r_avg == 0:
            return img_bgr
        k = (b_avg + g_avg + r_avg) / 3.0
        b_balanced = np.clip(b * (k / b_avg), 0, 255).astype(np.uint8)
        g_balanced = np.clip(g * (k / g_avg), 0, 255).astype(np.uint8)
        r_balanced = np.clip(r * (k / r_avg), 0, 255).astype(np.uint8)
        return cv2.merge([b_balanced, g_balanced, r_balanced])

    def crop_and_normalize(self, img_bgr: np.ndarray) -> Tuple[np.ndarray, Image.Image]:
        """White-balances, detects coin circle mask, crops precisely, normalizes background and resizes."""
        img_balanced = self.balance_white(img_bgr)

        h, w = img_balanced.shape[:2]
        gray = cv2.cvtColor(img_balanced, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 1.5)

        # 1. Otsu thresholding & contour bounding circle to locate coin
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        cx, cy, r = w // 2, h // 2, min(w, h) // 2

        if contours:
            c_max = max(contours, key=cv2.contourArea)
            (x_c, y_c), r_c = cv2.minEnclosingCircle(c_max)
            if r_c > min(w, h) * 0.15:
                cx, cy, r = int(x_c), int(y_c), int(r_c)

        # 2. Hough Circles refine if available
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=h//3,
            param1=100, param2=30, minRadius=int(min(h, w)*0.2), maxRadius=int(min(h, w)*0.48)
        )

        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            best_circle = min(circles, key=lambda c: (c[0]-w/2)**2 + (c[1]-h/2)**2)
            cx, cy, r = best_circle[0], best_circle[1], best_circle[2]

        margin = int(r * 1.02)
        x1 = max(0, cx - margin)
        y1 = max(0, cy - margin)
        x2 = min(w, cx + margin)
        y2 = min(h, cy + margin)

        cropped_bgr = img_balanced[y1:y2, x1:x2]
        if cropped_bgr.size == 0:
            cropped_bgr = img_balanced

        resized_bgr = cv2.resize(cropped_bgr, (NORM_SIZE, NORM_SIZE), interpolation=cv2.INTER_AREA)

        mask = np.zeros((NORM_SIZE, NORM_SIZE), dtype=np.uint8)
        cv2.circle(mask, (NORM_SIZE // 2, NORM_SIZE // 2), int(NORM_SIZE * 0.48), 255, -1)
        masked_bgr = cv2.bitwise_and(resized_bgr, resized_bgr, mask=mask)

        pil_img = Image.fromarray(cv2.cvtColor(masked_bgr, cv2.COLOR_BGR2RGB))
        return masked_bgr, pil_img

    def detect_bimetallic(self, img_bgr: np.ndarray) -> Tuple[bool, float]:
        """Analyzes core vs outer ring color distribution to detect bimetallic R$1 signature."""
        h, w = img_bgr.shape[:2]
        balanced = self.balance_white(img_bgr)
        hsv = cv2.cvtColor(balanced, cv2.COLOR_BGR2HSV)
        
        mask_core = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask_core, (w//2, h//2), int(min(w, h)*0.24), 255, -1)

        mask_ring = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask_ring, (w//2, h//2), int(min(w, h)*0.45), 255, -1)
        cv2.circle(mask_ring, (w//2, h//2), int(min(w, h)*0.28), 0, -1)

        core_hsv = hsv[mask_core > 0]
        ring_hsv = hsv[mask_ring > 0]

        if len(core_hsv) == 0 or len(ring_hsv) == 0:
            return False, 0.0

        core_gold_count = np.sum((core_hsv[:, 0] >= 5) & (core_hsv[:, 0] <= 48) & (core_hsv[:, 1] >= 20))
        core_gold_ratio = core_gold_count / len(core_hsv)

        ring_silver_count = np.sum(ring_hsv[:, 1] < 65)
        ring_silver_ratio = ring_silver_count / len(ring_hsv)

        bimetallic_score = (core_gold_ratio * 0.6) + (ring_silver_ratio * 0.4)
        is_bimetallic = core_gold_ratio > 0.12 and ring_silver_ratio > 0.20
        return is_bimetallic, float(bimetallic_score)

    def extract_features(self, pil_img: Image.Image) -> Dict:
        """Extracts CLAHE-normalized intensity grid, HSV histograms, and ORB keypoints."""
        img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        balanced = self.balance_white(img_bgr)
        gray = cv2.cvtColor(balanced, cv2.COLOR_BGR2GRAY)
        
        gray_norm = self.clahe.apply(gray)

        kp, des = self.orb.detectAndCompute(gray_norm, None)

        spatial_gray = cv2.resize(gray_norm, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)
        spatial_gray = (spatial_gray - np.mean(spatial_gray)) / (np.std(spatial_gray) + 1e-5)

        hsv = cv2.cvtColor(balanced, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        return {
            "keypoints": kp,
            "descriptors": des,
            "spatial_grid": spatial_gray,
            "histogram": hist
        }

    def extract_rotational_features(self, pil_img: Image.Image) -> List[Dict]:
        """Extracts features for cardinal rotations (0°, 90°, 180°, 270°) for rotation invariance."""
        feats = []
        for angle in [0, 90, 180, 270]:
            rot_img = pil_img.rotate(angle, resample=Image.BICUBIC, expand=False)
            feats.append(self.extract_features(rot_img))
        return feats

    def register_reference(self, coin_id: str, obverse_img: Image.Image, reverse_img: Image.Image):
        """Registers reference features for a coin in the index."""
        obv_bgr = cv2.cvtColor(np.array(obverse_img), cv2.COLOR_RGB2BGR)
        rev_bgr = cv2.cvtColor(np.array(reverse_img), cv2.COLOR_RGB2BGR)

        _, obv_pil = self.crop_and_normalize(obv_bgr)
        _, rev_pil = self.crop_and_normalize(rev_bgr)

        obv_feats = self.extract_rotational_features(obv_pil)
        rev_feats = self.extract_rotational_features(rev_pil)
        self.reference_index[coin_id] = {
            "obverse": obv_feats,
            "reverse": rev_feats
        }

    def match_features(self, feat_a: Dict, feat_b: Dict) -> Dict:
        """Calculates detailed multi-signal visual match metrics."""
        grid_a = feat_a["spatial_grid"]
        grid_b = feat_b["spatial_grid"]

        ncc = np.sum(grid_a * grid_b) / (grid_a.size)
        ncc_score = max(0.0, float((ncc + 1.0) / 2.0))

        hist_a = feat_a["histogram"]
        hist_b = feat_b["histogram"]
        hist_score = max(0.0, float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)))

        des_a = feat_a.get("descriptors")
        des_b = feat_b.get("descriptors")
        orb_score = 0.0
        good_matches_count = 0
        if des_a is not None and des_b is not None and len(des_a) > 5 and len(des_b) > 5:
            matches = self.bf.match(des_a, des_b)
            if matches:
                good_matches = [m for m in matches if m.distance < 60]
                good_matches_count = len(good_matches)
                orb_score = min(1.0, good_matches_count / 12.0)

        combined = (ncc_score * 0.45) + (orb_score * 0.40) + (hist_score * 0.15)
        return {
            "combined": float(combined),
            "ncc": float(ncc_score),
            "orb_inliers": good_matches_count,
            "hist": float(hist_score)
        }

    def match_pair(self, front_img: Image.Image, back_img: Image.Image) -> Dict[str, Dict]:
        """Compares front & back images against registered references and returns side-specific metric breakdowns."""
        f_feats = self.extract_rotational_features(front_img)
        b_feats = self.extract_rotational_features(back_img)

        coin_match_details: Dict[str, Dict] = {}

        for coin_id, ref in self.reference_index.items():
            obv_refs = ref["obverse"]
            rev_refs = ref["reverse"]

            # Direct orientation (front = obverse, back = reverse)
            direct_pairs = [(self.match_features(ff, ro), self.match_features(bf, rr))
                            for ff in f_feats for ro in obv_refs
                            for bf in b_feats for rr in rev_refs]
            best_direct = max(direct_pairs, key=lambda x: (x[0]["combined"] + x[1]["combined"]) / 2.0)

            # Swapped orientation (front = reverse, back = obverse)
            swapped_pairs = [(self.match_features(ff, rr), self.match_features(bf, ro))
                             for ff in f_feats for rr in rev_refs
                             for bf in b_feats for ro in obv_refs]
            best_swapped = max(swapped_pairs, key=lambda x: (x[0]["combined"] + x[1]["combined"]) / 2.0)

            dir_score = (best_direct[0]["combined"] + best_direct[1]["combined"]) / 2.0
            swap_score = (best_swapped[0]["combined"] + best_swapped[1]["combined"]) / 2.0

            if dir_score >= swap_score:
                best_obv_side = best_direct[0]
                best_rev_side = best_direct[1]
                best_combined = dir_score
            else:
                best_obv_side = best_swapped[1]
                best_rev_side = best_swapped[0]
                best_combined = swap_score

            avg_ncc = (best_obv_side["ncc"] + best_rev_side["ncc"]) / 2.0
            avg_orb = (best_obv_side["orb_inliers"] + best_rev_side["orb_inliers"]) / 2.0
            avg_hist = (best_obv_side["hist"] + best_rev_side["hist"]) / 2.0

            coin_match_details[coin_id] = {
                "score": float(best_combined),
                "obv_score": float(best_obv_side["combined"]),
                "rev_score": float(best_rev_side["combined"]),
                "ncc": float(avg_ncc),
                "orb_inliers": float(avg_orb),
                "hist": float(avg_hist)
            }

        return coin_match_details

    def should_accept_candidate(
        self,
        top_cand: Candidate,
        top_details: Dict,
        second_cand: Optional[Candidate] = None,
        second_details: Optional[Dict] = None,
        bimetallic_detected: bool = False
    ) -> Tuple[bool, str, str]:
        """
        Open-Set Decision Policy (OOD Rejection Engine).
        Decides whether to ACCEPT, REJECT_UNKNOWN, REJECT_AMBIGUOUS, or REJECT_LOW_CONFIDENCE.
        """
        score = top_details.get("score", 0.0)
        top_obv = top_details.get("obv_score", score)
        top_rev = top_details.get("rev_score", score)
        ncc = top_details.get("ncc", 0.0)
        orb_inliers = top_details.get("orb_inliers", 0.0)
        hist = top_details.get("hist", 0.0)

        top_coin = catalog_service.get_coin(top_cand.id)
        is_coin_bimetallic = bool(top_coin and top_coin.specifications and top_coin.specifications.material and "bimetálic" in top_coin.specifications.material.lower())

        # 1. Check absolute score threshold
        if score < 0.70:
            return False, "low_confidence", f"Pontuação visual {score*100:.1f}% abaixo do limiar mínimo de 70%."

        # 2. Check ORB feature match count (Unindexed/unknown coins or medals have low keypoint matches)
        min_orb_required = 3.5 if score >= 0.78 else 5.5
        if orb_inliers < min_orb_required:
            return False, "unknown_coin", f"Poucos pontos de correspondência ORB válidos ({orb_inliers:.1f} inliers)."

        # 3. Check bimetallic material consistency
        if is_coin_bimetallic and not bimetallic_detected and score < 0.90:
            return False, "unknown_coin", "Estrutura bimetálica esperada (núcleo dourado / anel prateado) não detectada."

        # 4. Side-specific margin check (Commemorative coins share reverse side with regular coins!)
        if second_cand and second_details:
            sec_obv = second_details.get("obv_score", second_details.get("score", 0.0))
            sec_rev = second_details.get("rev_score", second_details.get("score", 0.0))
            obv_margin = top_obv - sec_obv
            rev_margin = top_rev - sec_rev
            max_side_margin = max(obv_margin, rev_margin)
            global_margin = score - second_details.get("score", 0.0)

            # If Top1 is commemorative or regular coin of same denomination with close scores:
            if top_cand.denomination == second_cand.denomination and score >= 0.85:
                ambiguity_threshold = -0.05  # High confidence match of same denomination
            else:
                ambiguity_threshold = 0.02

            if global_margin < ambiguity_threshold and max_side_margin < ambiguity_threshold:
                return False, "ambiguous_match", f"Ambiguidades entre emissões próximas (margem lateral: {max_side_margin*100:.1f}%)."

        # 5. Check structural NCC and color histogram
        if ncc < 0.45 or hist < 0.25:
            return False, "unknown_coin", f"Características estruturais atípicas (NCC: {ncc:.2f})."

        return True, "accepted", "Identificação aceita com alta confiança."

    def identify(self, front_bytes: bytes, back_bytes: bytes) -> IdentifyResponse:
        """Main recognition pipeline endpoint logic with Open-Set Recognition."""
        # 1. Decode & normalize images
        f_bgr, f_pil = self.crop_and_normalize(self.decode_image(front_bytes))
        b_bgr, b_pil = self.crop_and_normalize(self.decode_image(back_bytes))

        # 2. Check bimetallic physical property
        f_bim, f_bim_score = self.detect_bimetallic(f_bgr)
        b_bim, b_bim_score = self.detect_bimetallic(b_bgr)
        bimetallic_detected = f_bim or b_bim

        # 3. Visual feature match & metrics
        match_details_dict = self.match_pair(f_pil, b_pil)

        # Prefer specific commemorative coin over regular coin if obverse match is strong
        sorted_matches = sorted(match_details_dict.items(), key=lambda x: x[1]["score"], reverse=True)

        # Check if top candidate is regular coin but a commemorative candidate of same denomination has high obverse score
        if len(sorted_matches) > 1:
            top_id, top_d = sorted_matches[0]
            sec_id, sec_d = sorted_matches[1]
            top_c = catalog_service.get_coin(top_id)
            sec_c = catalog_service.get_coin(sec_id)

            if top_c and sec_c and not top_c.commemorative and sec_c.commemorative and top_c.denomination == sec_c.denomination:
                if sec_d["obv_score"] >= 0.75 and (top_d["score"] - sec_d["score"]) < 0.05:
                    # Swap top candidate to the specific commemorative emission!
                    sorted_matches[0], sorted_matches[1] = sorted_matches[1], sorted_matches[0]

        candidates: List[Candidate] = []
        for coin_id, detail in sorted_matches[:5]:
            coin = catalog_service.get_coin(coin_id)
            if coin:
                candidates.append(Candidate(
                    id=coin.id,
                    design=coin.design_name,
                    confidence=round(detail["score"], 4),
                    denomination=coin.denomination,
                    year=coin.year,
                    commemorative=coin.commemorative
                ))

        if not candidates:
            return IdentifyResponse(
                identified=False,
                reason="unknown_coin",
                denomination="0.00",
                year="",
                family="desconhecida",
                design="Moeda não identificada",
                commemorative=False,
                confidence=0.0,
                candidates=[],
                warnings=["Nenhuma emissão conhecida atinge os critérios visuais do catálogo."],
                bimetallic_detected=bimetallic_detected
            )

        top_cand = candidates[0]
        top_details = match_details_dict[top_cand.id]

        second_cand = candidates[1] if len(candidates) > 1 else None
        second_details = match_details_dict[second_cand.id] if second_cand else None

        # 4. Open-Set Decision Policy
        accepted, reason, decision_msg = self.should_accept_candidate(
            top_cand, top_details, second_cand, second_details, bimetallic_detected
        )

        top_coin = catalog_service.get_coin(top_cand.id)
        confidence = top_cand.confidence

        warnings = []
        if not accepted:
            warnings.append(f"Rejeição Open-Set ({reason}): {decision_msg}")
            return IdentifyResponse(
                identified=False,
                reason=reason,
                denomination=top_cand.denomination,
                year=top_cand.year,
                family=top_coin.family if top_coin else "segunda_familia",
                design="Moeda não identificada com segurança",
                commemorative=False,
                confidence=round(confidence, 4),
                best_candidate=top_cand,
                candidates=candidates,
                warnings=warnings,
                bimetallic_detected=bimetallic_detected
            )

        return IdentifyResponse(
            identified=True,
            reason="accepted",
            denomination=top_coin.denomination if top_coin else top_cand.denomination,
            year=top_coin.year if top_coin else top_cand.year,
            family=top_coin.family if top_coin else "segunda_familia",
            design=top_coin.design_name if top_coin else top_cand.design,
            commemorative=top_coin.commemorative if top_coin else top_cand.commemorative,
            confidence=round(confidence, 4),
            coin_details=top_coin,
            best_candidate=top_cand,
            candidates=candidates,
            warnings=warnings,
            bimetallic_detected=bimetallic_detected
        )


vision_engine = VisionEngine()
