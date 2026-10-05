"""Verify actual template use and preservation of editable equations/figure slots."""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E
import json
import re
from collections import Counter
import pypandoc
ROOT=Path(__file__).resolve().parents[1]
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
W='{'+NS['w']+'}'
source=(ROOT/'Article.md').read_text()
equation_count=len(re.findall(r'\\tag\{\d+\}',source))
with ZipFile(ROOT/'conference-template-a4.docx') as template, ZipFile(ROOT/'Article.docx') as doc:
    assert template.read('word/styles.xml')==doc.read('word/styles.xml'),'Template styles changed'
    root=E.fromstring(doc.read('word/document.xml'))
    src=E.fromstring(template.read('word/document.xml'))
    original=next(s for s in src.iter(W+'sectPr') if s.find('w:cols',NS).get(W+'num')=='2')
    actual=next(s for s in root.iter(W+'sectPr') if s.find('w:cols',NS).get(W+'num')=='2')
    assert E.tostring(original)==E.tostring(actual),'Body section differs from template'
    assert len(root.findall('.//m:oMathPara',NS))==equation_count,'Lost a display equation'
    ast=json.loads(pypandoc.convert_file(str(ROOT/'Article.md'),'json'))
    def math_count(node):
        if isinstance(node,dict): return int(node.get('t')=='Math')+sum(math_count(v) for v in node.values())
        if isinstance(node,list): return sum(math_count(v) for v in node)
        return 0
    assert len(root.findall('.//m:oMath',NS))==math_count(ast),'Lost inline mathematical expressions'
    assert not any((t.text or '')=='&' for t in root.findall('.//m:t',NS)), 'Literal alignment marker'
    assert len(root.findall('.//w:pBdr',NS))==8,'Missing figure blank'
    names=[s.get(W+'val') for s in root.findall('.//w:tblCaption',NS)]
    assert names==[f'Equation {i}' for i in range(1,equation_count+1)],names
    for r in root.findall('.//m:r',NS):
        tags=[x.tag for x in r]
        if '{'+NS['m']+'}rPr' in tags and W+'rPr' in tags:
            assert tags.index('{'+NS['m']+'}rPr')<tags.index(W+'rPr'),'Invalid OMML property order'
    # The previous build passed expression-count checks while turning every
    # matrix into a bold italic vector. Verify semantic style, not just presence.
    M='{'+NS['m']+'}'
    expected_matrices=Counter(''.join(re.findall(r'\\mathbf\{([A-Za-z]+)\}',source)))
    actual_matrices=Counter()
    for r in root.findall('.//m:r',NS):
        t=r.find('m:t',NS);sty=r.find('m:rPr/m:sty',NS)
        value=sty.get(M+'val') if sty is not None else 'i'
        if value=='b' and t is not None:
            actual_matrices.update(c for c in t.text or '' if c.isalpha())
        fonts=r.find('w:rPr/w:rFonts',NS)
        assert fonts is not None and fonts.get(W+'ascii')=='Cambria Math'
    assert actual_matrices==expected_matrices,(actual_matrices,expected_matrices)
    settings=E.fromstring(doc.read('word/settings.xml'))
    assert settings.find('m:mathPr/m:mathFont',NS).get(M+'val')=='Cambria Math'
    for style_id in ['21','14','12','29','2','3','4','7','17','18','22','24','26','28']:
        assert any(s.get(W+'val')==style_id for s in root.findall('.//w:pStyle',NS)),style_id
    text=''.join(t.text or '' for t in root.findall('.//w:t',NS))
    for forbidden in ['Paper Title*','author1@example.com','FIGURESLOT','use style:']:
        assert forbidden not in text,forbidden
print(f'DOCX validation: PASS (exact template styles/columns, {equation_count} editable display equations, '
      'inline math, 8 blank figures, no template guidance text)')
