"""Altair 스펙을 설명 텍스트가 있는 독립 HTML 페이지로 감싼다."""
import json

VEGA = "https://cdn.jsdelivr.net/npm/vega@6.2.0"
VEGA_LITE = "https://cdn.jsdelivr.net/npm/vega-lite@6.4.1"
VEGA_EMBED = "https://cdn.jsdelivr.net/npm/vega-embed@7.0.2"

REGION_DOMAIN = ["Africa", "Americas", "Asia", "Europe"]
REGION_RANGE = ["#D55E00", "#009E73", "#CC79A7", "#0072B2"]  # Okabe-Ito: 색각이상 안전

SOURCES = (
    "출처: Gapminder Fast Track (open-numbers/ddf--gapminder--fasttrack; 아동사망률·기대수명·합계출산율·"
    "1인당 GDP[2017 PPP 불변 국제달러]·인구), World Bank WDI SH.IMM.IDPT (WHO/UNICEF DTP3 접종률)·SH.DYN.MORT "
    "(UN IGME 5세 미만 사망률, 교차 검증용). "
    "접근일 2026-10-23. 1960–2022년, 179개국(2022년 인구 15만 미만 국가 제외)."
)

CSS = """
:root{--bg:#fbfaf7;--fg:#1f2328;--muted:#5b616b;--line:#e3e1dc;--accent:#0072B2;--card:#ffffff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
main{max-width:1000px;margin:0 auto;padding:28px 16px 48px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:18px;margin:28px 0 6px}
.lede{color:var(--muted);margin:0 0 18px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.card h3{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 6px}
.card ul,.card ol{margin:0;padding-left:18px}
.status{display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:#eef4f9;border:1px solid #cfe0ee;border-radius:8px;padding:8px 12px;margin:8px 0 12px;font-size:14px}
.status b{font-weight:600}
button{font:inherit;font-size:13px;padding:4px 12px;border-radius:6px;border:1px solid #9bb7cc;background:#fff;cursor:pointer}
button:hover{background:#f2f7fb}
.controls{display:flex;flex-wrap:wrap;align-items:center;gap:10px 22px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0 8px;font-size:14px;position:sticky;top:0;z-index:10}
.controls .reset{margin-left:auto}
.hint{color:var(--muted);font-size:12.5px;margin:0 2px 8px}
.ms{position:relative;display:flex;align-items:center}
.ms-btn{min-width:150px;text-align:left;font-size:14px}
.ms-panel{position:absolute;top:calc(100% + 6px);left:0;width:300px;background:#fff;border:1px solid #c9c6bf;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.12);z-index:20}
.ms-top{display:flex;gap:6px;padding:8px;border-bottom:1px solid var(--line)}
.ms-top input{flex:1;font:inherit;font-size:13.5px;padding:4px 8px;border:1px solid #c9c6bf;border-radius:6px}
.ms-link{border:none;background:none;color:var(--accent);padding:4px 6px}
.ms-list{max-height:320px;overflow-y:auto;padding:4px 0}
.ms-group{font-size:12px;font-weight:600;color:var(--muted);padding:8px 12px 2px;text-transform:uppercase;letter-spacing:.03em}
.ms-item{display:flex;align-items:center;gap:8px;padding:3px 12px;font-size:13.5px;cursor:pointer}
.ms-item:hover{background:#f2f7fb}
.ms-item .dot{width:9px;height:9px;border-radius:50%;flex:none}
[hidden]{display:none!important}
.chart{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;overflow-x:auto}
.chart.vega-embed{display:block!important}
.vega-bindings{display:flex;flex-wrap:wrap;gap:6px 22px;font-size:14px}
.vega-bindings select,.vega-bindings input[type=search]{font:inherit;font-size:14px;padding:2px 6px}
.vega-bind-name{font-weight:600;margin-right:4px}
.caption{color:var(--muted);font-size:13px;margin:6px 2px 0}
.claim{font-size:20px;line-height:1.45;font-weight:600;margin:6px 0 10px}
.fig{margin:18px 0 6px}
.fig h3{font-size:16px;margin:0 0 2px}
.fig p{margin:0 0 8px;color:var(--muted);font-size:14px}
footer{color:var(--muted);font-size:12.5px;margin-top:28px;border-top:1px solid var(--line);padding-top:10px}
@media (max-width:720px){.grid{grid-template-columns:1fr}}
"""


def render(title, body_html, specs, script_after="", max_width=1000):
    """specs: {div_id: altair_chart} — 각 div에 차트를 임베드한다."""
    embeds = "\n".join(
        f"const spec_{k} = {c.to_json(indent=None)};\n"
        f"const res_{k} = await vegaEmbed('#{k}', spec_{k}, {{actions:false, renderer:'svg'}});"
        for k, c in specs.items()
    )
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<script src="{VEGA}"></script><script src="{VEGA_LITE}"></script><script src="{VEGA_EMBED}"></script>
<style>{CSS}main{{max-width:{max_width}px}}</style></head>
<body><main>
{body_html}
<footer>{SOURCES}</footer>
</main>
<script type="module">
{embeds}
{script_after}
</script>
</body></html>"""
