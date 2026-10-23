# 소득과 아동 생존: Gapminder 데이터 시각화

데이터 시각화 중간고사 대체 과제(Take-Home Exam v1.1) 제출물입니다.

## 먼저 열어볼 것
1. **온라인 버전**: https://sosohan-sonny.github.io/dataviz-gapminder/
   - 첫 화면 `index.html`에서 Part A와 Part B로 이동합니다.
   - Part A: https://sosohan-sonny.github.io/dataviz-gapminder/explore.html · Part B: https://sosohan-sonny.github.io/dataviz-gapminder/explain.html
   - 저장소: https://github.com/sosohan-sonny/dataviz-gapminder
2. **보고서**: `report.pdf`. 설계 근거, 전처리, 강건성 점검, 한계, 가산점 항목을 그림과 함께 정리했습니다(원문은 `report.md`).
3. **로컬에서 열기**: `docs/explore.html`(Part A), `docs/explain.html`(Part B)을 브라우저로 엽니다.
   - 데이터가 HTML 안에 들어 있어 별도 서버가 필요 없습니다(`file://`로 열어도 동작하는 것을 확인했습니다).
   - 차트 라이브러리(Vega)를 CDN에서 불러오므로 인터넷 연결은 필요합니다.

## Part A 사용법
- 위쪽 컨트롤에서 **지표**와 **연도**를 바꿉니다. 네 그래프의 제목과 단위가 함께 바뀝니다. **▶ 재생**을 누르면 1960년부터 연도가 자동으로 넘어갑니다.
- **국가 선택** 드롭다운에서 국가를 체크하거나, 그래프의 점을 **클릭**해 국가를 고릅니다(Shift+클릭으로 추가, 더블클릭으로 해제). 두 방식은 서로 동기화됩니다.
- 범례의 **대륙**을 클릭하면 해당 대륙만 봅니다.
- **초기화** 버튼을 누르면 처음 화면으로 돌아갑니다. 현재 상태는 파란 상태 표시줄에 나옵니다.
- 주소로 특정 보기를 바로 열 수 있습니다. 예: `explore.html?ind=life_exp&yr=1980&reg=Asia&pick=India,China`
  - `ind`: `child_mort` · `life_exp` · `fertility`
  - `yr`: 1960–2022
  - `reg`: `Africa` · `Americas` · `Asia` · `Europe`
  - `pick`: 쉼표로 구분한 국가명

## 다시 만들기
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/prepare.py       # data/raw → data/processed (정제·결합)
.venv/bin/python src/robustness.py    # Part B 강건성 점검 → data/processed/robustness.json
.venv/bin/python src/part_a.py        # → docs/explore.html
.venv/bin/python src/part_b.py        # → docs/explain.html
.venv/bin/python src/screenshots.py   # 보고서 그림 → report_assets/ (Google Chrome 필요)
.venv/bin/python src/build_report.py  # report.md → report.pdf (Google Chrome 필요)
```
원본 데이터는 `data/raw/`에 포함되어 있습니다. 출처와 접근일은 `data_sources.md`를 참고하세요.

## 폴더 구조
```
data/raw/          원본 (Gapminder CSV, World Bank JSON 2종)
data/processed/    정제 데이터, 전처리 로그, 강건성 점검 결과
src/               prepare · robustness · part_a · part_b · page(HTML 템플릿) · screenshots · build_report
docs/              게시용 HTML (GitHub Pages 루트)
report_assets/     보고서 그림
report.md / .pdf   보고서
```
