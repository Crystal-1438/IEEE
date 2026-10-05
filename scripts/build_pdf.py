"""Build Article.pdf from the single source Article.md, without network access.
Setup: python3 -m venv .venv
       .venv/bin/pip install -r scripts/requirements.txt
Build: .venv/bin/python scripts/build_pdf.py
Fonts: Nimbus Roman and Droid Sans Fallback (installed system fonts).
Pandoc's TeX math parser converts equations; Typst embeds text/math fonts.
"""
import json
import re
from pathlib import Path
import pypandoc
import typst

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'Article.md').read_text()
# Keep figure placeholders and captions as one unbreakable object in the PDF.
source = re.sub(
    r'<!-- FIGURE_SLOT:(\d+) -->\s*\n\*([^\n]+)\*',
    lambda m: '\n```{=typst}\n#blank-figure[' + m[2] + ']\n```\n', source)
ast = json.loads(pypandoc.convert_text(source, 'json', format='markdown'))
# Extract the title and author placeholder; the remaining body is two-column.
title = ast['blocks'].pop(0)
assert title['t'] == 'Header'
author = ast['blocks'].pop(0)
assert author['t'] == 'Para'
count = 0


def visit(node):
    global count
    if isinstance(node, list):
        return [visit(x) for x in node]
    if not isinstance(node, dict):
        return node
    if node.get('t') == 'Math' and node['c'][0]['t'] == 'DisplayMath':
        count += 1
        formula = node['c'][1]
        tag = re.search(r'\\tag\{(\d+)\}', formula)
        assert tag and int(tag[1]) == count, 'Equation numbering out of sequence'
        formula = re.sub(r'\\tag\{\d+\}', '', formula).strip()
        converted = pypandoc.convert_text('$$\n'+formula+'\n$$', 'typst', format='markdown').strip()
        assert converted.startswith('$ ') and converted.endswith(' $'), converted
        raw = '#paper-equation($' + converted[1:-1].strip() + '$, "' + str(count) + '")'
        return {'t': 'RawInline', 'c': ['typst', raw]}
    return {key: visit(value) for key, value in node.items()}


ast = visit(ast)
# Keep explicit TABLE titles together with their tables across column/page breaks.
blocks = []
i = 0
while i < len(ast['blocks']):
    current = ast['blocks'][i]
    is_title = (current['t'] == 'Para' and current['c']
                and current['c'][0]['t'] == 'Strong'
                and current['c'][0]['c'][0].get('c') == 'TABLE')
    if is_title and i+1 < len(ast['blocks']) and ast['blocks'][i+1]['t'] == 'Table':
        pair = {**ast, 'blocks': ast['blocks'][i:i+2]}
        rendered = pypandoc.convert_text(json.dumps(pair), 'typst', format='json')
        blocks.append({'t': 'RawBlock', 'c': ['typst', '#block(breakable: false)[\n'+rendered+'\n]']})
        i += 2
    else:
        blocks.append(current)
        i += 1
ast['blocks'] = blocks
body = pypandoc.convert_text(json.dumps(ast), 'typst', format='json', extra_args=['--wrap=none'])
# Pandoc emits #figure with an image and a caption; keep its explicit Fig. labels.
body = body.replace('image("figures/', 'image("../figures/')
# Start references in the second column of the final review page.
body = body.replace('== 参考文献（References）',
    '#colbreak()\n#set text(size: 9pt)\n#set par(justify: false, first-line-indent: 0pt)\n'
    '== 参考文献（References）')
heading_ast = {**ast, 'blocks': [{'t': 'Para', 'c': title['c'][2]}, author]}
heading_text = pypandoc.convert_text(json.dumps(heading_ast), 'typst', format='json')
title_text, author_text = heading_text.strip().split('\n\n', 1)
preamble = (ROOT / 'scripts/paper.typ').read_text()
result = preamble + '\n#align(center)[\n#text(size: 19pt, weight: "bold")[' + title_text + \
    ']\n#v(7pt)\n#text(size: 9pt)[' + author_text + ']\n]\n#v(8pt)\n#columns(2, gutter: 6.3mm)[\n' + body + '\n]\n'
build = ROOT / 'build'
build.mkdir(exist_ok=True)
(build / 'Article.typ').write_text(result)
typst.compile(str(build / 'Article.typ'), output=str(ROOT / 'Article.pdf'), root=str(ROOT))
print(f'Built Article.pdf with {count} numbered equations.')
