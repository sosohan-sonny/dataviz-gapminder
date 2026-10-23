# 데이터 출처

접근일: 2026-10-23

| 지표 | 데이터셋 / 파일 | URL | 단위 | 원본 범위 |
|---|---|---|---|---|
| 5세 미만 아동사망률 | Gapminder Fast Track · `ddf--datapoints--child_mortality_0_5_year_olds_dying_per_1000_born--by--country--time.csv` | https://github.com/open-numbers/ddf--gapminder--fasttrack | 출생 1,000명당 사망 | 196개국, 1800–2100 |
| 기대수명 | Gapminder Fast Track · `ddf--datapoints--lex--by--country--time.csv` | 위와 같음 | 년 | 196개국, 1800–2100 |
| 합계출산율 | Gapminder Fast Track · `ddf--datapoints--children_per_woman_total_fertility--by--country--time.csv` | 위와 같음 | 여성 1인당 자녀 수 | 197개국, 1800–2100 |
| 1인당 GDP | Gapminder Fast Track · `ddf--datapoints--gdp_pcap--by--country--time.csv` | 위와 같음 | 2017 PPP 불변 국제달러 | 195개국, 1800–2100 |
| 인구 | Gapminder Fast Track · `ddf--datapoints--pop--by--country--time.csv` | 위와 같음 | 명 | 197개국, 1800–2100 |
| 국가 메타데이터 (4개 지역, 소득그룹, ISO3) | Gapminder · `ddf--entities--geo--country.csv` | 위와 같음 | 범주 | — |
| DTP3 접종률 (WHO/UNICEF 추정) | World Bank WDI · 지표 `SH.IMM.IDPT` | https://api.worldbank.org/v2/country/all/indicator/SH.IMM.IDPT?format=json&per_page=20000&date=1980:2024 | 12–23개월 영아 중 % | 1980–2024 |
| 5세 미만 사망률 (UN IGME 추정, Part B 교차 검증용) | World Bank WDI · 지표 `SH.DYN.MORT` | https://api.worldbank.org/v2/country/all/indicator/SH.DYN.MORT?format=json&per_page=20000&date=1960:2022 | 출생아 1,000명당 | 1960–2022 |

Gapminder 원본은 Gapminder 웹사이트(https://www.gapminder.org/data/)의 Fast Track 지표와 같은 데이터이며, 기계가 읽기 좋은 DDF 형식으로 공개된 GitHub 저장소에서 내려받았습니다.

## 사용 범위
- 기간: 1960–2022년. 2023년 이후는 Gapminder의 추계(projection) 비중이 커서 제외했습니다.
- 국가: 179개국. 2022년 인구 15만 명 미만인 17개국과 핵심 지표 결측이 10%를 넘는 Holy See를 제외했습니다.
- DTP3는 Gapminder 179개국 중 177개국이 ISO3 코드로 매칭됩니다. 대만(TWN)은 World Bank 자료에 없고, 홍콩(HKG)은 DTP3 값이 없습니다.

전처리의 상세 기록은 `data/processed/prep_log.txt`에 있습니다.
