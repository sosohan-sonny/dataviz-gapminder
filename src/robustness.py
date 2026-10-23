"""Part B 메시지의 강건성 점검 → data/processed/robustness.json

1. 독립 출처 교차 검증: Gapminder 아동사망률 대신 UN IGME 추정치(World Bank SH.DYN.MORT)를 쓴다.
   IGME 추정은 조사·인구동태 자료에 기반하며 소득을 입력으로 쓰지 않는다.
2. 인구가중: 국가 동일 가중 대신 인구가중 중앙값으로 소득 구간별 비교.
3. 최저 소득 구간(<$2천)의 2020년 구성 국가 확인.
4. 연도 쌍을 바꿔도 결론이 유지되는지 확인.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
FRAC = 0.6
INCOMES = [1000, 2000, 4000, 8000, 16000]
BANDS = [(0, 2000, "<$2천"), (2000, 4000, "$2천–4천"), (4000, 8000, "$4천–8천"),
         (8000, 16000, "$8천–1만6천"), (16000, 1e9, "≥$1만6천")]

d = pd.read_csv(OUT / "gapminder_clean.csv")
payload = json.load(open(RAW / "wb_u5mr.json"))
igme = pd.DataFrame([{"iso3": r["countryiso3code"], "year": int(r["date"]), "igme": r["value"]}
                     for r in payload[1] if r["value"] is not None])
d = d.merge(igme, on=["iso3", "year"], how="left")  # 지역 집계(WLD 등)는 Gapminder 국가와 매칭되지 않아 자동 제외


def loess_at(df, col, year):
    s = df[df.year == year].dropna(subset=["gdp_pc", col])
    fit = lowess(s[col], np.log10(s.gdp_pc), frac=FRAC, return_sorted=True)
    return {g: float(np.interp(np.log10(g), fit[:, 0], fit[:, 1])) for g in INCOMES}, len(s)


def drops(df, col, y0, y1):
    a, n0 = loess_at(df, col, y0)
    b, n1 = loess_at(df, col, y1)
    return {"n": [n0, n1], "at": {g: [round(a[g], 1), round(b[g], 1), round((1 - b[g] / a[g]) * 100, 1)] for g in INCOMES}}


def wmedian(values, weights):
    o = np.argsort(values)
    v, w = np.asarray(values)[o], np.asarray(weights)[o]
    return float(v[np.searchsorted(np.cumsum(w), w.sum() / 2)])


res = {}

# 1. 독립 출처(IGME) — 두 해 모두 IGME 값이 있는 국가만(고정 패널)
for y0, y1 in [(1970, 2020), (1980, 2015)]:
    both = set(d[(d.year == y0) & d.igme.notna()].country) & set(d[(d.year == y1) & d.igme.notna()].country)
    panel = d[d.country.isin(both)]
    res[f"igme_{y0}_{y1}"] = drops(panel, "igme", y0, y1)
    res[f"gapminder_same_panel_{y0}_{y1}"] = drops(panel, "child_mort", y0, y1)
    print(f"[IGME {y0}->{y1}] panel={len(both)}개국")
    for g in INCOMES:
        a = res[f"igme_{y0}_{y1}"]["at"][g]
        b = res[f"gapminder_same_panel_{y0}_{y1}"]["at"][g]
        print(f"   ${g:>6,}: IGME {a[0]:6.1f}->{a[1]:5.1f} (-{a[2]:.0f}%) | Gapminder {b[0]:6.1f}->{b[1]:5.1f} (-{b[2]:.0f}%)")

# 두 출처 값의 일치도 (1970년)
s = d[(d.year == 1970)].dropna(subset=["igme", "child_mort"])
res["agreement_1970"] = {"n": len(s), "pearson_r": round(float(s.igme.corr(s.child_mort)), 3),
                         "median_abs_diff": round(float((s.igme - s.child_mort).abs().median()), 1)}
print("[agreement 1970]", res["agreement_1970"])

# 2. 인구가중 중앙값 (Gapminder), 소득 구간별 1970 vs 2020
res["pop_weighted_bands"] = {}
for lo, hi, name in BANDS:
    row = []
    for y in (1970, 2020):
        s = d[(d.year == y) & (d.gdp_pc >= lo) & (d.gdp_pc < hi)].dropna(subset=["child_mort", "pop"])
        row.append((round(wmedian(s.child_mort, s["pop"]), 1), len(s)))
    res["pop_weighted_bands"][name] = {"1970": row[0], "2020": row[1], "drop_pct": round((1 - row[1][0] / row[0][0]) * 100, 1)}
    print(f"[pop-weighted] {name:>10}: 1970 {row[0][0]:6.1f} (n={row[0][1]}) -> 2020 {row[1][0]:5.1f} (n={row[1][1]})"
          f"  -{res['pop_weighted_bands'][name]['drop_pct']:.0f}%")

# 3. 최저 소득 구간의 2020년 구성
low = d[(d.year == 2020) & (d.gdp_pc < 2000)].sort_values("child_mort", ascending=False)
res["lowest_band_2020"] = low[["name", "gdp_pc", "child_mort"]].round(0).to_dict("records")
print("[<$2천, 2020]", ", ".join(low.name))

# 4. 연도 쌍 강건성 (Gapminder 전체)
res["year_pairs"] = {f"{a}_{b}": drops(d, "child_mort", a, b) for a, b in [(1970, 2020), (1980, 2015), (1960, 2022)]}
for k, v in res["year_pairs"].items():
    print(f"[years {k}] drop range {min(x[2] for x in v['at'].values()):.0f}–{max(x[2] for x in v['at'].values()):.0f}%")

(OUT / "robustness.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
