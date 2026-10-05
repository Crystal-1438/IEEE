"""Check the generated review PDF for dropped content, numbering and layout bounds."""
from pathlib import Path
import re
import unicodedata
from collections import Counter
from zipfile import ZipFile
from xml.etree import ElementTree as E
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
# CJK hanging punctuation may extend one glyph beyond the template's text area.
pdf = pymupdf.open(ROOT / 'Article.pdf')
text = '\n'.join(page.get_text() for page in pdf)
assert len(pdf) > 0
numbers = [int(x) for x in re.findall(r'\((\d+)\)', text)]
expected_numbers=[int(n) for n in re.findall(r'\\tag\{(\d+)\}',(ROOT/'Article.md').read_text())]
assert numbers == expected_numbers, numbers
for n in [1, 2, 4, 5, 6, 7, 8, 9]:
    assert f'Fig. {n}.' in text
for key in ['TABLE I.', 'TABLE II.', 'TABLE III.', 'TABLE IV.',
            'Introduction', 'Related Work', 'Proposed Method',
            'Experiments and Results', 'Conclusion', 'References',
            '0.89', '0.51', '42.7', '16483', '16488']:
    assert key.casefold() in text.casefold(), key
assert '&' not in text, 'TeX alignment marker leaked into PDF'
assert sum(0x1d400 <= ord(c) <= 0x1d7ff for c in text) > 100, 'Styled mathematical identifiers lost'
assert '\ufffd' not in text, 'Replacement glyph in extracted text'
# Check all styled identifiers against the editable source, including zero
# vectors. Counts catch dropped glyphs and incorrect matrix/vector conversion.
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
with ZipFile(ROOT/'Article.docx') as z:
    doc=E.fromstring(z.read('word/document.xml'))
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
prose=''.join(t.text or '' for t in doc.iter(W+'t'))
assert len(re.sub(r'\s','',text))>=0.9*len(re.sub(r'\s','',prose)),'Possible missing prose'
expected=Counter()
for run in doc.iter(M+'r'):
    sty=run.find(M+'rPr/'+M+'sty');t=run.find(M+'t')
    if sty is None or t is None:continue
    value=sty.get(M+'val')
    if value not in ['b','bi']:continue
    for c in t.text or '':
        if not c.isalnum():continue
        name=unicodedata.name(c).removeprefix('LATIN ').removeprefix('GREEK ').replace(' LETTER','')
        expected[unicodedata.lookup('MATHEMATICAL '+('BOLD ITALIC ' if value=='bi' else 'BOLD ')+name)]+=1
actual=Counter(c for c in text if unicodedata.name(c,'').startswith('MATHEMATICAL BOLD'))
assert actual==expected,('Missing',expected-actual,'Unexpected',actual-expected)
assert text.count('ℬ')==2,'Calligraphic workspace set B lost'
expected_reals=sum(t.text=='R' for r in doc.iter(M+'r')
    if (scr:=r.find(M+'rPr/'+M+'scr')) is not None and scr.get(M+'val')=='double-struck'
    for t in r.findall(M+'t'))
assert text.count('ℝ')==expected_reals,'Real-number symbol lost'
# Every non-ASCII mathematical operator in the source must survive export.
source_symbols=Counter(c for t in doc.iter(M+'t') for c in t.text or ''
    if ord(c)>127 and not c.isspace() and unicodedata.category(c)=='Sm')
for c,n in source_symbols.items():assert text.count(c)>=n,(c,n,text.count(c))
font_xrefs = set()
for index, page in enumerate(pdf):
    assert len(page.get_text().strip()) > 100, f'Unexpected empty page {index+1}'
    for span in page.get_texttrace():
        for codepoint,glyph,origin,bounds in span['chars']:
            assert glyph!=0,(index+1,'Missing font glyph',chr(codepoint))
            assert bounds[0]>=30 and bounds[2]<=page.rect.width-27,(index+1,'Clipped glyph',chr(codepoint),bounds)
    for block in page.get_text('dict')['blocks']:
        if block['type'] != 0:
            continue
        for line in block['lines']:
            for span in line['spans']:
                x0, y0, x1, y1 = span['bbox']
                assert x0 >= 30 and x1 <= page.rect.width-27, (index+1, span['text'], span['bbox'])
                assert y0 >= 14 and y1 <= page.rect.height-14, (index+1, span['text'], span['bbox'])
                if index > 0 or y0 > 140:
                    # A4 column content must not bridge the central gutter.
                    assert not (x0 < 290 and x1 > 306), (index+1, span['text'], span['bbox'])
    for font in page.get_fonts(full=True):
        font_xrefs.add(font[0])
for xref in font_xrefs:
    assert pdf.extract_font(xref)[3], f'Font {xref} is not embedded'
print(f'PDF validation: PASS ({len(pdf)} pages, {len(numbers)} ordered equations, 8 figure slots, '
      f'{len(font_xrefs)} embedded fonts, no out-of-bounds text)')
print('Visual inspection is also required after layout changes.')
