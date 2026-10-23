"""Part B: 설명 시각화 → docs/explain.html

핵심 메시지: 소득이 같은 나라끼리 비교해도 아동사망률은 1970년보다 2020년에 훨씬 낮다.
"""
import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

from page import REGION_DOMAIN, REGION_RANGE, render

ROOT = Path(__file__).resolve().parents[1]
alt.data_transformers.disable_max_rows()

d = pd.read_csv(ROOT / "data" / "processed" / "gapminder_clean.csv")
rob = json.loads((ROOT / "data" / "processed" / "robustness.json").read_text(encoding="utf-8"))  # src/robustness.py 결과


def drop_range(block):
    pcts = [v[2] for v in block["at"].values()]
    return f"{min(pcts):.0f}–{max(pcts):.0f}%"
Y0, Y1 = 1970, 2020
REF_GDP = 4000            # 주석을 다는 기준 소득
FRAC = 0.6                # LOESS 평활 정도
OLD, NEW = "#9a9a9a", "#0072B2"
X_GDP = alt.X("gdp_pc:Q", title="1인당 GDP (2017 PPP 국제달러, 로그 눈금)",
              scale=alt.Scale(type="log", domain=[400, 120000], nice=False),
              axis=alt.Axis(format="$,.0f", values=[500, 1000, 2000, 4000, 8000, 16000, 32000, 64000]))
Y_CM = alt.Y("child_mort:Q", title="5세 미만 아동사망률 (출생 1,000명당)", scale=alt.Scale(domain=[0, 400]))


def loess_curve(year):
    s = d[d.year == year].dropna(subset=["gdp_pc", "child_mort"])
    fit = lowess(s.child_mort, np.log10(s.gdp_pc), frac=FRAC, return_sorted=True)
    c = pd.DataFrame({"gdp_pc": 10 ** fit[:, 0], "child_mort": fit[:, 1], "year": str(year)})
    lo, hi = s.gdp_pc.quantile([0.05, 0.95])
    return c, lo, hi


def trim(curve, lo, hi):
    """국가가 드문 양 끝(소득 하위·상위 5%)은 소수 국가(예: 1970년 산유국)에 끌려가므로 그리지 않는다."""
    return curve[(curve.gdp_pc >= lo) & (curve.gdp_pc <= hi)]


def at(curve, gdp):
    return float(np.interp(np.log10(gdp), np.log10(curve.gdp_pc), curve.child_mort))


# ---- B1: 두 시점 산점도 + LOESS ------------------------------------------
(c0, lo0, hi0), (c1, lo1, hi1) = loess_curve(Y0), loess_curve(Y1)
v0, v1 = at(c0, REF_GDP), at(c1, REF_GDP)
drop = (1 - v1 / v0) * 100
other = ", ".join(f"{k}: −{(1 - at(c1, g) / at(c0, g)) * 100:.0f}%" for k, g in (("$1천", 1000), ("$8천", 8000), ("$1만6천", 16000)))
print(f"[B1] at ${REF_GDP:,}: {Y0}={v0:.1f}, {Y1}={v1:.1f}, -{drop:.0f}%")

pts = d[d.year.isin([Y0, Y1])].dropna(subset=["gdp_pc", "child_mort"]).assign(year=lambda x: x.year.astype(str))
yscale = alt.Scale(domain=[str(Y0), str(Y1)], range=[OLD, NEW])
tt = [alt.Tooltip("name:N", title="국가"), alt.Tooltip("year:N", title="연도"),
      alt.Tooltip("gdp_pc:Q", title="1인당 GDP ($)", format=",.0f"),
      alt.Tooltip("child_mort:Q", title="아동사망률 (‰)", format=".0f")]
b1_pts = alt.Chart(pts).mark_circle(size=34, opacity=0.38).encode(
    x=X_GDP, y=Y_CM, color=alt.Color("year:N", scale=yscale, legend=None), tooltip=tt)
curves = pd.concat([trim(c0, lo0, hi0), trim(c1, lo1, hi1)])
b1_lines = alt.Chart(curves).mark_line(strokeWidth=3.5).encode(
    x="gdp_pc:Q", y="child_mort:Q", color=alt.Color("year:N", scale=yscale, legend=None))
# 곡선 직접 레이블 (범례 대신)
lab = pd.DataFrame([
    {"gdp_pc": 750, "child_mort": at(c0, 750) + 22, "t": f"{Y0}년 국가들", "year": str(Y0)},
    {"gdp_pc": 750, "child_mort": at(c1, 750) - 26, "t": f"{Y1}년 국가들", "year": str(Y1)},
])
b1_lab = alt.Chart(lab).mark_text(fontSize=14, fontWeight="bold", align="left").encode(
    x="gdp_pc:Q", y="child_mort:Q", text="t:N", color=alt.Color("year:N", scale=yscale, legend=None))
# 같은 소득에서의 차이: 세로 화살표와 수치
arrow = pd.DataFrame({"gdp_pc": [REF_GDP], "y0": [v0], "y1": [v1]})
b1_rule = alt.Chart(arrow).mark_rule(strokeWidth=2, color="#222").encode(x="gdp_pc:Q", y="y0:Q", y2="y1:Q")
b1_head = alt.Chart(arrow).mark_point(shape="triangle-down", size=110, filled=True, color="#222").encode(
    x="gdp_pc:Q", y=alt.Y("y1:Q"))
b1_dots = alt.Chart(pd.DataFrame({"gdp_pc": [REF_GDP] * 2, "v": [v0, v1]})).mark_circle(
    size=70, color="#222").encode(x="gdp_pc:Q", y="v:Q")
note = pd.DataFrame({"gdp_pc": [REF_GDP * 1.12], "v": [(v0 + v1) / 2],
                     "t": [f"1인당 GDP ${REF_GDP:,}에서: {v0:.0f}명 → {v1:.0f}명 (−{drop:.0f}%)"]})
b1_note = alt.Chart(note).mark_text(align="left", fontSize=13, fontWeight="bold", color="#222").encode(
    x="gdp_pc:Q", y="v:Q", text="t:N")
b1 = alt.layer(b1_pts, b1_lines, b1_lab, b1_rule, b1_dots, b1_head, b1_note).properties(width=820, height=400)

# ---- B2: 고정 소득 구간별 아동사망률 중앙값 추이 --------------------------
BANDS = [(0, 2000, "$2천 미만"), (2000, 4000, "$2천–4천"), (4000, 8000, "$4천–8천"),
         (8000, 16000, "$8천–1만6천"), (16000, 1e9, "$1만6천 이상")]
BAND_COLORS = ["#08306b", "#1d5fa3", "#3f8fcc", "#73b0dd", "#a4cbe8"]
MIN_N = 5
rows = []
for lo, hi, name in BANDS:
    s = d[(d.gdp_pc >= lo) & (d.gdp_pc < hi)].groupby("year").agg(
        child_mort=("child_mort", "median"), n=("country", "nunique")).reset_index()
    rows.append(s[s.n >= MIN_N].assign(band=name))
bands = pd.concat(rows)
band_names = [b[2] for b in BANDS]
bscale = alt.Scale(domain=band_names, range=BAND_COLORS)
X_YEAR = alt.X("year:Q", title=None, axis=alt.Axis(format="d", values=list(range(1960, 2021, 10))),
               scale=alt.Scale(domain=[1960, 2034]))
b2_lines = alt.Chart(bands).mark_line(strokeWidth=2.6).encode(
    x=X_YEAR, y=alt.Y("child_mort:Q", title="소득 구간별 아동사망률 중앙값 (출생 1,000명당)", scale=alt.Scale(domain=[0, 300])),
    color=alt.Color("band:N", scale=bscale, legend=None),
    tooltip=[alt.Tooltip("band:N", title="소득 구간"), alt.Tooltip("year:O", title="연도"),
             alt.Tooltip("child_mort:Q", title="중앙값", format=".0f"), alt.Tooltip("n:Q", title="국가 수")])
ends = bands.sort_values("year").groupby("band").tail(1).sort_values("child_mort").reset_index(drop=True)
# 끝 레이블이 겹치지 않도록 최소 간격(데이터 단위 ≈ 13px)을 두고 위로 밀어낸다
gap, prev = 300 / 320 * 13, -1e9
for i in ends.index:
    ends.loc[i, "label_y"] = prev = max(ends.loc[i, "child_mort"], prev + gap)
b2_lab = alt.Chart(ends).mark_text(align="left", dx=6, fontSize=12.5, fontWeight="bold", color="#333").encode(
    x="year:Q", y="label_y:Q", text="band:N")
for lo, hi, name in BANDS:
    b = bands[bands.band == name].set_index("year").child_mort
    if 1970 in b.index and 2020 in b.index:
        print(f"[B2] {name}: 1970={b[1970]:.0f} 2020={b[2020]:.0f} (-{(1 - b[2020] / b[1970]) * 100:.0f}%)")
b2 = alt.layer(b2_lines, b2_lab).properties(width=820, height=320)

# ---- B3 (맥락): 지역별 DTP3 접종률, 같은 국가 집합으로 비교 ----------------
D0, D1 = 1985, 2020
v = d.dropna(subset=["dtp3"])
both = set(v[v.year == D0].country) & set(v[v.year == D1].country)
p = v[v.country.isin(both) & v.year.isin([D0, D1])]
reg = (p.assign(w=p.dtp3 * p["pop"]).groupby(["region", "year"])
       .agg(w=("w", "sum"), pop=("pop", "sum"), n=("country", "nunique")).reset_index())
reg["dtp3"] = reg.w / reg["pop"]
reg["year"] = reg.year.astype(str)
print("[B3]", reg.pivot(index="region", columns="year", values="dtp3").round(0).to_dict())
dscale = alt.Scale(domain=[str(D0), str(D1)], range=[OLD, NEW])
REGION_KO = {"Africa": "아프리카", "Americas": "아메리카", "Asia": "아시아", "Europe": "유럽"}
Y_REG = alt.Y("region:N", sort=REGION_DOMAIN, title=None, axis=alt.Axis(
    labelFontSize=13, labelFontWeight="bold", labelExpr=f"{json.dumps(REGION_KO, ensure_ascii=False)}[datum.label]"))
X_DTP = alt.X("dtp3:Q", title="DTP3(디프테리아·파상풍·백일해 3차) 접종률, 인구가중 평균 (%)",
              scale=alt.Scale(domain=[0, 100]))
b3_bar = alt.Chart(reg).mark_line(color="#bbb", strokeWidth=3).encode(y=Y_REG, x=X_DTP, detail="region:N")
b3_pts = alt.Chart(reg).mark_circle(size=170, opacity=1).encode(
    y=Y_REG, x="dtp3:Q", color=alt.Color("year:N", scale=dscale, legend=None),
    tooltip=[alt.Tooltip("region:N", title="지역"), alt.Tooltip("year:N", title="연도"),
             alt.Tooltip("dtp3:Q", title="접종률 (%)", format=".0f"), alt.Tooltip("n:Q", title="국가 수")])
b3_txt = alt.Chart(reg).mark_text(dy=-14, fontSize=11.5, fontWeight="bold").encode(
    y=Y_REG, x="dtp3:Q", text=alt.Text("dtp3:Q", format=".0f"), color=alt.Color("year:N", scale=dscale, legend=None))
b3 = alt.layer(b3_bar, b3_pts, b3_txt).properties(width=820, height=200)


def style(c):
    return c.configure_view(stroke=None).configure_axis(
        labelFontSize=12, titleFontSize=12.5, gridColor="#eeeeee", domainColor="#999", titleColor="#333").configure(
        font="-apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif")


n_both = len(both)
body = f"""
<p class="lede" style="margin-bottom:4px">Part B · 설명 시각화 · 1960–2022, 179개국</p>
<h1 class="claim">같은 소득 수준끼리 비교해도, 2020년의 아이들은 1970년보다 5세 전에 사망할 확률이 약 3분의 1에 불과합니다.<br>
<span style="font-weight:400;color:#5b616b;font-size:16px">아동 생존의 개선은 “나라가 부유해졌기 때문”만으로는 설명되지 않습니다.</span></h1>
<div class="card"><h3>누구에게, 왜</h3>
경제성장만 이루면 보건은 자연히 따라온다고 생각하는 일반 독자와 정책 입문자를 위한 시각화입니다.
소득 증가 외의 요인(보건 기술·서비스 확산 등)이 아동 생존에 얼마나 큰 몫을 했는지 보여주며, 이는 저소득국이 부유해지기를 기다리지 않고도 개선할 여지가 크다는 뜻입니다.</div>

<section class="fig"><h3>① 소득이 같아도 곡선 전체가 아래로 내려갔다</h3>
<p>점 하나는 한 나라입니다. 회색은 {Y0}년, 파랑은 {Y1}년이고, 굵은 선은 각 연도의 추세(LOESS)입니다. 같은 가로 위치(같은 소득)에서 파란 선이 회색 선보다 훨씬 아래에 있습니다.</p>
<div class="chart" id="b1"></div>
<p class="caption">소득 축은 로그 눈금입니다. 다른 소득 수준에서도 감소폭은 비슷합니다({other}).</p></section>

<section class="fig"><h3>② 소득 구간을 고정해 시간을 따라가도, 모든 구간에서 꾸준히 떨어졌다</h3>
<p>1인당 GDP 구간(2017 PPP 불변 달러)마다, 해마다 그 구간에 속한 나라들의 아동사망률 중앙값입니다. 나라가 다른 구간으로 옮겨 가더라도 <b>구간 안에서</b> 값이 줄었다는 것은 소득 외의 개선이 있었다는 뜻입니다.</p>
<div class="chart" id="b2"></div>
<p class="caption">국가 수가 {MIN_N}개 미만인 구간·연도는 그리지 않았습니다.</p></section>

<section class="fig"><h3>③ 맥락: 같은 기간 기초 백신 접종이 크게 확대되었다</h3>
<p>{D0}년과 {D1}년에 모두 자료가 있는 같은 {n_both}개국만으로 비교한 지역별 DTP3 접종률(인구가중 평균)입니다. 회색 = {D0}년, 파랑 = {D1}년.</p>
<div class="chart" id="b3"></div>
<p class="caption">③은 ①·②의 하락과 <b>같은 시기에</b> 일어난 변화를 보여줄 뿐이며, 백신이 하락의 원인이라는 증거가 아닙니다. 위생, 모자보건, 교육, 영양 등 다른 요인도 함께 변했습니다.</p></section>

<div class="card" style="margin-top:20px"><h3>결론이 데이터 선택에 좌우되지 않는지 점검했습니다</h3><ul>
<li><b>다른 출처로 다시 계산:</b> 아동사망률을 UN IGME 추정치(World Bank SH.DYN.MORT)로 바꿔 두 해 모두 값이 있는 {rob['igme_1970_2020']['n'][0]}개국으로 다시 계산해도, 같은 소득에서 감소폭은 {drop_range(rob['igme_1970_2020'])}로 같습니다. IGME 추정치는 가구조사·인구동태 자료로 만들며 소득을 입력으로 쓰지 않으므로, “소득으로 추정한 값이라 생긴 결과”라는 반론을 배제할 수 있습니다(1970년 두 출처의 상관계수 r = {rob['agreement_1970']['pearson_r']}).</li>
<li><b>연도 선택:</b> {Y0}/{Y1} 대신 1980/2015, 1960/2022로 바꿔도 같은 소득에서의 감소폭은 {min(min(v[2] for v in b['at'].values()) for b in rob['year_pairs'].values()):.0f}–{max(max(v[2] for v in b['at'].values()) for b in rob['year_pairs'].values()):.0f}%입니다.</li>
<li><b>인구가중:</b> ②를 인구가중 중앙값으로 다시 계산해도 다섯 구간 모두 {min(v['drop_pct'] for v in rob['pop_weighted_bands'].values()):.0f}–{max(v['drop_pct'] for v in rob['pop_weighted_bands'].values()):.0f}% 낮아졌습니다.</li>
<li><b>최저 소득 구간의 구성:</b> 2020년 $2천 미만 구간에는 소말리아·중앙아프리카공화국·남수단·예멘 등 분쟁·취약국이 주로 남아 있습니다. 이들은 사망률이 높아 이 구간의 2020년 값을 끌어올리므로, 실제 개선 폭은 그래프보다 클 수 있습니다(보수적 추정).</li></ul></div>

<div class="card" style="margin-top:12px"><h3>해석할 때 주의할 점</h3><ul>
<li><b>상관이지 인과가 아닙니다.</b> 이 자료는 “소득만으로 설명되지 않는다”는 것을 보여줄 뿐, 무엇이 원인인지 증명하지 않습니다.</li>
<li><b>국가 단위 비교</b>입니다(생태학적 자료). 한 나라 안의 소득 계층별 차이는 다루지 않습니다. ①②는 나라마다 같은 가중치를 주고, ③은 인구가중 평균입니다.</li>
<li>출처가 바뀌는 해에 값이 불연속적으로 바뀌는 사례가 있습니다(예: 나이지리아 아동사망률 1980→1981년).</li>
<li>PPP 환산 소득은 국가 간 비교를 위한 근사치입니다.</li></ul></div>
<p class="caption" style="margin-top:10px">탐색용 대시보드: <a href="explore.html">World Health &amp; Wealth Explorer</a></p>
"""

out = ROOT / "docs" / "explain.html"
out.write_text(render("Same Income, Fewer Deaths", body, {"b1": style(b1), "b2": style(b2), "b3": style(b3)}),
               encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB)")
