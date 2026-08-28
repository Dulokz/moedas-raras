// Auto-Capture V3: Real-time geometry (circularity, centering, size), stability & sharpness detection.

let autoStableFrames = 0;
let autoCooldown = false;
let autoCountdownTimer = null;
let lastCoinPos = null;

const MIN_CIRCULARITY = 0.65;
const AUTO_FOCUS_SCORE = 750;
const AUTO_STABLE_FRAMES = 3;

function resetAutoCapture() {
  autoStableFrames = 0;
  lastCoinPos = null;
  autoCooldown = false;
  clearInterval(autoCountdownTimer);
  autoCountdownTimer = null;
  const c = document.querySelector('#countdown');
  if (c) c.textContent = '';
  document.querySelector('.camera')?.classList.remove('ready', 'captured');
}

function finishCapturedSide() {
  if (step++ === 0) {
    document.querySelector('#side').textContent = 'VERSO';
    document.querySelector('#captureProgress').textContent = '2/2';
    document.querySelector('#focusHint').textContent = 'Vire a moeda e centralize na moldura';
    document.querySelector('#capture').textContent = '📸 CAPTURAR VERSO AGORA';
    setTimeout(() => {
      autoCooldown = false;
      autoStableFrames = 0;
      lastCoinPos = null;
      document.querySelector('.camera')?.classList.remove('ready', 'captured');
    }, 900);
  } else {
    stop();
    autoIdentify();
  }
}

function captureNow() {
  if (autoCooldown || !stream) return;
  autoCooldown = true;
  photos.push(cropCoinData());
  document.querySelector('.camera')?.classList.add('captured');
  finishCapturedSide();
}

function analyzeCameraFrame() {
  const v = document.querySelector('#video');
  if (!v || !v.videoWidth || !v.videoHeight) return { hasCoin: false, reason: 'NO_VIDEO' };

  const w = v.videoWidth;
  const h = v.videoHeight;

  const canvas = document.createElement('canvas');
  const size = 260;
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(v, 0, 0, w, h, 0, 0, size, size);

  const imgData = ctx.getImageData(0, 0, size, size);
  const data = imgData.data;

  // 1. Grayscale & Intensity Variance Analysis
  let sum = 0, sumSq = 0, n = size * size;
  const gray = new Uint8Array(n);

  for (let i = 0; i < n; i++) {
    const idx = i * 4;
    const g = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2];
    gray[i] = g;
    sum += g;
    sumSq += g * g;
  }

  const mean = sum / n;
  const variance = (sumSq / n) - (mean * mean);

  // Reject uniform/flat frames (no object / empty surface)
  if (variance < 150) {
    return { hasCoin: false, reason: 'POSICIONE A MOEDA' };
  }

  // 2. Simple Circularity & Bounding Box Estimation via Gradient Edges
  let edgePixels = 0;
  let cx = 0, cy = 0;
  let minX = size, maxX = 0, minY = size, maxY = 0;

  for (let y = 1; y < size - 1; y += 2) {
    for (let x = 1; x < size - 1; x += 2) {
      const idx = y * size + x;
      const gx = Math.abs(gray[idx + 1] - gray[idx - 1]);
      const gy = Math.abs(gray[idx + size] - gray[idx - size]);
      const grad = gx + gy;

      if (grad > 35) {
        edgePixels++;
        cx += x;
        cy += y;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }

  if (edgePixels < 120) {
    return { hasCoin: false, reason: 'POSICIONE A MOEDA' };
  }

  cx = cx / edgePixels;
  cy = cy / edgePixels;

  const bw = maxX - minX;
  const bh = maxY - minY;
  const radius = (bw + bh) / 4;
  const aspectRatio = bw / (bh || 1);

  // Check circular geometry ratio (bw vs bh should be close to 1:1)
  if (aspectRatio < 0.65 || aspectRatio > 1.45) {
    return { hasCoin: false, reason: 'POSICIONE A MOEDA' };
  }

  // Check centering distance from frame center (130, 130)
  const distFromCenter = Math.hypot(cx - 130, cy - 130);

  if (radius < 35) {
    return { hasCoin: true, reason: 'APROXIME A MOEDA', pos: { x: cx, y: cy, r: radius } };
  }
  if (radius > 115) {
    return { hasCoin: true, reason: 'AFASTE A MOEDA', pos: { x: cx, y: cy, r: radius } };
  }
  if (distFromCenter > 45) {
    return { hasCoin: true, reason: 'CENTRALIZE A MOEDA', pos: { x: cx, y: cy, r: radius } };
  }

  // 3. Laplacian Sharpness Variance Calculation
  let lapSum = 0, lapSumSq = 0, lapN = 0;
  for (let y = 10; y < size - 10; y += 3) {
    for (let x = 10; x < size - 10; x += 3) {
      const i = y * size + x;
      const lap = 4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - size] - gray[i + size];
      lapSum += lap;
      lapSumSq += lap * lap;
      lapN++;
    }
  }
  const lapMean = lapSum / (lapN || 1);
  const sharpnessScore = (lapSumSq / (lapN || 1)) - (lapMean * lapMean);

  return {
    hasCoin: true,
    reason: 'VALID',
    pos: { x: cx, y: cy, r: radius },
    sharpness: sharpnessScore
  };
}

async function automaticSnap() {
  if (autoCooldown || !stream) return;
  autoCooldown = true;
  document.querySelector('.camera')?.classList.add('ready');
  let n = 2;
  const cd = document.querySelector('#countdown');
  if (cd) cd.textContent = n;

  autoCountdownTimer = setInterval(() => {
    n--;
    if (n > 0) {
      if (cd) cd.textContent = n;
      return;
    }
    clearInterval(autoCountdownTimer);
    autoCountdownTimer = null;
    if (cd) cd.textContent = '';

    const frameResult = analyzeCameraFrame();
    if (!frameResult.hasCoin || frameResult.reason !== 'VALID') {
      autoCooldown = false;
      autoStableFrames = 0;
      document.querySelector('.camera')?.classList.remove('ready');
      return;
    }

    photos.push(cropCoinData());
    document.querySelector('.camera')?.classList.add('captured');
    finishCapturedSide();
  }, 400);
}

startFocusMeter = function () {
  if (focusTimer) clearInterval(focusTimer);
  resetAutoCapture();

  focusTimer = setInterval(() => {
    const el = document.querySelector('#focusState');
    const hint = document.querySelector('#focusHint');
    if (!el) return;

    const res = analyzeCameraFrame();

    if (!res.hasCoin || res.reason !== 'VALID') {
      autoStableFrames = 0;
      lastCoinPos = null;
      el.className = 'focusState bad';

      if (res.reason === 'APROXIME A MOEDA') {
        el.textContent = '🟡 APROXIME A MOEDA';
        hint.textContent = 'Traga a moeda mais perto da câmera';
      } else if (res.reason === 'AFASTE A MOEDA') {
        el.textContent = '🟡 AFASTE A MOEDA';
        hint.textContent = 'Afaste um pouco a moeda da lente';
      } else if (res.reason === 'CENTRALIZE A MOEDA') {
        el.textContent = '🟡 CENTRALIZE A MOEDA';
        hint.textContent = 'Mantenha a moeda dentro da retícula central';
      } else {
        el.textContent = '⚪ POSICIONE A MOEDA';
        hint.textContent = 'Enquadre a moeda dentro da marcação';
      }
      return;
    }

    // Coin detected and correctly centered & sized -> Check Stability
    const curPos = res.pos;
    if (lastCoinPos) {
      const dx = Math.abs(curPos.x - lastCoinPos.x);
      const dy = Math.abs(curPos.y - lastCoinPos.y);
      const dr = Math.abs(curPos.r - lastCoinPos.r);

      if (dx <= 12 && dy <= 12 && dr <= 10) {
        autoStableFrames++;
      } else {
        autoStableFrames = 0;
      }
    } else {
      autoStableFrames = 1;
    }
    lastCoinPos = curPos;

    if (autoStableFrames < AUTO_STABLE_FRAMES) {
      el.className = 'focusState waiting';
      el.textContent = '🟡 SEGURE FIRME';
      hint.textContent = 'Mantenha a mão firme por um instante';
      return;
    }

    // Stable -> Check Sharpness
    if (res.sharpness >= AUTO_FOCUS_SCORE) {
      el.className = 'focusState good';
      el.textContent = `🟢 NÍTIDO • CAPTURANDO`;
      hint.textContent = autoCooldown ? 'Capturando…' : 'Perfeito! Mantendo foco...';
      if (!autoCooldown) automaticSnap();
    } else {
      el.className = 'focusState waiting';
      el.textContent = `🟡 AJUSTANDO FOCO`;
      hint.textContent = 'Foco em ajuste — ou capture manualmente';
    }
  }, 250);
};

const originalStart = start;
start = async function () {
  resetAutoCapture();
  document.querySelector('#captureProgress').textContent = '1/2';
  document.querySelector('#captureMode').textContent = 'AUTO + MANUAL';
  await originalStart();
  document.querySelector('#capture').textContent = '📸 CAPTURAR FRENTE AGORA';
};

document.querySelector('#capture').onclick = captureNow;
