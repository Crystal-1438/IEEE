"""Export the template-based Word document using LibreOffice Writer + Math.
Normal system install: python scripts/build_pdf.py
Portable install: python scripts/build_pdf.py --office-root /path/to/unpacked/root
Use --no-rebuild to export an already-built Article.docx.
No network access is used. PDF is replaced only after a successful export.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--office-root',type=Path)
parser.add_argument('--no-rebuild',action='store_true')
args=parser.parse_args()
if not args.no_rebuild:
    subprocess.run([sys.executable,str(ROOT/'scripts/build_docx.py')],check=True,cwd=ROOT)
env=os.environ.copy()
if args.office_root:
    office=args.office_root.resolve()
    program=office/'usr/lib/libreoffice/program'
    soffice=str(program/'soffice')
    env['LD_LIBRARY_PATH']=str(program)+':'+str(office/'usr/lib/x86_64-linux-gnu')
else:
    soffice=shutil.which('libreoffice') or shutil.which('soffice')
    if not soffice:raise SystemExit('Install LibreOffice Writer and Math, or pass --office-root.')
build=ROOT/'build';build.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ieee-word-export-') as temp:
    temporary=Path(temp)
    font_dirs=f'<dir>{office}/usr/share/fonts</dir>' if args.office_root else ''
    font_config=temporary/'fonts.conf'
    font_config.write_text(f'''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig><include>/etc/fonts/fonts.conf</include>{font_dirs}
<cachedir>{temporary}/font-cache</cachedir>
<alias><family>SimSun</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
<alias><family>MS Mincho</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
<alias><family>Times New Roman</family><prefer><family>Liberation Serif</family></prefer></alias>
</fontconfig>''')
    env['FONTCONFIG_FILE']=str(font_config)
    # LibreOffice 26.2 ignores m:sty (p/b/bi) in OMML. Normalize only the
    # temporary export copy: upright text via m:nor; styled identifiers via
    # equivalent Unicode mathematical alphabets. Article.docx remains native.
    M='http://schemas.openxmlformats.org/officeDocument/2006/math'
    W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    with ZipFile(ROOT/'Article.docx') as z: parts={n:z.read(n) for n in z.namelist()}
    doc=E.fromstring(parts['word/document.xml'])
    for parent in doc.iter():
        previous=None
        for run in list(parent):
            if run.tag != '{'+M+'}r':previous=None;continue
            sty=run.find('{'+M+'}rPr/{'+M+'}sty')
            txt=run.find('{'+M+'}t')
            if sty is None or txt is None:previous=None;continue
            value=sty.get('{'+M+'}val')
            if value=='p' and (txt.text or '').isascii() and (txt.text or '').isalpha():
                if previous is not None:
                    previous.text=(previous.text or '')+(txt.text or '');parent.remove(run);continue
                previous=txt
            else:previous=None
    for run in doc.iter('{'+M+'}r'):
        pr=run.find('{'+M+'}rPr')
        sty=pr.find('{'+M+'}sty') if pr is not None else None
        txt=run.find('{'+M+'}t')
        if txt is None:continue
        script=pr.find('{'+M+'}scr') if pr is not None else None
        if script is not None and script.get('{'+M+'}val')=='script':
            # Writer 26.2 also drops calligraphic/script alphabets (the set B).
            converted=[]
            for c in txt.text or '':
                name=unicodedata.name(c).removeprefix('LATIN ').replace(' LETTER','')
                try:converted.append(unicodedata.lookup('MATHEMATICAL SCRIPT '+name))
                except KeyError:converted.append(unicodedata.lookup('SCRIPT '+name))
            txt.text=''.join(converted)
            pr.remove(script)
            if pr.find('{'+M+'}nor') is None:pr.insert(0,E.Element('{'+M+'}nor'))
        if sty is None:continue
        value=sty.get('{'+M+'}val'); original=txt.text or ''
        if value not in ['p','b','bi'] or not any(c.isalnum() for c in original):continue
        if value in ['b','bi']:
            converted=[]
            for c in original:
                name=unicodedata.name(c,'')
                if name.startswith('LATIN '):name=name.removeprefix('LATIN ').replace(' LETTER','')
                elif name.startswith('GREEK '):name=name.removeprefix('GREEK ').replace(' LETTER','')
                elif name.startswith('DIGIT '):pass
                else:converted.append(c);continue
                try:converted.append(unicodedata.lookup('MATHEMATICAL '+('BOLD ITALIC ' if value=='bi' else 'BOLD ')+name))
                except KeyError:raise ValueError(f'Unsupported styled math character: {c!r}')
            txt.text=''.join(converted)
        if pr.find('{'+M+'}nor') is None:pr.insert(0,E.Element('{'+M+'}nor'))
    parts['word/document.xml']=E.tostring(doc,encoding='utf-8',xml_declaration=True)
    export_docx=temporary/'Article.docx'
    with ZipFile(export_docx,'w',ZIP_DEFLATED) as z:
        for name,data in parts.items():z.writestr(name,data)
    command=[soffice,'--headless','-env:UserInstallation='+str((temporary/'profile').as_uri()),
             '--convert-to','pdf:writer_pdf_Export','--outdir',str(temporary),str(export_docx)]
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
    (build/'word-export.log').write_text(result.stdout+'\n'+result.stderr)
    if result.returncode or not (temporary/'Article.pdf').is_file():
        raise SystemExit('Word export failed; see build/word-export.log.')
    import pymupdf
    with pymupdf.open(temporary/'Article.pdf') as pdf:
        text='\n'.join(page.get_text() for page in pdf)
        if len(text)<14000:raise SystemExit('Possible missing formulas. Install LibreOffice Math.')
        pages=len(pdf)
    shutil.copy2(temporary/'Article.pdf',ROOT/'Article.pdf')
print(f'Exported Article.docx -> Article.pdf ({pages} pages) using LibreOffice.')
