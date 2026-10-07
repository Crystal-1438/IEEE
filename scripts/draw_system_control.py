"""Draw Fig. 1 with explicit joint, wheel, and feedforward control paths.

Panel (a) omits master gravity compensation and TD. Panel (b) follows the
specified chassis controller: attitude P/P -> leg-height increment -> leg IK
-> joint PID/PID; Mecanum kinematics -> wheel-speed PID; rigid-body dynamics
-> desired foot forces -> wheel dynamics / leg force mapping. Each motor
channel sums its feedback-controller output with its own feedforward torque.
Outputs editable SVG and high-resolution PNG; no PDF is generated.
"""
from pathlib import Path
from html import escape
import subprocess
import xml.etree.ElementTree as ET
import cairosvg
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures/整机控制流程图'
W, H = 980, 2360
FONT = subprocess.check_output(['fc-match', '-f', '%{file}', 'DejaVu Sans'], text=True)
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<title>System control architecture</title>
<desc>Teleoperation and arm control, followed by three parallel chassis branches: joint controller, torque feedforward, and Mecanum wheel controller. Joint and wheel motor torques each sum controller output and feedforward.</desc>
<defs><marker id="arrow" markerWidth="12" markerHeight="11" refX="11" refY="5.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L11,5.5 L0,11 Z" fill="#111"/></marker></defs>
<rect width="{W}" height="{H}" fill="white"/>
<g font-family="DejaVu Sans, sans-serif" fill="#111">''']

def text(x, y, value, size=30, bold=False, anchor='middle', backed=False):
    if backed:
        width = ImageFont.truetype(FONT, size).getlength(value) + 14
        left = x-width/2 if anchor == 'middle' else x-7
        parts.append(f'<rect x="{left}" y="{y-size}" width="{width}" height="{size+7}" fill="white"/>')
    parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{escape(value)}</text>')

def block(x, y, w, h, lines, size=30, plant=False):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"#eef1f4" if plant else "white"}" stroke="#111" stroke-width="3"/>')
    leading = size * 1.27
    assert leading * (len(lines)-1)+size < h-8, lines
    for i, label in enumerate(lines):
        width = ImageFont.truetype(FONT, size).getlength(label)
        assert width < w-16, (label, width, w)
        text(x+w/2, y+h/2+(i-(len(lines)-1)/2)*leading+size*.35, label, size)

def line(points, arrow=True, feedback=False):
    path = ' '.join(f'{x},{y}' for x,y in points)
    extra = ' stroke-dasharray="10 7"' if feedback else ''
    if arrow: extra += ' marker-end="url(#arrow)"'
    parts.append(f'<polyline points="{path}" fill="none" stroke="#111" stroke-width="2.8" stroke-linejoin="round"{extra}/>')

def dot(x,y):
    parts.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#111"/>')

def summing(x,y,side):
    parts.append(f'<circle cx="{x}" cy="{y}" r="21" fill="white" stroke="#111" stroke-width="2.8"/>')
    text(x-23 if side == 1 else x+23,y-30,'+',30)
    text(x+side*34,y-18,'+',30)

# (a) The arm retains its own gravity feedforward. The master and link do not
# display the two functions explicitly removed by the user.
text(490, 40, '(a) Teleoperation and arm control', 34, True)
block(55,80,390,122,['Delta master','Forward kinematics'],31)
block(535,80,390,122,['RPY handle: moving axes','Roll / pitch / yaw'],30)
line([(250,202),(250,238),(490,238)],arrow=False)
line([(730,202),(730,238),(490,238)],arrow=False)
dot(490,238)
line([(490,238),(490,272)])
block(275,272,430,102,['Master pose: xyz + RPY','Wireless link'],31)
line([(490,374),(490,415),(190,415),(190,459)])
block(55,459,270,138,['Pose mapping','Arm inverse','kinematics'],30)
line([(325,528),(362,528)])
block(362,459,296,138,['Joint cascaded PID','+ gravity','feedforward'],29)
line([(658,528),(705,528)])
block(705,479,220,98,['Six-axis arm'],31,plant=True)
line([(815,577),(815,644),(510,644),(510,597)],feedback=True)
text(675,681,'Joint encoders',28)

parts.append('<line x1="40" y1="713" x2="940" y2="713" stroke="#777" stroke-width="1.5"/>')
text(490,764,'(b) Chassis control',34,True)
block(75,805,830,143,['Chassis commands','Translational velocity + acceleration','Baseline height + roll / pitch angles'],31)
line([(490,948),(490,980)],arrow=False)
dot(490,980)
line([(490,980),(185,980),(185,1062)])
line([(490,980),(490,1062)])
line([(490,980),(795,980),(795,1062)])
# Headings sit to the side of each branch input line, with a white backing.
for x, label in [(185,'Joint controller'),(490,'Feedforward'),(795,'Wheel controller')]:
    parts.append(f'<rect x="{x-132}" y="1003" width="264" height="41" fill="white"/>')
    text(x,1033,label,29,True)

# Joint controller: the increment is accumulated before inverse kinematics.
block(60,1062,250,162,['Attitude angle /','angular-rate','cascaded P loops'],28)
line([(185,1224),(185,1320)])
text(185,1257,'Equivalent leg-length',25,backed=True)
text(185,1290,'increment',27,backed=True)
block(60,1320,250,142,['Accumulate','+ baseline height','Leg inverse','kinematics'],27)
line([(185,1462),(185,1560)])
text(185,1502,'Joint-angle targets',26,backed=True)
block(60,1560,250,150,['Single-joint','position / speed','cascaded PID'],29)
line([(185,1710),(185,1849)])
text(185,1750,'Joint controller',26,backed=True)
text(185,1782,'torque',27,backed=True)

# Feedforward: desired contact force is an intermediate physical quantity.
block(365,1062,250,162,['Single-rigid-body','dynamics','Force allocation'],27)
line([(490,1224),(490,1320)])
text(490,1275,'Desired foot forces',26,backed=True)
block(365,1320,250,204,['Mecanum wheel','dynamics','+ leg-linkage','force mapping'],29)
line([(490,1524),(490,1760)],arrow=False)
text(490,1583,'Motor torque',27,backed=True)
text(490,1617,'feedforward',27,backed=True)
dot(490,1760)
line([(490,1760),(340,1760),(340,1870),(206,1870)])
line([(490,1760),(640,1760),(640,1870),(774,1870)])
text(357,1801,'Joint FF',27,backed=True)
text(357,1833,'torque',27,backed=True)
text(623,1801,'Wheel FF',27,backed=True)
text(623,1833,'torque',27,backed=True)

# Wheel controller: a speed-loop PID, not the leg position / speed cascade.
block(670,1062,250,162,['Mecanum wheel','kinematics'],29)
line([(795,1224),(795,1560)])
text(795,1370,'Wheel-motor',27,backed=True)
text(795,1406,'speed targets',27,backed=True)
block(670,1560,250,150,['Wheel-motor','speed-loop PID'],29)
line([(795,1710),(795,1849)])
text(795,1750,'Wheel controller',26,backed=True)
text(795,1782,'torque',27,backed=True)

# Separate sums ensure both motor types receive their own feedforward term.
summing(185,1870,1)
summing(795,1870,-1)
line([(185,1891),(185,1970)])
line([(795,1891),(795,1970)])
text(185,1932,'Total joint torque',26,backed=True)
text(795,1932,'Total wheel torque',26,backed=True)
block(60,1970,250,92,['Leg joint motors'],29,plant=True)
block(670,1970,250,92,['Wheel motors'],29,plant=True)
line([(185,2062),(185,2130),(310,2130)])
line([(795,2062),(795,2130),(670,2130)])
block(310,2084,360,92,['Wheel-legged chassis'],29,plant=True)
line([(490,2176),(490,2230)])
block(310,2230,360,84,['IMU + encoders'],30)
# Typed controller blocks select angle/rate, joint position/speed, and wheel
# speed from this shared measurement bus; model-state details stay in the text.
line([(310,2272),(24,2272),(24,1143),(60,1143)],feedback=True)
line([(24,1635),(60,1635)],feedback=True)
dot(24,1635)
line([(670,2272),(956,2272),(956,1635),(920,1635)],feedback=True)
text(490,2350,'Solid: forward path   Dashed: feedback   FF: feedforward',25)
parts.append('</g></svg>')
svg='\n'.join(parts)
ET.fromstring(svg)
OUT.with_suffix('.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(),write_to=str(OUT.with_suffix('.png')),scale=3)
print(OUT.with_suffix('.svg'))
print(OUT.with_suffix('.png'))
