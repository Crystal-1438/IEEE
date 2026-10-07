"""Draw Fig. 1: system control architecture from the report and Article.docx.

The overview keeps the master's local gravity support, intrinsic RPY handle,
arm PID / gravity feedforward, and the paper's simplified chassis controller.
Solid arrows show the forward path; dashed arrows carry measured feedback.
Outputs an editable SVG and a 3x PNG for the IEEE single-column Word figure.
"""
from pathlib import Path
from html import escape
import subprocess
import xml.etree.ElementTree as ET
import cairosvg
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures/整机控制流程图'
W, H = 760, 1860
FONT = subprocess.check_output(['fc-match', '-f', '%{file}', 'DejaVu Sans'], text=True)
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<title>System control architecture</title>
<desc>Teleoperation master to six-axis arm, and chassis commands to wheel-legged chassis. Dashed feedback paths show encoder and IMU measurements.</desc>
<defs><marker id="arrow" markerWidth="11" markerHeight="10" refX="10" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L10,5 L0,10 Z" fill="#111"/></marker></defs>
<rect width="{W}" height="{H}" fill="white"/>
<g font-family="DejaVu Sans, sans-serif" fill="#111">''']

def text(x, y, value, size=27, bold=False, anchor='middle'):
    parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{escape(value)}</text>')

def block(x, y, w, h, lines, size=27, plant=False):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"#eef1f4" if plant else "white"}" stroke="#111" stroke-width="2.8"/>')
    leading = size * 1.32
    for i, line in enumerate(lines):
        measured = ImageFont.truetype(FONT, size).getlength(line)
        assert measured < w-18, (line, measured, w)
        text(x+w/2, y+h/2+(i-(len(lines)-1)/2)*leading+size*.35, line, size)

def line(points, arrow=True, feedback=False):
    path = ' '.join(f'{x},{y}' for x,y in points)
    extra = ' stroke-dasharray="9 6"' if feedback else ''
    if arrow: extra += ' marker-end="url(#arrow)"'
    parts.append(f'<polyline points="{path}" fill="none" stroke="#111" stroke-width="2.6" stroke-linejoin="round"{extra}/>')

def dot(x,y):
    parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#111"/>')

# (a) A local gravity-support loop is summarized inside the master block.
# No slave contact-force return or automatic base-motion compensation is implied.
text(380, 39, '(a) Teleoperation and arm control', 30, True)
block(45, 75, 320, 135, ['Delta master', 'Forward kinematics', 'Gravity compensation'], 26)
block(395, 75, 320, 135, ['RPY handle', 'Moving-axis rotations', 'Roll / pitch / yaw'], 26)
line([(205,210),(205,248),(380,248)], arrow=False)
line([(555,210),(555,248),(380,248)], arrow=False)
dot(380,248)
line([(380,248),(380,288)])
block(170,288,420,105,['Master pose: xyz + RPY','Wireless link + TD'],27)
line([(380,393),(380,449)])
block(170,449,420,105,['Pose mapping','Arm inverse kinematics'],27)
text(403,589,'Joint targets',25,anchor='start')
line([(380,554),(380,618)])
block(170,618,420,140,['Joint position / velocity PID','+ gravity feedforward'],27)
line([(380,758),(380,810)])
block(170,810,420,76,['Six-axis arm'],29,plant=True)
# The controller block includes the joint feedback summation and model input.
line([(170,848),(65,848),(65,688),(170,688)],feedback=True)
text(74,790,'Encoders',24,anchor='start')

# (b) Kinematic references and torque feedforward are parallel paths.
parts.append('<line x1="35" y1="933" x2="725" y2="933" stroke="#777" stroke-width="1.5"/>')
text(380, 981, '(b) Chassis control',30,True)
block(170,1015,420,100,['Chassis commands','Velocity, height, attitude'],27)
line([(380,1115),(380,1149)],arrow=False)
dot(380,1149)
line([(380,1149),(205,1149),(205,1185)])
line([(380,1149),(555,1149),(555,1185)])
block(50,1185,315,160,['Motion references','Mecanum wheel speeds','Dual-loop P + leg IK','IMU feedback'],24)
block(395,1185,315,160,['Torque feedforward','Rigid-body allocation','Wheel / leg torque map','State feedback'],25)
line([(205,1345),(205,1398)])
block(50,1398,315,130,['Wheel / leg servos','Position / speed loops','Encoder feedback'],24)
# Sum feedback control and model feedforward immediately before the plant.
line([(205,1528),(205,1570),(360,1570)])
line([(555,1345),(555,1570),(400,1570)])
parts.append('<circle cx="380" cy="1570" r="20" fill="white" stroke="#111" stroke-width="2.6"/>')
text(345,1553,'+',27)
text(416,1553,'+',27)
line([(380,1590),(380,1635)])
block(170,1635,420,78,['Wheel-legged chassis'],28,plant=True)
line([(380,1713),(380,1747)])
block(170,1747,420,72,['IMU + joint encoders'],27)
# Shared measurement bus; each input is selected inside the receiving block.
line([(170,1783),(22,1783),(22,1265),(50,1265)],feedback=True)
line([(22,1463),(50,1463)],feedback=True)
dot(22,1463)
# Measured configuration / attitude also supplies the model feedforward.
line([(590,1783),(738,1783),(738,1265),(710,1265)],feedback=True)
text(380,1850,'Solid: forward path     Dashed: feedback',23)
parts.append('</g></svg>')
svg='\n'.join(parts)
ET.fromstring(svg)
OUT.with_suffix('.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(OUT.with_suffix('.png')),scale=3)
print(OUT.with_suffix('.svg'))
print(OUT.with_suffix('.png'))
