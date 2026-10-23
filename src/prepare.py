"""Gapminder + World Bank 데이터를 수집·정제·조인한다.

입력:  data/raw/ (Gapminder fasttrack CSV, World Bank DTP3 JSON)
출력:  data/processed/gapminder_clean.csv  (국가-연도 wide)
       data/processed/dtp3_region.csv      (지역별 DTP3 가중평균)
       data/processed/prep_log.txt         (전처리 기록)
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

START, END = 1960, 2022          # 2023년 이후는 Gapminder 추계(projection) 비중이 커서 제외
MIN_POP = 150_000                # 소국 제외 기준 (2022년 인구)
MAX_MISSING_SHARE = 0.10         # 핵심 지표 결측 비율 상한

INDICATORS = {
    "child_mortality_0_5_year_olds_dying_per_1000_born": "child_mort",
    "lex": "life_exp",
    "children_per_woman_total_fertility": "fertility",
    "gdp_pcap": "gdp_pc",
    "pop": "pop",
}
REGION_KO = {"africa": "Africa", "americas": "Americas", "asia": "Asia", "europe": "Europe"}

log = []


def note(msg):
    print(msg)
    log.append(msg)


# 1. Gapminder 지표 로드 후 (country, time)으로 outer join
frames = []
for concept, short in INDICATORS.items():
    f = RAW / f"ddf--datapoints--{concept}--by--country--time.csv"
    d = pd.read_csv(f).rename(columns={concept: short})
    dup = d.duplicated(["country", "time"]).sum()
    note(f"[load] {short:11s} rows={len(d):6d} countries={d.country.nunique()} years={d.time.min()}-{d.time.max()} dup_keys={dup}")
    frames.append(d.set_index(["country", "time"]))
df = pd.concat(frames, axis=1, join="outer").reset_index()

# 2. 기간 제한 (추계 제외)
df = df[(df.time >= START) & (df.time <= END)]
note(f"[filter] years {START}-{END}: rows={len(df)}")

# 3. 국가 메타데이터 조인 (지역, 소득그룹, ISO3)
geo = pd.read_csv(RAW / "ddf--entities--geo--country.csv")
geo = geo[geo["is--country"] == True][
    ["country", "name", "iso3166_1_alpha3", "world_4region", "income_groups"]
]
df = df.merge(geo, on="country", how="left", validate="many_to_one")
no_meta = df[df.name.isna()].country.unique()
note(f"[geo] countries without metadata: {list(no_meta)}")
df = df[df.name.notna() & df.world_4region.notna()]

# 4. 소국·결측 과다 국가 제외
pop_last = df[df.time == END].set_index("country")["pop"]
small = pop_last[pop_last < MIN_POP].index
note(f"[exclude] pop<{MIN_POP:,} in {END}: {len(small)} countries -> {sorted(df[df.country.isin(small)].name.unique())}")
df = df[~df.country.isin(small)]

core = ["child_mort", "life_exp", "fertility", "gdp_pc"]
miss = df.groupby("country")[core].apply(lambda g: g.isna().mean().max())
too_missing = miss[miss > MAX_MISSING_SHARE].index
note(f"[exclude] >{MAX_MISSING_SHARE:.0%} missing in a core indicator: {sorted(df[df.country.isin(too_missing)].name.unique())}")
df = df[~df.country.isin(too_missing)]

# 5. 남은 결측은 국가 내 선형보간 (양끝 외삽 없음)
before = df[core].isna().sum().sum()
df = df.sort_values(["country", "time"])
df[core] = df.groupby("country")[core].transform(lambda s: s.interpolate(limit_area="inside"))
note(f"[impute] interpolated core cells: {before - df[core].isna().sum().sum()} (remaining NA: {df[core].isna().sum().sum()})")

# 6. World Bank DTP3 (WHO/UNICEF 추정치) 조인: ISO3 기준
payload = json.load(open(RAW / "wb_dtp3.json"))
wb = pd.DataFrame(
    [{"iso3": r["countryiso3code"], "time": int(r["date"]), "dtp3": r["value"]} for r in payload[1]]
)
wb = wb[wb.iso3.str.len() == 3].dropna(subset=["dtp3"])
iso_gm = set(df.iso3166_1_alpha3.dropna())
iso_wb = set(wb.iso3)
note(f"[wb] DTP3 rows={len(wb)}; Gapminder countries matched by ISO3: {len(iso_gm & iso_wb)}/{len(iso_gm)}; unmatched: {sorted(iso_gm - iso_wb)}")
df = df.merge(wb, left_on=["iso3166_1_alpha3", "time"], right_on=["iso3", "time"], how="left").drop(columns="iso3")

# 7. 정리 및 저장
df["region"] = df.world_4region.map(REGION_KO)
df["income_group"] = df.income_groups.str.replace("_", " ").str.capitalize()
clean = df[["country", "name", "iso3166_1_alpha3", "region", "income_group", "time",
            "child_mort", "life_exp", "fertility", "gdp_pc", "pop", "dtp3"]].rename(
    columns={"iso3166_1_alpha3": "iso3", "time": "year"})
assert not clean.duplicated(["country", "year"]).any()
clean.to_csv(OUT / "gapminder_clean.csv", index=False)
note(f"[save] gapminder_clean.csv rows={len(clean)} countries={clean.country.nunique()} years={clean.year.min()}-{clean.year.max()}")
note("[save] missing share:\n" + clean.isna().mean().round(3).to_string())

# 8. 지역별 DTP3 인구가중평균 (Part B 보조 차트)
d = clean.dropna(subset=["dtp3", "pop"])
reg = (d.assign(w=d.dtp3 * d["pop"]).groupby(["region", "year"])
       .agg(w=("w", "sum"), pop=("pop", "sum"), n=("country", "nunique")).reset_index())
reg["dtp3"] = reg.w / reg["pop"]
reg[["region", "year", "dtp3", "n"]].to_csv(OUT / "dtp3_region.csv", index=False)

(OUT / "prep_log.txt").write_text("\n".join(log), encoding="utf-8")
