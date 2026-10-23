"""Part A: 탐색 대시보드 World Health & Wealth Explorer → docs/explore.html"""
import json
from pathlib import Path

import altair as alt
import pandas as pd

from page import REGION_DOMAIN, REGION_RANGE, render

ROOT = Path(__file__).resolve().parents[1]
alt.data_transformers.disable_max_rows()

d = pd.read_csv(ROOT / "data" / "processed" / "gapminder_clean.csv")
d = d[["name", "region", "year", "gdp_pc", "pop", "child_mort", "life_exp", "fertility"]].round(
    {"gdp_pc": 0, "child_mort": 1, "life_exp": 1, "fertility": 2})

# 지표 키 → (지표명, 단위, 고정 축 범위)
IND = {
    "child_mort": ("5세 미만 아동사망률", "출생아 1,000명당 5세 이전 사망자 수", [0, 450]),
    "life_exp": ("기대수명", "출생 시 기대수명 (년)", [20, 90]),
    "fertility": ("합계출산율", "여성 1인당 평생 출생아 수 (명)", [0, 9]),
}
REGION_KO = {"Africa": "아프리카", "Americas": "아메리카", "Asia": "아시아", "Europe": "유럽"}
DEFAULT_PICK = ["South Korea", "Nigeria", "Bangladesh"]
FIRST_YEAR, LAST_YEAR = int(d.year.min()), int(d.year.max())
N_COUNTRIES = d.name.nunique()
ONE = alt.Data(values=[{}])  # 데이터와 무관한 주석·눈금선용 한 행짜리 데이터


def js_map(i):
    """지표 키 → IND 튜플의 i번째 값을 돌려주는 Vega 표현식용 객체 리터럴."""
    return "{" + ",".join(f"'{k}':{json.dumps(v[i], ensure_ascii=False)}" for k, v in IND.items()) + "}"


IND_NAME = f"{js_map(0)}[ind]"
IND_UNIT = f"{js_map(1)}[ind]"
ind_domain = alt.expr(f"{js_map(2)}[ind]")

# ---- 파라미터 -------------------------------------------------------------
ind = alt.param(name="ind", value="child_mort", bind=alt.binding_select(
    options=list(IND), labels=[v[0] for v in IND.values()], name="지표"))
yr = alt.param(name="yr", value=LAST_YEAR, bind=alt.binding_range(
    min=FIRST_YEAR, max=LAST_YEAR, step=1, name="연도"))
pick = alt.selection_point(name="pick", fields=["name"], on="click", clear="dblclick",
                           value=[{"name": n} for n in DEFAULT_PICK])
reg = alt.selection_point(name="reg", fields=["region"], bind="legend")

HL = {"param": "pick", "empty": False}  # 선택한 국가 → 강조


def hl(on, off):
    """선택 국가 여부에 따른 조건부 값."""
    return {"condition": {"test": HL, "value": on}, "value": off}


def title(text_expr, subtitle):
    return alt.TitleParams(text=alt.expr(text_expr), subtitle=subtitle, anchor="start", fontSize=15,
                           subtitleColor="#5b616b", subtitleFontSize=12, offset=22)


color = alt.Color("region:N", title="대륙 (클릭: 필터 · Shift+클릭: 복수 선택)",
                  scale=alt.Scale(domain=REGION_DOMAIN, range=REGION_RANGE),
                  legend=alt.Legend(orient="top", direction="horizontal", titleLimit=360,
                                    labelExpr=f"{json.dumps(REGION_KO, ensure_ascii=False)}[datum.label]"))
color_nolegend = alt.Color("region:N", scale=alt.Scale(domain=REGION_DOMAIN, range=REGION_RANGE), legend=None)

tooltip = [
    alt.Tooltip("name:N", title="국가"), alt.Tooltip("region:N", title="대륙"),
    alt.Tooltip("year:O", title="연도"),
    alt.Tooltip("gdp_pc:Q", title="1인당 GDP (2017 PPP $)", format=",.0f"),
    alt.Tooltip("child_mort:Q", title="5세 미만 아동사망률 (1,000명당)"),
    alt.Tooltip("life_exp:Q", title="기대수명 (년)"),
    alt.Tooltip("fertility:Q", title="합계출산율 (명)"), alt.Tooltip("pop:Q", title="인구 (명)", format=",.0f"),
]

# 축 제목은 표현식을 받지 않으므로, 선택 지표의 단위를 텍스트 마크로 플롯 왼쪽 위에 표시한다
unit_label = alt.Chart(ONE).mark_text(align="left", baseline="bottom", x=0, y=-6, fontSize=11.5,
                                      color="#444", text=alt.expr(f"'단위: ' + {IND_UNIT}"))

LABEL_GAP_PX = 16  # 국가명 레이블 사이 최소 세로 간격(px)


def dodge(chart, height):
    """선택 국가 레이블이 겹치지 않도록 세로 위치(label_y)를 계산하는 변환을 붙인다.

    값 오름차순 i번째 레이블을 y_i = max(v_i, y_(i-1) + gap)로 밀어 올린다. 점화식을 풀면
    y_i = i·gap + max_(j≤i)(v_j − j·gap) 이므로 누적 최댓값(window max)으로 계산할 수 있다.
    모든 레이블이 세로로 gap 이상 떨어지므로 가로 위치와 관계없이 겹치지 않는다.
    둘째 단계에서 맨 위 레이블이 축 상단(top)을 넘지 않도록 위에서부터 다시 내려 쌓는다:
    y'_i = min(y_i, y'_(i+1) − gap), y'_n = min(y_n, top) → y'_i = i·gap + min(min_(k≥i)(y_k − k·gap), top − n·gap).
    """
    order = [alt.SortField("v", order="ascending")]
    return chart.transform_window(rk="row_number()", sort=order).transform_calculate(
        gap=f"({js_map(2)}[ind][1] - {js_map(2)}[ind][0]) * {LABEL_GAP_PX} / {height}",
        top=f"{js_map(2)}[ind][1]").transform_calculate(
        w="datum.v - datum.rk * datum.gap").transform_window(
        wmax="max(w)", frame=[None, 0], sort=order).transform_calculate(
        y_up="datum.rk * datum.gap + datum.wmax").transform_calculate(
        z="datum.y_up - datum.rk * datum.gap").transform_window(
        zmin="min(z)", frame=[0, None], sort=order).transform_window(
        n="count()", frame=[None, None]).transform_calculate(
        label_y="datum.rk * datum.gap + min(datum.zmin, datum.top - datum.n * datum.gap)")


base = alt.Chart(d).transform_calculate(v="datum[ind]").transform_filter("isValid(datum.v)")
y_val = alt.Y("v:Q", axis=alt.Axis(title=None), scale=alt.Scale(domain=ind_domain))

# ---- ① 산점도: 1인당 GDP와 지표 (선택 연도) ---------------------------------
a1_base = base.transform_filter("datum.year == yr")
year_bg = alt.Chart(ONE).mark_text(fontSize=64, fontWeight="bold", color="#ececec", align="right",
                                   baseline="top", dx=-6, dy=4, x="width", y=0, text=alt.expr("yr"))
pts = a1_base.mark_circle(size=55, stroke="#222").encode(
    x=alt.X("gdp_pc:Q", title="1인당 GDP (2017년 PPP 기준 국제달러, 로그 눈금)",
            scale=alt.Scale(type="log", domain=[300, 150000], nice=False), axis=alt.Axis(format="$,.0f", tickCount=6)),
    y=y_val,
    color=color,
    opacity=alt.condition(reg, alt.value(0.85), alt.value(0.08)),
    strokeWidth=hl(1.6, 0),
    size=hl(140, 55),
    order=hl(1, 0),
    tooltip=tooltip,
).add_params(pick, reg)
A1_HEIGHT = 360
a1_lab = dodge(a1_base.transform_filter(HL), A1_HEIGHT)
leaders = a1_lab.transform_filter(f"abs(datum.label_y - datum.v) > datum.gap * 0.3").mark_rule(
    color="#777", strokeWidth=0.8).encode(x="gdp_pc:Q", y="v:Q", y2="label_y:Q")
LABEL_STYLE = dict(align="left", baseline="middle", dx=9, fontSize=12, fontWeight="bold")
halo = a1_lab.mark_text(stroke="white", strokeWidth=3.5, strokeJoin="round", **LABEL_STYLE).encode(
    x="gdp_pc:Q", y="label_y:Q", text="name:N")
labels = a1_lab.mark_text(color="#1f2328", **LABEL_STYLE).encode(x="gdp_pc:Q", y="label_y:Q", text="name:N")
a1 = alt.layer(year_bg, pts, leaders, halo, labels, unit_label).properties(
    width=640, height=A1_HEIGHT,
    title=title(f"'① 1인당 GDP와 ' + {IND_NAME} + ', ' + yr + '년'",
                "점 1개 = 1개국 · 가로: 1인당 GDP (로그 눈금) · 세로: 선택 지표 · 색: 대륙"))

# ---- ③ 시계열: 선택 국가 + 대륙 중앙값 --------------------------------------
a2_base = base.transform_filter(reg)
x_year = alt.X("year:Q", title="연도", axis=alt.Axis(format="d", tickCount=7),
               scale=alt.Scale(domain=[FIRST_YEAR, LAST_YEAR]))
medians = a2_base.transform_aggregate(v="median(v)", groupby=["region", "year"]).mark_line(
    strokeDash=[4, 3], strokeWidth=1.4, opacity=0.7).encode(
    x=x_year, y=y_val, color=color_nolegend,
    tooltip=[alt.Tooltip("region:N", title="대륙 중앙값"), alt.Tooltip("year:O", title="연도"),
             alt.Tooltip("v:Q", title="값", format=".1f")])
sel_lines = a2_base.transform_filter(HL).mark_line(strokeWidth=2.6).encode(
    x=x_year, y="v:Q", color=color_nolegend, detail="name:N", tooltip=tooltip)
A2_HEIGHT = 250
sel_end = dodge(a2_base.transform_filter(HL).transform_filter(f"datum.year == {LAST_YEAR}"), A2_HEIGHT).mark_text(
    align="left", dx=5, fontSize=11, fontWeight="bold").encode(
    x=x_year, y="label_y:Q", text="name:N", color=color_nolegend)
year_rule = alt.Chart(ONE).mark_rule(color="#888", strokeDash=[2, 2]).encode(x=alt.datum(alt.expr("yr"), type="quantitative"))
# 선 종류 범례: 플롯 위(단위 표기 오른쪽)에 그려 데이터 선과 겹치지 않게 한다. 좌표는 px.
LEG_Y, LEG_COLOR = -10, "#555"
line_key = alt.layer(
    alt.Chart(ONE).mark_rule(strokeWidth=2.6, color=LEG_COLOR).encode(
        x=alt.value(360), x2=alt.value(384), y=alt.value(LEG_Y)),
    alt.Chart(ONE).mark_text(x=389, y=LEG_Y, text="선택 국가", align="left", baseline="middle", fontSize=11.5, color="#333"),
    alt.Chart(ONE).mark_rule(strokeWidth=1.4, strokeDash=[4, 3], color=LEG_COLOR).encode(
        x=alt.value(455), x2=alt.value(479), y=alt.value(LEG_Y)),
    alt.Chart(ONE).mark_text(x=484, y=LEG_Y, text="대륙별 국가 중앙값", align="left", baseline="middle", fontSize=11.5, color="#333"),
    alt.Chart(ONE).mark_rule(strokeDash=[2, 2], color="#888").encode(
        x=alt.value(588), y=alt.value(LEG_Y - 6), y2=alt.value(LEG_Y + 6)),
    alt.Chart(ONE).mark_text(x=593, y=LEG_Y, text="현재 연도", align="left", baseline="middle", fontSize=11.5, color="#333"),
)
a2 = alt.layer(medians, sel_lines, sel_end, year_rule, unit_label, line_key).properties(
    width=640, height=A2_HEIGHT,
    title=title(f"'③ 선택 국가의 ' + {IND_NAME} + ' 추이, {FIRST_YEAR}–{LAST_YEAR}년'",
                "선택 국가와 같은 대륙 국가들의 중앙값을 함께 비교"))

# ---- ② 순위 dot plot: 선택 연도 상위·하위 10개국 -----------------------------
a3 = base.transform_filter("datum.year == yr").transform_filter(reg).transform_window(
    r_hi="row_number()", sort=[alt.SortField("v", order="descending")]).transform_window(
    r_lo="row_number()", sort=[alt.SortField("v", order="ascending")]).transform_filter(
    "datum.r_hi <= 10 || datum.r_lo <= 10")
rank_y = alt.Y("name:N", sort=alt.EncodingSortField("v", order="descending"), title=None,
               axis=alt.Axis(labelLimit=120, labelFontSize=11))
a3_rules = a3.transform_calculate(zero="0").mark_rule(color="#d6d3cc").encode(y=rank_y, x="zero:Q", x2="v:Q")
a3_dots = a3.mark_circle(size=70, stroke="#222").encode(
    y=rank_y, x=alt.X("v:Q", scale=alt.Scale(zero=True, nice=True), axis=alt.Axis(title=None)),
    color=color_nolegend, strokeWidth=hl(1.6, 0), tooltip=tooltip,
).add_params(pick)
a3c = alt.layer(a3_rules, a3_dots, unit_label).properties(
    width=440, height=alt.Step(16),
    title=title(f"'② ' + {IND_NAME} + ' 상위·하위 10개국, ' + yr + '년'",
                "값이 높은 순 정렬 · 위 10개: 최고 · 아래 10개: 최저"))

# ---- ④ 대륙별 분포 strip plot -------------------------------------------
a4_base = base.transform_filter("datum.year == yr").transform_filter(reg)
region_axis = alt.Axis(labelExpr=f"{json.dumps(REGION_KO, ensure_ascii=False)}[datum.label]")
a4_pts = a4_base.transform_calculate(jit="(random() - 0.5) * 18").mark_circle(size=22).encode(
    y=alt.Y("region:N", title=None, sort=REGION_DOMAIN, axis=region_axis), yOffset="jit:Q",
    x=alt.X("v:Q", scale=alt.Scale(domain=ind_domain), axis=alt.Axis(title=None)),
    color=color_nolegend,
    opacity=hl(1, 0.45),
    size=hl(90, 22),
    stroke=hl("#222", None),
    tooltip=tooltip).add_params(pick)
a4_med = a4_base.mark_tick(color="#111", thickness=2.5, size=30).encode(
    y=alt.Y("region:N", sort=REGION_DOMAIN), x="median(v):Q",
    tooltip=[alt.Tooltip("region:N", title="대륙"), alt.Tooltip("median(v):Q", title="중앙값", format=".1f")])
a4 = alt.layer(a4_pts, a4_med, unit_label).properties(
    width=440, height=250,
    title=title(f"'④ 대륙별 ' + {IND_NAME} + ' 분포, ' + yr + '년'",
                "점: 국가 · 검은 세로 막대: 대륙 중앙값"))

dash = alt.vconcat(
    alt.hconcat(a1, a3c, spacing=28),
    alt.hconcat(a2, a4, spacing=28),
    spacing=26,
).add_params(ind, yr).resolve_scale(color="shared").configure_view(stroke=None).configure_axis(
    labelFontSize=11, titleFontSize=12, gridColor="#eeeeee", domainColor="#999").configure(
    font="-apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif")

body = f"""
<h1>World Health &amp; Wealth Explorer</h1>
<p class="lede">국가별 소득 수준(1인당 GDP)과 건강 지표(5세 미만 아동사망률 · 기대수명 · 합계출산율) · {FIRST_YEAR}–{LAST_YEAR}년 · {N_COUNTRIES}개국</p>
<div class="grid">
  <div class="card"><h3>대상과 목적</h3>
    국제개발·보건을 공부하는 학생과 일반 독자가 소득과 건강의 관계를 국가·대륙·연도별로 직접 비교하도록 만든 대시보드입니다.</div>
  <div class="card"><h3>사용법</h3><ol>
    <li><b>지표</b>와 <b>연도</b>를 고르면 네 그래프의 값과 제목이 함께 바뀝니다.</li>
    <li><b>국가 선택</b> 목록에서 체크하거나 그래프의 점을 클릭하면 해당 국가가 모든 그래프에서 강조되고 ③에 추이가 그려집니다.</li>
    <li>① 위 범례에서 <b>대륙</b>을 클릭하면 ②③④가 그 대륙만 보여줍니다. <b>초기화</b>를 누르면 처음 상태로 돌아갑니다.</li></ol></div>
</div>
<div class="card" style="margin-bottom:12px"><h3>탐색 질문 예시</h3><ul>
  <li>1인당 GDP가 비슷한 국가 사이에서도 아동사망률은 얼마나 차이 나는가? (①: 같은 가로 위치에서의 세로 퍼짐)</li>
  <li>한국·방글라데시·나이지리아의 아동사망률은 언제부터 서로 다른 추이를 보였는가? (③)</li>
  <li>2022년 기대수명 하위 10개국은 어느 대륙에 몰려 있으며, 1980년과 비교하면 어떤가? (② + 연도)</li>
  <li>아프리카 국가 간 편차는 유럽보다 얼마나 크고, 시간이 지나며 줄었는가? (④ + 연도)</li></ul></div>
<div class="controls" id="controls">
  <div class="ms" id="ms">
    <span class="vega-bind-name">국가 선택</span>
    <button class="ms-btn" id="ms-btn" type="button" aria-haspopup="listbox" aria-expanded="false"><span id="ms-label">…</span> ▾</button>
    <div class="ms-panel" id="ms-panel" hidden>
      <div class="ms-top"><input type="search" id="ms-filter" placeholder="국가명으로 찾기 (예: Korea)" autocomplete="off">
        <button type="button" id="ms-clear" class="ms-link">모두 해제</button></div>
      <div class="ms-list" id="ms-list" role="listbox" aria-multiselectable="true"></div>
    </div>
  </div>
  <button id="reset" type="button" class="reset">초기화</button>
</div>
<div class="status" id="status"><span>현재 보기:</span><span id="st-text">…</span></div>
<p class="hint">그래프의 점 클릭: 국가 선택 · Shift+클릭: 추가 선택 · 더블클릭: 선택 해제</p>
<div class="chart" id="dash"></div>
"""

countries = (d.drop_duplicates("name")[["name", "region"]].sort_values(["region", "name"])
             .to_dict("records"))
script = f"""
const view = res_dash.view;
const LABEL = {js_map(0)};
const REGION_KO = {json.dumps(REGION_KO, ensure_ascii=False)};
const REGION_COLOR = {json.dumps(dict(zip(REGION_DOMAIN, REGION_RANGE)))};
const COUNTRIES = {json.dumps(countries, ensure_ascii=False)};

// Vega 컨트롤(지표·연도)을 페이지 상단 컨트롤 바로 옮긴다
const controls = document.getElementById('controls');
controls.insertBefore(document.querySelector('#dash .vega-bindings'), controls.firstChild);

// ---- 연도 재생: 슬라이더 옆 ▶ 버튼으로 {FIRST_YEAR}→{LAST_YEAR}년을 자동으로 넘긴다 ----
const range = document.querySelector('.vega-bindings input[type=range]');
const playBtn = document.createElement('button');
playBtn.type = 'button';
playBtn.className = 'play';
range.closest('.vega-bind').after(playBtn);
let timer = null;
function setYear(y) {{ range.value = y; range.dispatchEvent(new Event('input')); }}
function stopPlay() {{
  clearInterval(timer); timer = null;
  playBtn.textContent = '▶ 재생'; playBtn.setAttribute('aria-pressed', 'false');
}}
function startPlay() {{
  let y = +view.signal('yr');
  if (y >= {LAST_YEAR}) {{ y = {FIRST_YEAR}; setYear(y); }}  // 끝에 있으면 처음부터
  playBtn.textContent = '⏸ 정지'; playBtn.setAttribute('aria-pressed', 'true');
  timer = setInterval(() => {{ y += 1; setYear(y); if (y >= {LAST_YEAR}) stopPlay(); }}, 250);
}}
playBtn.addEventListener('click', () => timer ? stopPlay() : startPlay());
['pointerdown', 'keydown'].forEach(e => range.addEventListener(e, stopPlay));  // 직접 조작하면 재생 멈춤
stopPlay();

function storeVals(name, field) {{
  try {{ return (view.data(name + '_store') || []).map(t => t.values[t.fields.findIndex(f => f.field === field)]); }}
  catch (e) {{ return []; }}
}}

// ---- 국가 선택 드롭다운: pick 선택 저장소와 양방향 동기화 ----
const initialPick = view.data('pick_store').slice();
const tupleTmpl = initialPick[0];
const list = document.getElementById('ms-list');
let html = '';
for (const r of Object.keys(REGION_KO)) {{
  html += `<div class="ms-group" data-region="${{r}}">${{REGION_KO[r]}}</div>`;
  for (const c of COUNTRIES.filter(c => c.region === r)) {{
    html += `<label class="ms-item" data-name="${{c.name.toLowerCase()}}"><input type="checkbox" value="${{c.name}}">` +
            `<span class="dot" style="background:${{REGION_COLOR[r]}}"></span>${{c.name}}</label>`;
  }}
}}
list.innerHTML = html;
const boxes = [...list.querySelectorAll('input[type=checkbox]')];

async function setPicks(names) {{
  view.data('pick_store', names.map(n => ({{unit: tupleTmpl.unit, fields: tupleTmpl.fields, values: [n]}})));
  await view.runAsync();
}}
list.addEventListener('change', () => setPicks(boxes.filter(b => b.checked).map(b => b.value)));
document.getElementById('ms-clear').addEventListener('click', () => setPicks([]));

const filter = document.getElementById('ms-filter');
filter.addEventListener('input', () => {{
  const q = filter.value.trim().toLowerCase();
  list.querySelectorAll('.ms-item').forEach(el => el.hidden = q && !el.dataset.name.includes(q));
  list.querySelectorAll('.ms-group').forEach(g => {{
    let el = g.nextElementSibling, any = false;
    while (el && !el.classList.contains('ms-group')) {{ if (!el.hidden) any = true; el = el.nextElementSibling; }}
    g.hidden = !any;
  }});
}});

const btn = document.getElementById('ms-btn'), panel = document.getElementById('ms-panel');
function openPanel(open) {{
  panel.hidden = !open; btn.setAttribute('aria-expanded', open);
  if (open) filter.focus();
}}
btn.addEventListener('click', () => openPanel(panel.hidden));
document.addEventListener('click', e => {{ if (!document.getElementById('ms').contains(e.target)) openPanel(false); }});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') openPanel(false); }});

function update() {{
  const picks = storeVals('pick', 'name');
  const regs = storeVals('reg', 'region');
  boxes.forEach(b => b.checked = picks.includes(b.value));
  document.getElementById('ms-label').textContent = picks.length ? `${{picks.length}}개국 선택됨` : '선택 없음';
  document.getElementById('st-text').innerHTML =
    `<b>${{LABEL[view.signal('ind')]}}</b> · <b>${{view.signal('yr')}}년</b>` +
    ` · 대륙: <b>${{regs.length ? regs.map(r => REGION_KO[r]).join(', ') : '전체'}}</b>` +
    ` · 선택 국가: <b>${{picks.length ? picks.join(', ') : '없음'}}</b>`;
}}
['ind', 'yr'].forEach(s => view.addSignalListener(s, update));
['pick_store', 'reg_store'].forEach(n => view.addDataListener(n, update));

// ---- URL로 보기 상태 지정: ?ind=life_exp&yr=1980&pick=Brazil,India&reg=Africa ----
const P = new URLSearchParams(location.search);
if (P.has('ind') && P.get('ind') in LABEL) {{
  view.signal('ind', P.get('ind'));
  document.querySelector('.vega-bindings select').value = P.get('ind');
}}
const yrParam = parseInt(P.get('yr'), 10);
if (yrParam >= {FIRST_YEAR} && yrParam <= {LAST_YEAR}) {{
  setYear(yrParam);
}}
const known = new Set(COUNTRIES.map(c => c.name));
if (P.has('pick')) await setPicks(P.get('pick').split(',').map(s => s.trim()).filter(n => known.has(n)));
if (P.has('reg')) {{
  const regs = P.get('reg').split(',').filter(r => r in REGION_KO);
  view.data('reg_store', regs.map(r => ({{fields: [{{type: 'E', field: 'region'}}], values: [r]}})));
}}
await view.runAsync();
update();

document.getElementById('reset').addEventListener('click', async () => {{
  stopPlay();
  view.signal('ind', 'child_mort').signal('yr', {LAST_YEAR});
  view.data('reg_store', []).data('pick_store', initialPick);
  await view.runAsync();
  document.querySelectorAll('.vega-bindings select').forEach(s => s.value = 'child_mort');
  document.querySelectorAll('.vega-bindings input[type=range]').forEach(s => {{ s.value = {LAST_YEAR}; s.dispatchEvent(new Event('input')); }});
  filter.value = ''; filter.dispatchEvent(new Event('input'));
  update();
}});
"""

out = ROOT / "docs" / "explore.html"
out.write_text(render("Health & Wealth Explorer", body, {"dash": dash}, script, max_width=1360), encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB)")
