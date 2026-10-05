"""Check the generated review PDF for dropped content, numbering and layout bounds."""
from pathlib import Path
import re
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
# CJK hanging punctuation may extend one glyph beyond the template's text area.
pdf = pymupdf.open(ROOT / 'Article.pdf')
text = '\n'.join(page.get_text() for page in pdf)
assert len(pdf) > 0
numbers = [int(x) for x in re.findall(r'\((\d+)\)', text)]
assert numbers == list(range(1, 46)), numbers
for n in [1, 2, 4, 5, 6, 7, 8, 9]:
    assert f'Fig. {n}.' in text
for key in ['TABLE I.', 'TABLE II.', 'TABLE III.', 'TABLE IV.',
            'Introduction', 'Related Work', 'Proposed Method',
            'Experiments and Results', 'Conclusion', 'References',
            '0.89', '0.51', '42.7', '16483', '16488']:
    assert key.casefold() in text.casefold(), key
assert len(text) > 14000, 'Possible missing equations during Word export'
assert '&' not in text, 'TeX alignment marker leaked into PDF'
assert sum(0x1d400 <= ord(c) <= 0x1d7ff for c in text) > 100, 'Styled mathematical identifiers lost'
assert '\ufffd' not in text, 'Replacement glyph in extracted text'
font_xrefs = set()
for index, page in enumerate(pdf):
    assert len(page.get_text().strip()) > 100, f'Unexpected empty page {index+1}'
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
print(f'PDF validation: PASS ({len(pdf)} pages, 45 ordered equations, 8 figure slots, '
      f'{len(font_xrefs)} embedded fonts, no out-of-bounds text)')
print('Visual inspection is also required after layout changes.')
