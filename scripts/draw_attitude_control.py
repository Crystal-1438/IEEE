"""Draw the attitude loop in Article.docx, Eqs. (18) and (19).

Creates an editable SVG and a high-resolution PNG for Word. No PDF output.
Requires cairosvg; English labels and math use locally installed DejaVu fonts.
"""
from pathlib import Path
import cairosvg
import re
import subprocess
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
MATH_FONT = subprocess.check_output(['fc-match', '-f', '%{file}', 'DejaVu Serif'], text=True)
out = ROOT / 'figures/底盘姿态控制框图'
items = ['''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="1070" viewBox="0 0 760 1070">
<defs><marker id="arrow" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="black"/></marker></defs>
<rect width="760" height="1070" fill="white"/>
<g fill="black" font-family="DejaVu Sans, sans-serif" font-size="27">''']

def text(x, y, value, size=27, anchor='middle', math=False):
    font = 'DejaVu Serif' if math else 'DejaVu Sans, sans-serif'
    if math:
        plain = re.sub('<[^>]+>', '', value).replace('&#8203;', '')
        width = ImageFont.truetype(MATH_FONT, size).getlength(plain)
        x -= width / 2 if anchor == 'middle' else width if anchor == 'end' else 0
        anchor = 'start'
    items.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{font}" font-size="{size}">{value}</text>')

def sym(base, sub='', sup=''):
    if base == 'χ̇':
        s = '<tspan dx="8" dy="-17">·</tspan><tspan dx="-17" dy="17" font-style="italic">χ</tspan>'
    else:
        s = f'<tspan font-style="italic">{base}</tspan>'
    if sub:
        s += f'<tspan dy="7" font-size="19">{sub}</tspan><tspan dy="-7">&#8203;</tspan>'
    if sup:
        s += f'<tspan dx="-7" dy="-13" font-size="19">{sup}</tspan><tspan dy="13">&#8203;</tspan>'
    return s

def arrow(points):
    points = ' '.join(f'{x},{y}' for x, y in points)
    items.append(f'<polyline points="{points}" fill="none" stroke="black" stroke-width="2.5" marker-end="url(#arrow)"/>')

def block(y, lines, height=62, size=27):
    items.append(f'<rect x="125" y="{y}" width="310" height="{height}" fill="white" stroke="black" stroke-width="2.5"/>')
    for j, (label, math) in enumerate(lines):
        text(280, y+height/2+size/3+(j-(len(lines)-1)/2)*min(34, (height-14)/len(lines)), label, size, math=math)

def summing(y):
    items.append(f'<circle cx="280" cy="{y}" r="21" fill="white" stroke="black" stroke-width="2.5"/>')
    text(247, y-23, '+', 25, math=True)
    text(319, y-9, '−', 25, math=True)

# The same scalar controller is configured for roll and pitch.
text(420, 32, 'Separate loops for roll and pitch', 25)
text(225, 61, sym('χ', 'd')+'[k]', 27, 'end', True)
arrow([(280, 40), (280, 79)])
summing(100)
arrow([(280,121),(280,159)])
text(305,147,sym('e','χ')+'[k]',25,'start',True)
block(159,[(sym('k','p,χ'),True)])
arrow([(280,221),(280,270)])
text(235,254,sym('χ̇','d')+'[k]',25,'end',True)
summing(291)
arrow([(280,312),(280,347)])
block(347,[(sym('k','h,χ'),True)])
arrow([(280,409),(280,452)])
text(305,438,'Δ'+sym('u','χ')+'[k]',25,'start',True)
block(452,[('Accumulate + limit',False),('Block outward updates',False),('when saturated',False)],86,size=23)
arrow([(280,538),(280,586)])
text(305,568,sym('u','ϕ')+', '+sym('u','θ'),25,'start',True)
block(586,[('Four-leg height allocation',False),('Eq. (19)',False)],86,size=23)
arrow([(28,629),(125,629)])
text(69,609,sym('h','0'),27,math=True)
arrow([(280,672),(280,716)])
text(305,701,sym('h','i','d'),25,'start',True)
block(716,[('Leg inverse kinematics',False)],size=25)
arrow([(280,778),(280,820)])
text(305,806,'Joint targets',25,'start')
block(820,[('Joint servos',False)],size=25)
arrow([(280,882),(280,926)])
text(305,911,'Body motion',25,'start')
block(926,[('IMU',False),('Attitude / angular rate',False)],86,size=25)
# Two independent measurement outputs: no differentiation block is implied.
arrow([(435,951),(552,951),(552,291),(301,291)])
arrow([(435,989),(688,989),(688,100),(301,100)])
# Keep both measurement labels equally offset to the right of their own lines.
text(564,695,sym('χ̇')+'[k]',26,'start',True)
text(700,695,sym('χ')+'[k]',26,'start',True)
text(380,1053,'χ ∈ {ϕ, θ}',26,math=True)
items.append('</g></svg>')
svg = '\n'.join(items)
out.with_suffix('.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(out.with_suffix('.png')),scale=3)
print(out.with_suffix('.svg'))
print(out.with_suffix('.png'))
