"""보고서용 스크린샷 생성 → report_assets/*.png

headless Chrome으로 docs/*.html을 file:// 로 열어 캡처한 뒤, 1440px 폭 레이아웃 기준 좌표로 잘라낸다.
(file:// 로 렌더링되므로 '서버 없이 HTML만 열어도 동작한다'는 점도 함께 확인된다.)
"""
import subprocess
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report_assets"
OUT.mkdir(exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH, SCALE = 1440, 2

# (파일명, 페이지, URL 쿼리, 캡처 높이, 자를 영역[x, y, w, h] — CSS px)
SHOTS = [
    ("a_overview", "explore.html", "", 1700, [46, 445, 1348, 1092]),
    ("a_lifeexp_1980", "explore.html", "?ind=life_exp&yr=1980&pick=South Korea,Nigeria,Bangladesh", 1700, [46, 586, 1348, 950]),
    ("a_asia_fertility", "explore.html", "?ind=fertility&yr=1990&pick=South Korea,China,India&reg=Asia", 1700, [46, 586, 1348, 950]),
    ("b_header", "explain.html", "", 2300, [226, 20, 988, 222]),
    ("b1", "explain.html", "", 2300, [226, 240, 988, 598]),
    ("b2", "explain.html", "", 2300, [226, 838, 988, 488]),
    ("b3", "explain.html", "", 2300, [226, 1330, 988, 380]),
]


def capture(page, query, height, path):
    url = (ROOT / "docs" / page).as_uri() + quote(query, safe="?=&,")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--force-device-scale-factor={SCALE}", f"--window-size={WIDTH},{height}",
                    "--virtual-time-budget=10000", f"--screenshot={path}", url],
                   check=True, capture_output=True)


cache = {}
for name, page, query, height, (x, y, w, h) in SHOTS:
    key = (page, query, height)
    if key not in cache:
        tmp = OUT / f"_full_{len(cache)}.png"
        capture(page, query, height, tmp)
        cache[key] = tmp
    img = Image.open(cache[key])
    img.crop((x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE)).save(OUT / f"{name}.png", optimize=True)
    print("saved", name)

for tmp in cache.values():
    tmp.unlink()
