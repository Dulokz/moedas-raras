import urllib.request
import json
from pathlib import Path

# 1. Test /api/health
print("Testando GET /api/health...")
req = urllib.request.urlopen("http://127.0.0.1:8000/api/health")
health_data = json.loads(req.read().decode())
print("  Status Health:", health_data)

# 2. Test POST /api/identify with 30 anos 2024 test photos
print("\nTestando POST /api/identify com par de fotos Base64...")
fixture_dir = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "brl_1_2024_30_anos"
front_p = fixture_dir / "01_standard_0deg_front.jpg"
back_p = fixture_dir / "01_standard_0deg_back.jpg"

import base64
with open(front_p, "rb") as f:
    f_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
with open(back_p, "rb") as b:
    b_b64 = "data:image/jpeg;base64," + base64.b64encode(b.read()).decode()

payload = json.dumps({"front": f_b64, "back": b_b64}).encode("utf-8")
post_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/identify",
    data=payload,
    headers={"Content-Type": "application/json"}
)

res = urllib.request.urlopen(post_req)
identify_result = json.loads(res.read().decode())
print("  Resultado API /api/identify:")
print(json.dumps(identify_result, indent=2, ensure_ascii=False))

# Assertions
assert identify_result["identified"] is True
assert identify_result["denomination"] in ["1.00", "1"]
assert identify_result["year"] == "2024"
assert "30 anos" in identify_result["design"].lower()
assert identify_result["commemorative"] is True
print("\n>>> API TEST PASSED! TUDO FUNCIONANDO COM SUCESSO DO FRONT AO BACKEND! <<<")
