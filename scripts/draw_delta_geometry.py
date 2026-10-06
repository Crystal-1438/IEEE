"""Reproducible Delta geometry for Article.docx (metres internally).

Draws a three-limb view and a radial section without modifying the reference
bitmap. Produces editable SVG and PNG; no PDF is generated.
"""
from pathlib import Path
import math
import re
import subprocess
from PIL import ImageFont
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures/Delta机械臂几何图'
R, r, LD, LP = .095, .066, .150, .200
theta = math.radians(50)
elbow_r = R + LD * math.cos(theta)
elbow_x = -LD * math.sin(theta)
px = elbow_x - math.sqrt(LP**2 - (elbow_r-r)**2)
# Frame D: +X is the platform normal toward the fixed platform;
# +Z points from O to A1; +Y completes the right-handed basis.
P = (px, 0., 0.)
FONT = subprocess.check_output(['fc-match', '-f', '%{file}', 'DejaVu Serif'], text=True)
BLUE, ORANGE, GREEN, INK = '#174f86', '#bb4807', '#087e77', '#17232c'
items = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1070" viewBox="0 0 1600 1070">
<defs><marker id="arrow" markerWidth="13" markerHeight="11" refX="12" refY="5.5" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M0,0 L12,5.5 L0,11 Z" fill="context-stroke"/></marker></defs>
<rect width="1600" height="1070" fill="white"/>
<g font-family="DejaVu Serif" fill="{INK}" font-size="36">''']

def text(x, y, s, size=36, anchor='start', color=INK):
    plain = re.sub('<[^>]+>', '', s).replace('&#8203;', '')
    width = ImageFont.truetype(FONT, size).getlength(plain)
    if anchor == 'middle': x -= width/2
    if anchor == 'end': x -= width
    items.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color}">{s}</text>')

def sym(base, sub='', bold=False):
    s = f'<tspan font-style="italic" font-weight="{"bold" if bold else "normal"}">{base}</tspan>'
    if sub:
        sub = sub.replace('i', '<tspan font-style="italic">i</tspan>')
        s += f'<tspan dy="9" font-size="26">{sub}</tspan><tspan dy="-9">&#8203;</tspan>'
    return s

def line(a, b, color=INK, width=3, dash=None, arrow=False, both=False):
    extra = f' stroke-dasharray="{dash}"' if dash else ''
    if arrow or both: extra += ' marker-end="url(#arrow)"'
    if both: extra += ' marker-start="url(#arrow)"'
    items.append(f'<path d="M{a[0]:.2f},{a[1]:.2f} L{b[0]:.2f},{b[1]:.2f}" fill="none" stroke="{color}" stroke-width="{width}"{extra}/>')

def poly(points, stroke, fill='none', width=3, dash=None):
    pts = ' '.join(f'{x:.2f},{y:.2f}' for x,y in points)
    d = f' stroke-dasharray="{dash}"' if dash else ''
    items.append(f'<polygon points="{pts}" stroke="{stroke}" fill="{fill}" stroke-width="{width}"{d}/>')

def point(p, color=INK, radius=6):
    items.append(f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="{radius}" fill="{color}" stroke="white" stroke-width="2"/>')

def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def dot(a,b):return sum(x*y for x,y in zip(a,b))

# A proper orthographic camera above the fixed-platform plane. The previous
# oblique view was from the negative-X side and made the handedness ambiguous.
az,el=math.radians(20),math.radians(25)
screen_right=(0.,-math.sin(az),math.cos(az))
screen_up=(math.cos(el),-math.sin(el)*math.cos(az),-math.sin(el)*math.sin(az))
toward_viewer=cross(screen_right,screen_up)
assert abs(dot(screen_right,screen_up))<1e-12
assert abs(dot(screen_right,screen_right)-1)<1e-12
assert abs(dot(screen_up,screen_up)-1)<1e-12
assert toward_viewer[0]>0
ex,ey,ez=(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)
assert cross(ex,ey)==ez and cross(ez,ex)==ey

def project(v):
    return (430+1450*dot(screen_right,v),240-1450*dot(screen_up,v))

def add(v, w): return tuple(a+b for a,b in zip(v,w))
def mul(a, v): return tuple(a*b for b in v)
def norm(v): return math.sqrt(sum(a*a for a in v))
def diff(a,b): return tuple(x-y for x,y in zip(a,b))

limbs=[]
for i in range(3):
    psi=2*math.pi*i/3
    e=(0.,-math.sin(psi),math.cos(psi))
    t=(0.,-math.cos(psi),-math.sin(psi))
    assert norm(diff(cross(ex,e),t))<1e-12
    A=mul(R,e); B=add(mul(elbow_r,e),(elbow_x,0,0)); C=add(P,mul(r,e))
    c=add(B,mul(-r,e))
    assert abs(norm(diff(B,A))-LD)<1e-12
    assert abs(norm(diff(C,B))-LP)<1e-12
    assert abs(norm(diff(P,c))-LP)<1e-12
    limbs.append((A,B,C,t))

# (a) Complete mechanism. Both platform planes have normal (1,0,0).
line((816,55),(816,980),'#c8ced3',2)
poly([project(x[0]) for x in limbs], BLUE, '#edf4fb', 4)
poly([project(x[2]) for x in limbs], BLUE, '#dbeaf6', 4)
for i in [1,0,2]:
    A,B,C,t=limbs[i]
    line(project(A),project(B),ORANGE,7)
    offset=mul(.008,t)
    corners=[add(B,offset),add(B,mul(-1,offset)),add(C,mul(-1,offset)),add(C,offset)]
    poly([project(v) for v in corners],GREEN,width=4)
    line(project(B),project(C),GREEN,2,'8 7')
    for v in [A,B,C]: point(project(v))

O=project((0,0,0)); pp=project(P)
line(O,pp,INK,2.5,'9 7',True)
point(O);point(pp)
text(451,223,'O',38)
text(453,439,sym('p','D',True),40)
text(pp[0]+18,pp[1]+37,'P',38)
for v,label,delta in [((0,0,.145),'z',(13,21)),((0,.145,0),'y',(-20,35)),((.125,0,0),'x',(16,-3))]:
    tip=project(v);line(O,tip,INK,3,arrow=True)
    text(tip[0]+delta[0],tip[1]+delta[1],sym(label,'D'),37)
text(461,146,'{D}',36)
text(529,64,'Right-handed frame',28)
text(532,111,sym('e','x',True)+' × '+sym('e','y',True)+' = '+sym('e','z',True),32)

offsets={0:((10,-15),(15,8),(18,26)),1:((-57,-17),(-69,-9),(-28,-20)),2:((-56,28),(-67,8),(-59,28))}
for i,(A,B,C,t) in enumerate(limbs):
    for j,(base,v) in enumerate(zip('ABC',[A,B,C])):
        q=project(v);dx,dy=offsets[i][j]
        text(q[0]+dx,q[1]+dy,sym(base,str(i+1)),35)
line((203,112),(365,229),BLUE,2.5)
text(50,88,'Fixed platform',39,color=BLUE)
line((287,752),project(add(P,(-0.,.016,-.026))),BLUE,2.5)
text(47,802,'Moving platform',39,color=BLUE)
text(357,850,'Parallel platforms',35,color=BLUE)
line((66,897),(127,897),ORANGE,7)
text(150,908,'Active arm',36,color=ORANGE)
line((66,945),(127,945),GREEN,4)
line((66,955),(127,955),GREEN,4)
text(150,961,'Passive arm (paired rods)',36,color=GREEN)
text(407,1030,'(a) Three-limb geometry',37,'middle')

# (b) True radial section for the symmetric illustrated configuration.
# C_i is the real platform joint. c_i is the equivalent sphere center,
# shifted from B_i by r_D e_i, as in Article Eq. (24).
def section(rho,x):return (950+1800*rho,180-1800*x)
oo=section(0,0);aa=section(R,0);bb=section(elbow_r,elbow_x)
cc=section(r,px);pp2=section(0,px);eqc=section(elbow_r-r,elbow_x)
line((oo[0],oo[1]+10),(oo[0],pp2[1]),'#82909a',2,'7 6')
line(oo,(oo[0],55),INK,3,arrow=True)
text(oo[0]-21,51,sym('x','D'),36)
line(oo,(1515,180),INK,2.5,'8 6',True)
text(1426,150,sym('e','i',True),36)
text(1180,103,'Radially outward',33)
line(oo,aa,BLUE,5)
line(pp2,cc,BLUE,5)
line(aa,bb,ORANGE,7)
line(bb,cc,GREEN,7)
line(eqc,pp2,GREEN,2.5,'10 7')
line(eqc,bb,INK,2,'6 5')
for v in [oo,aa,bb,cc,pp2,eqc]:point(v)
text(oo[0]-40,oo[1]+12,'O',36)
text(aa[0]-22,aa[1]-19,sym('A','i'),37)
text(bb[0]+17,bb[1]+12,sym('B','i'),37)
text(cc[0]+17,cc[1]+17,sym('C','i'),37)
text(pp2[0]-35,pp2[1]+16,'P',36)
text(eqc[0]-52,eqc[1]-18,sym('c','i',True),37)
text((aa[0]+bb[0])/2-57,(aa[1]+bb[1])/2+10,sym('L','D'),40,color=ORANGE)
text((bb[0]+cc[0])/2+20,(bb[1]+cc[1])/2+15,sym('L','P'),40,color=GREEN)
# Correct clockwise angle in the scaled section: endpoints follow the plotted arm.
angle=math.atan2(bb[1]-aa[1],bb[0]-aa[0])
assert abs(angle-theta)<1e-12  # The radial section preserves physical angles.
rad=69
arcpts=[(aa[0]+rad*math.cos(angle*j/28),aa[1]+rad*math.sin(angle*j/28)) for j in range(29)]
for a,b in zip(arcpts,arcpts[1:]):line(a,b,ORANGE,2.8)
line(arcpts[-2],arcpts[-1],ORANGE,2.8,arrow=True)
text(aa[0]+78,aa[1]+57,sym('θ','D,i'),36,color=ORANGE)

def dim(a,b,y,label):
    line((a[0],a[1]),(a[0],y), '#7a8891',1.5)
    line((b[0],b[1]),(b[0],y), '#7a8891',1.5)
    line((a[0],y),(b[0],y),BLUE,2,both=True)
    text((a[0]+b[0])/2,y-12,label,36,'middle',BLUE)
dim(oo,aa,128,sym('R','D'))
dim(pp2,cc,pp2[1]+54,sym('r','D'))
dim(eqc,bb,bb[1]+54,sym('r','D'))
text(866,778,sym('A','i')+': base joint',31)
text(1197,778,sym('B','i')+': elbow joint',31)
text(866,826,sym('C','i')+': platform joint',31)
text(866,874,sym('c','i',True)+': equivalent sphere center',31)
text(866,932,'Dashed link: equivalent constraint',31,color=GREEN)
text(1201,1030,'(b) Single-limb geometry',37,'middle')
items.append('</g></svg>')
svg='\n'.join(items)
OUT.with_suffix('.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(OUT.with_suffix('.png')),scale=2)
# A stacked version keeps labels readable in the single-column Word layout.
inner=svg[svg.index('<defs>'):svg.rindex('</svg>')]
inner=re.sub(r'<path[^>]*stroke="#c8ced3"[^>]*/>', '', inner)
stacked='''<svg xmlns="http://www.w3.org/2000/svg" width="840" height="2160" viewBox="0 0 840 2160"><rect width="840" height="2160" fill="white"/>
<svg x="0" y="0" width="840" height="1070" viewBox="0 0 808 1070">'''+inner.replace('id="arrow"','id="arrow-a"').replace('url(#arrow)','url(#arrow-a)')+'''</svg>
<svg x="0" y="1090" width="840" height="1070" viewBox="824 0 776 1070">'''+inner.replace('id="arrow"','id="arrow-b"').replace('url(#arrow)','url(#arrow-b)')+'</svg></svg>'
stack_out=OUT.with_name(OUT.name+'-单栏')
stack_out.with_suffix('.svg').write_text(stacked)
cairosvg.svg2png(bytestring=stacked.encode(),write_to=str(stack_out.with_suffix('.png')),scale=2)
print(f'Geometry verified: LD={LD} m, LP={LP} m, all three limbs close; platform x={px:.6f} m.')
print(OUT.with_suffix('.png'))
