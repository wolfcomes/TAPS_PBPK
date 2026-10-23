#!/usr/bin/env python3
"""Render the canonical report with a local table of contents and inline CSS."""
from hashlib import sha256
from html import escape
from pathlib import Path
import re

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/reports/research_report.md"
OUTPUT = SOURCE.with_suffix(".html")


def render():
    raw = SOURCE.read_bytes()
    body = BeautifulSoup(MarkdownIt("commonmark").enable("table").render(raw.decode()), "html.parser")
    toc = []
    used = set()
    for heading in body.select("h1, h2, h3"):
        label = heading.get_text()
        base = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", label.lower()).strip("-")
        anchor = base
        n = 2
        while anchor in used:
            anchor = f"{base}-{n}"
            n += 1
        used.add(anchor)
        heading["id"] = anchor
        if heading.name != "h1":
            toc.append(f'<a class="{heading.name}" href="#{anchor}">{escape(label)}</a>')
    for table in body.select("table"):
        wrapper = body.new_tag("div", attrs={"class": "table-scroll"})
        table.wrap(wrapper)
    title = escape(body.h1.get_text())
    digest = sha256(raw).hexdigest()
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="source-sha256" content="{digest}">
<title>{title}</title>
<style>
:root {{color-scheme:light; --ink:#243247; --muted:#617188; --line:#dbe3ec; --link:#145fa0;}}
* {{box-sizing:border-box}} html {{scroll-behavior:smooth;scroll-padding-top:24px}}
body {{margin:0;color:var(--ink);background:#f4f7fa;font:16px/1.85 system-ui,"Noto Sans CJK SC",sans-serif}}
nav {{position:fixed;inset:0 auto 0 0;width:292px;overflow:auto;padding:26px 20px;background:#edf2f7;border-right:1px solid var(--line)}}
nav strong {{display:block;margin-bottom:14px}} nav a {{display:block;line-height:1.6;margin:10px 0;text-decoration:none;font-size:14px}}
nav .h3 {{padding-left:16px;font-size:13px;color:var(--muted)}}
main {{max-width:1100px;margin:0 32px 0 324px;padding:34px 44px 70px;background:white;min-height:100vh}}
h1 {{font-size:30px;line-height:1.4;margin:0 0 24px}} h2 {{font-size:24px;margin-top:48px;padding-top:12px;border-top:1px solid var(--line)}}
h3 {{font-size:19px;margin-top:28px}} a {{color:var(--link)}} a:hover {{text-decoration:underline}}
p {{margin:14px 0}} img {{max-width:100%;height:auto}} code {{font-size:.9em;background:#edf2f7;padding:2px 4px;border-radius:3px}}
pre {{overflow:auto;background:#f4f7fa;padding:18px}} pre code {{background:none;padding:0}}
.table-scroll {{overflow-x:auto;margin:20px 0}} table {{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7}}
th,td {{border:1px solid var(--line);padding:10px 12px;vertical-align:top;text-align:left}} th {{background:#edf2f7}}
blockquote {{border-left:4px solid #b7cbde;margin-left:0;padding-left:18px;color:var(--muted)}}
.source {{font-size:13px;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:14px}}
@media(max-width:1000px) {{nav {{position:static;width:auto;max-height:42vh;border-bottom:1px solid var(--line)}} main {{margin:0;padding:24px;max-width:none}}}}
@media print {{nav,.source {{display:none}} main {{margin:0;padding:0;max-width:none}} h2 {{break-after:avoid}} tr,img {{break-inside:avoid}}}}
</style></head><body>
<nav aria-label="报告目录"><strong>研究报告 · 目录</strong><a href="../../README.md">项目首页</a>{''.join(toc)}</nav>
<main><p class="source">由 <a href="research_report.md">research_report.md</a> 生成 · <a href="../plans/research_plan.md">当前研究计划</a></p>{body}</main>
</body></html>'''


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Built {OUTPUT.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")
