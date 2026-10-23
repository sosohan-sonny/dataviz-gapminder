"""report.md → report.html → report.pdf (headless Chrome으로 A4 인쇄)"""
import re
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font: 10.5pt/1.6 "Apple SD Gothic Neo", "Noto Sans KR", sans-serif; color: #1f2328; }
h1 { font-size: 19pt; margin: 0 0 2pt; }
h1 + h2 { font-size: 13pt; color: #5b616b; font-weight: 500; margin: 0 0 12pt; border: none; }
h2 { font-size: 14pt; margin: 18pt 0 6pt; padding-bottom: 3pt; border-bottom: 1.5px solid #1f2328; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; break-after: avoid; }
p, li { margin: 3pt 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 8pt; font-size: 9pt; break-inside: avoid; }
th, td { border: 1px solid #d0cdc6; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #f1efea; }
img { width: 100%; border: 1px solid #e3e1dc; border-radius: 4px; margin-top: 6pt; break-inside: avoid; }
p:has(> img) { break-inside: avoid; break-after: avoid; }
p > em:only-child { display: block; color: #5b616b; font-size: 9pt; margin-bottom: 8pt; }
blockquote { margin: 6pt 0; padding: 6pt 10pt; background: #eef4f9; border-left: 3px solid #0072B2; }
code { font-size: 8.5pt; background: #f1efea; padding: 0 2pt; border-radius: 2px; }
pre { background: #f1efea; padding: 6pt 8pt; font-size: 8.5pt; border-radius: 4px; }
pre code { background: none; padding: 0; }
hr { border: none; margin: 8pt 0; }
"""

LIST_ITEM = re.compile(r"^\s*(?:[-*]|\d+\.)\s")


def to_python_markdown(md):
    """GitHub식 목록 문법을 Python-Markdown이 읽는 형태로 바꾼다.

    - 문단 바로 다음 줄에 오는 목록 앞에 빈 줄을 넣는다(없으면 문단에 붙어 버린다).
    - 2칸 들여쓴 하위 목록을 4칸으로 바꾼다(Python-Markdown은 4칸이어야 중첩으로 인식한다).
    """
    out, prev, in_code = [], "", False
    for line in md.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and LIST_ITEM.match(line):
            indent = len(line) - len(line.lstrip(" "))
            line = " " * (indent * 2) + line.lstrip(" ")
            if prev.strip() and not LIST_ITEM.match(prev) and not prev.startswith("|"):
                out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


md = to_python_markdown((ROOT / "report.md").read_text(encoding="utf-8"))
body = markdown.markdown(md, extensions=["tables", "fenced_code"])
html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>데이터 시각화 중간고사 대체 과제 보고서</title><style>{CSS}</style></head><body>{body}</body></html>"""
html_path = ROOT / "report.html"
html_path.write_text(html, encoding="utf-8")

pdf_path = ROOT / "report.pdf"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True, capture_output=True)
html_path.unlink()
print(f"wrote {pdf_path} ({pdf_path.stat().st_size / 1e6:.1f} MB)")
