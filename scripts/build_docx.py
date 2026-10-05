"""Build Article.docx using the repository's actual IEEE A4 Word template.
Pandoc supplies editable Office Math; template styles and section properties
are retained. Run with the dependencies in scripts/requirements.txt.
"""
from copy import deepcopy
from pathlib import Path
import io
import re
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as E
import pypandoc

ROOT = Path(__file__).resolve().parents[1]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W, 'm': M}
for prefix, uri in [('w', W), ('m', M), ('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'),
                    ('wp','http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'),
                    ('a','http://schemas.openxmlformats.org/drawingml/2006/main'),
                    ('pic','http://schemas.openxmlformats.org/drawingml/2006/picture')]:
    E.register_namespace(prefix, uri)


def el(name, attrs=None):
    prefix, local = name.split(':')
    return E.Element('{'+NS[prefix]+'}'+local,
                     {'{'+NS[prefix]+'}'+k: str(v) for k,v in (attrs or {}).items()})


def prop(parent, name, attrs=None):
    tag = el(name).tag
    found = parent.find(tag)
    if found is None:
        found = el(name)
        parent.append(found)
    for k,v in (attrs or {}).items(): found.set('{'+NS[name.split(':')[0]]+'}'+k,str(v))
    return found


def ppr(p):
    found = p.find('w:pPr',NS)
    if found is None:
        found=el('w:pPr');p.insert(0,found)
    return found


def style(p, sid, numbered=False):
    pr=ppr(p)
    prop(pr,'w:pStyle',{'val':sid})
    prop(pr,'w:snapToGrid',{'val':0})
    if not numbered: prop(prop(pr,'w:numPr'),'w:numId',{'val':0})


def plain_text(p):
    return ''.join(t.text or '' for t in p.iter('{'+W+'}t'))


def paragraph(text='',sid='7'):
    p=el('w:p');style(p,sid)
    if text:
        r=el('w:r');t=el('w:t');t.text=text;r.append(t);p.append(r)
    return p


def size(p, halfpoints):
    prop(prop(ppr(p),'w:rPr'),'w:sz',{'val':halfpoints})
    for r in list(p.iter('{'+W+'}r'))+list(p.iter('{'+M+'}r')):
        pr=prop(r,'w:rPr');prop(pr,'w:sz',{'val':halfpoints});prop(pr,'w:szCs',{'val':halfpoints})
        r.remove(pr);r.insert(1 if r.find('m:rPr',NS) is not None else 0,pr)


def table(widths, border=False):
    t=el('w:tbl');pr=el('w:tblPr');t.append(pr)
    prop(pr,'w:tblW',{'w':sum(widths),'type':'dxa'})
    prop(pr,'w:tblLayout',{'type':'fixed'})
    prop(pr,'w:tblInd',{'w':0,'type':'dxa'})
    borders=prop(pr,'w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        prop(borders,'w:'+side,{'val':'single' if border else 'nil','sz':4,'color':'B0B0B0'})
    margins=prop(pr,'w:tblCellMar')
    for side in ['top','left','bottom','right']:prop(margins,'w:'+side,{'w':0,'type':'dxa'})
    grid=el('w:tblGrid');t.append(grid)
    row=el('w:tr');t.append(row);prop(prop(row,'w:trPr'),'w:cantSplit')
    for width in widths:
        grid.append(el('w:gridCol',{'w':width}))
        cell=el('w:tc');cp=el('w:tcPr');cell.append(cp)
        prop(cp,'w:tcW',{'w':width,'type':'dxa'});prop(cp,'w:vAlign',{'val':'center'})
        row.append(cell)
    return t,row


source=(ROOT/'Article.md').read_text()
source=re.sub(r'<!-- FIGURE_SLOT:(\d+) -->',r'FIGURESLOT\1',source)
source=re.sub(r'\\tag\{\d+\}\n', '',source)
build=ROOT/'build';build.mkdir(exist_ok=True)
pypandoc.convert_text(source,'docx',format='markdown',outputfile=str(build/'template-content.docx'),
    extra_args=['--reference-doc='+str(ROOT/'conference-template-a4.docx'),'--resource-path='+str(ROOT)])
with ZipFile(build/'template-content.docx') as z: files={n:z.read(n) for n in z.namelist()}
with ZipFile(ROOT/'conference-template-a4.docx') as z:
    template=E.fromstring(z.read('word/document.xml'))
    original_styles=z.read('word/styles.xml')
sections=list(template.iter('{'+W+'}sectPr'))
body_section=next(deepcopy(s) for s in sections if s.find('w:cols',NS).get('{'+W+'}num')=='2')
title_section=deepcopy(sections[0])
# Author count is unconfirmed: retain one centered author placeholder, no fake authors.
for ref in list(title_section):
    if ref.tag.endswith('Reference') or ref.tag == '{'+W+'}titlePg':title_section.remove(ref)
root=E.fromstring(files['word/document.xml']);body=root.find('w:body',NS)
result=[]; equation_number=0; in_references=False; abstract_next=False; title_done=False
column_width=(11906-2*907-360)//2
for child in list(body):
    if child.tag=='{'+W+'}sectPr': continue
    if child.tag=='{'+W+'}tbl':
        # Fit the table to the template's column, retaining editable cells.
        pr=prop(child,'w:tblPr');prop(pr,'w:tblW',{'w':column_width,'type':'dxa'})
        prop(pr,'w:tblLayout',{'type':'fixed'})
        grid=child.find('w:tblGrid',NS); cols=list(grid)
        widths=[column_width//len(cols)]*len(cols);widths[-1]+=column_width-sum(widths)
        for c,width in zip(cols,widths):c.set('{'+W+'}w',str(width))
        for row_i,row in enumerate(child.findall('w:tr',NS)):
            prop(prop(row,'w:trPr'),'w:cantSplit')
            for cell,width in zip(row.findall('w:tc',NS),widths):
                prop(prop(cell,'w:tcPr'),'w:tcW',{'w':width,'type':'dxa'})
                for p in cell.findall('w:p',NS):
                    style(p,'24' if row_i==0 else '26');size(p,16)
                    prop(ppr(p),'w:spacing',{'before':0,'after':0,'line':240,'lineRule':'auto'})
                    prop(ppr(p),'w:keepNext',{'val':1 if row_i<len(child.findall('w:tr',NS))-1 else 0})
        result.append(child);continue
    if child.tag != '{'+W+'}p':
        result.append(child);continue
    p=child;text=plain_text(p)
    if not title_done:
        style(p,'21');title_done=True;result.append(p);continue
    if text.startswith('作者、单位'):
        style(p,'14');ppr(p).append(title_section);result.append(p);continue
    if text=='摘要（Abstract）':abstract_next=True;continue
    if abstract_next:
        style(p,'12');p.insert(1,paragraph('摘要（Abstract）—').find('w:r',NS));abstract_next=False
    elif text.startswith('关键词'):style(p,'29')
    elif re.match(r'^FIGURESLOT\d+$',text):
        empty=paragraph('\u00a0','1');pr=ppr(empty)
        prop(pr,'w:keepNext');prop(pr,'w:keepLines')
        prop(pr,'w:spacing',{'before':0,'after':0,'line':1644,'lineRule':'exact'})
        borders=prop(pr,'w:pBdr')
        for side in ['top','left','bottom','right']:
            prop(borders,'w:'+side,{'val':'single','sz':4,'color':'B0B0B0','space':1})
        result.append(empty);continue
    elif p.find('m:oMathPara',NS) is not None:
        equation_number+=1
        t,row=table([column_width-390,390])
        prop(t.find('w:tblPr',NS),'w:tblCaption',{'val':f'Equation {equation_number}'})
        style(p,'17');size(p,18)
        prop(ppr(p),'w:spacing',{'before':100,'after':100,'line':240,'lineRule':'auto'})
        prop(ppr(p),'w:ind',{'firstLine':0,'left':0,'right':0})
        prop(ppr(p),'w:jc',{'val':'center'})
        number=paragraph(f'({equation_number})','1');size(number,16)
        prop(ppr(number),'w:jc',{'val':'right'})
        row.findall('w:tc',NS)[0].append(p);row.findall('w:tc',NS)[1].append(number)
        result.append(t);continue
    elif re.match(r'^[IVX]+\. ',text):style(p,'2')
    elif re.match(r'^[A-D]\. ',text):style(p,'3')
    elif re.match(r'^\d+\)',text):style(p,'4')
    elif re.match(r'^TABLE [IVX]+\.',text):
        style(p,'28');prop(ppr(p),'w:keepNext')
        for rpr in p.findall('.//w:rPr',NS):
            for b in rpr.findall('w:b',NS):rpr.remove(b)
    elif text.startswith('Fig. '):
        style(p,'18')
        for rpr in p.findall('.//w:rPr',NS):
            for it in rpr.findall('w:i',NS):rpr.remove(it)
    elif text in ['致谢（Acknowledgment）','参考文献（References）']:
        style(p,'6');prop(ppr(p),'w:keepNext');in_references=text.startswith('参考文献')
    elif in_references:style(p,'22')
    elif p.find('.//w:drawing',NS) is not None:
        style(p,'1');prop(ppr(p),'w:keepNext')
        # Both existing figures are sized to a single template column.
        for extent in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent'):
            old=int(extent.get('cx'));new=column_width*635;ratio=new/old
            extent.set('cx',str(new));extent.set('cy',str(round(int(extent.get('cy'))*ratio)))
            for ext in p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}ext'):
                if 'cx' in ext.attrib:ext.set('cx',str(new));ext.set('cy',extent.get('cy'))
    else:style(p,'7');size(p,20)
    result.append(p)
# The template ends its two-column body with a continuous single-column
# section. Retain that structure so Word can balance the final page.
end=paragraph('', '1')
prop(ppr(end),'w:spacing',{'before':0,'after':0,'line':1,'lineRule':'exact'})
ppr(end).append(body_section)
result.append(end)
result.append(deepcopy(sections[-1]))
body[:]=result
# Pandoc emits alignment markers as literal ampersands in OMML equation arrays.
# Remove those TeX layout markers, retaining all mathematical operators/content.
for parent in root.iter():
    for run in list(parent):
        if run.tag == '{'+M+'}r' and ''.join(run.itertext()) == '&':
            parent.remove(run)
# Mirror explicit Office Math style into Word run properties for Writer import.
# This preserves upright units/descriptors and bold vectors/matrices in both apps.
for run in root.findall('.//m:r',NS):
    math_style=run.find('m:rPr/m:sty',NS)
    if math_style is not None:
        value=math_style.get('{'+M+'}val')
        wp=prop(run,'w:rPr')
        prop(wp,'w:b',{'val':1 if value in ['b','bi'] else 0})
        prop(wp,'w:i',{'val':1 if value in ['i','bi'] else 0})
        run.remove(wp);run.insert(1 if run.find('m:rPr',NS) is not None else 0,wp)
files['word/document.xml']=E.tostring(root,encoding='utf-8',xml_declaration=True)
# The source template's styles are the authority; no reconstructed lookalike styles.
files['word/styles.xml']=original_styles
with ZipFile(ROOT/'Article.docx','w',ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,data)
assert equation_number==45
print('Built Article.docx: original template styles, 2 columns, 45 editable numbered equations.')
