"""Reflow Figs. 2 and 8 for an 8.56 cm IEEE column.

Keep the existing control paths and Delta geometry. Produce separate editable
SVGs and high-resolution PNGs so earlier manuscript assets stay reproducible.
At the intended DOCX width, main labels are at least 8 pt; Delta subscripts
are 6 pt. Requires CairoSVG, Pillow, and the locally installed Liberation Sans
and DejaVu Serif fonts.
"""
from html import escape
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import cairosvg
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'figures'
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
PRINT_WIDTH_PT = 3080000 / 12700  # 8.556 cm, within the manuscript's column.
FONT = subprocess.check_output(
    ['fc-match', '-f', '%{file}', 'Liberation Sans'], text=True
)
BOLD_FONT = subprocess.check_output(
    ['fc-match', '-f', '%{file}', 'Liberation Sans:style=Bold'], text=True
)


def save(svg, stem, scale):
    root = ET.fromstring(svg)
    width = float(root.get('width'))
    sizes = [float(t.get('font-size')) for t in root.iter(f'{{{SVG}}}text')]
    smallest_pt = min(sizes) * PRINT_WIDTH_PT / width
    assert smallest_pt >= 8, (stem, smallest_pt)
    (FIGURES / f'{stem}.svg').write_text(svg)
    cairosvg.svg2png(
        bytestring=svg.encode(), write_to=str(FIGURES / f'{stem}.png'), scale=scale
    )
    print(f'{stem}: smallest main label {smallest_pt:.2f} pt at {PRINT_WIDTH_PT:.2f} pt width')


def draw_control():
    width, height = 900, 1760
    parts = [f'''<svg xmlns="{SVG}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>System control workflow with larger labels</title>
<desc>Master-to-arm pose mapping and arm control; chassis joint, feedforward,
and wheel branches. Each motor receives its feedback-control and feedforward
torques. Solid arrows are forward paths and dashed arrows are feedback.</desc>
<defs><marker id="arrow" markerWidth="11" markerHeight="10" refX="10" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L10,5 L0,10 Z" fill="#111"/></marker></defs>
<rect width="{width}" height="{height}" fill="white"/>
<g font-family="Liberation Sans, sans-serif" fill="#111">''']

    def text(x, y, value, size=30, bold=False, backed=False):
        font = ImageFont.truetype(BOLD_FONT if bold else FONT, size)
        length = font.getlength(value)
        assert x - length / 2 >= 0 and x + length / 2 <= width, value
        assert size <= y <= height - 5, value
        if backed:
            parts.append(f'<rect x="{x-length/2-5}" y="{y-size}" width="{length+10}" height="{size+7}" fill="white"/>')
        parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{escape(value)}</text>')

    def block(x, y, w, h, lines, plant=False):
        size, leading = 30, 34
        assert (len(lines)-1)*leading + size <= h-12, lines
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"#eef1f4" if plant else "white"}" stroke="#111" stroke-width="3"/>')
        for i, label in enumerate(lines):
            assert ImageFont.truetype(FONT, size).getlength(label) <= w-18, label
            text(x+w/2, y+h/2+(i-(len(lines)-1)/2)*leading+10, label)

    def line(points, arrow=True, feedback=False):
        coords = ' '.join(f'{x},{y}' for x, y in points)
        dash = ' stroke-dasharray="10 7"' if feedback else ''
        end = ' marker-end="url(#arrow)"' if arrow else ''
        parts.append(f'<polyline points="{coords}" fill="none" stroke="#111" stroke-width="2.8" stroke-linejoin="round"{dash}{end}/>')

    def dot(x, y):
        parts.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#111"/>')

    def sum_torques(x, side):
        parts.append(f'<circle cx="{x}" cy="1420" r="20" fill="white" stroke="#111" stroke-width="2.8"/>')
        text(x-side*25, 1397, '+')
        text(x+side*35, 1410, '+')

    text(450, 34, '(a) Teleoperation and arm control', 32, True)
    block(35, 58, 375, 92, ['Delta master', 'Forward kinematics'])
    block(490, 58, 375, 92, ['RPY handle: moving axes', 'Roll / pitch / yaw'])
    line([(222, 150), (222, 176), (450, 176)], arrow=False)
    line([(678, 150), (678, 176), (450, 176)], arrow=False)
    dot(450, 176)
    line([(450, 176), (450, 200)])
    block(260, 200, 380, 84, ['Master pose: xyz + RPY', 'Wireless link'])
    line([(450, 284), (450, 308), (157, 308), (157, 332)])
    block(35, 332, 245, 122, ['Pose mapping', 'Arm inverse', 'kinematics'])
    line([(280, 393), (330, 393)])
    block(330, 332, 245, 122, ['Cascaded joint', 'PID + gravity', 'feedforward'])
    line([(575, 393), (625, 393)])
    block(625, 350, 240, 86, ['Six-axis arm'], plant=True)
    line([(745, 436), (745, 480), (452, 480), (452, 454)], feedback=True)
    text(600, 516, 'Joint encoders')
    parts.append('<line x1="25" y1="539" x2="875" y2="539" stroke="#888" stroke-width="1.5"/>')

    text(450, 578, '(b) Chassis control', 32, True)
    block(65, 600, 770, 114, ['Chassis commands', 'Translational velocity + acceleration', 'Baseline height + roll / pitch angles'])
    line([(450, 714), (450, 736)], arrow=False)
    dot(450, 736)
    for x in [165, 450, 735]:
        line([(450, 736), (x, 736), (x, 792)])
    for x, title in [(165, 'Joint controller'), (450, 'Feedforward'), (735, 'Wheel controller')]:
        text(x, 775, title, bold=True, backed=True)

    block(40, 792, 250, 146, ['Attitude angle /', 'angular rate', 'P / P loops'])
    block(325, 792, 250, 146, ['Single rigid body', 'Dynamics / force', 'allocation'])
    block(610, 792, 250, 146, ['Mecanum wheel', 'kinematics'])
    line([(165, 938), (165, 1008)])
    text(165, 980, 'Leg-length increment', backed=True)
    block(40, 1008, 250, 148, ['Accumulate', '+ baseline height', 'Leg inverse', 'kinematics'])
    line([(165, 1156), (165, 1222)])
    text(165, 1196, 'Joint-angle targets', backed=True)
    block(40, 1222, 250, 112, ['Joint position /', 'speed cascaded', 'PID / PID'])
    line([(165, 1334), (165, 1400)])
    text(165, 1370, 'Joint torque', backed=True)

    line([(450, 938), (450, 1008)])
    text(450, 980, 'Desired foot forces', backed=True)
    block(325, 1008, 250, 148, ['Wheel dynamics', '+ leg-linkage', 'force mapping'])
    line([(450, 1156), (450, 1378)], arrow=False)
    text(450, 1205, 'Motor torque FF', backed=True)
    dot(450, 1378)
    line([(450, 1378), (300, 1378), (300, 1420), (185, 1420)])
    line([(450, 1378), (600, 1378), (600, 1420), (715, 1420)])
    text(360, 1350, 'Joint FF', backed=True)
    text(540, 1350, 'Wheel FF', backed=True)

    line([(735, 938), (735, 1222)])
    text(735, 1078, 'Wheel-motor', backed=True)
    text(735, 1112, 'speed targets', backed=True)
    block(610, 1222, 250, 112, ['Wheel-motor', 'speed-loop PID'])
    line([(735, 1334), (735, 1400)])
    text(735, 1370, 'Wheel torque', backed=True)
    sum_torques(165, 1)
    sum_torques(735, -1)
    line([(165, 1440), (165, 1490)])
    line([(735, 1440), (735, 1490)])
    text(165, 1472, 'Total joint torque', backed=True)
    text(735, 1472, 'Total wheel torque', backed=True)
    block(40, 1490, 250, 65, ['Leg joint motors'], plant=True)
    block(610, 1490, 250, 65, ['Wheel motors'], plant=True)
    line([(165, 1555), (165, 1597), (285, 1597)])
    line([(735, 1555), (735, 1597), (615, 1597)])
    block(285, 1565, 330, 64, ['Wheel-legged chassis'], plant=True)
    line([(450, 1629), (450, 1660)])
    block(295, 1660, 310, 64, ['IMU + encoders'])
    line([(295, 1692), (15, 1692), (15, 865), (40, 865)], feedback=True)
    line([(15, 1278), (40, 1278)], feedback=True)
    dot(15, 1278)
    line([(605, 1692), (885, 1692), (885, 1278), (860, 1278)], feedback=True)
    text(450, 1753, 'Solid: forward   Dashed: feedback   FF: feedforward')
    parts.append('</g></svg>')
    save('\n'.join(parts), 'Fig2_Control_Flow_Readable', 3)


def enlarge_delta():
    root = ET.parse(FIGURES / 'Delta机械臂几何图-并排大字.svg').getroot()
    for node in root.iter(f'{{{SVG}}}text'):
        label = ''.join(node.itertext()).replace('\u200b', '')
        node.set('font-size', '54')
        # Center panel titles explicitly, now that their widths have changed.
        if label.startswith('(a)'):
            node.set('x', '407'); node.set('text-anchor', 'middle')
        elif label.startswith('(b)'):
            node.set('x', '1201'); node.set('text-anchor', 'middle')
        elif label == 'Parallel platforms':
            node.set('x', '280')
        elif label == 'Bi: elbow':
            node.set('x', '1260')
        elif label in ['yD', 'C2']:
            node.set('x', str(float(node.get('x')) - 30))
        for span in node.iter(f'{{{SVG}}}tspan'):
            if 'font-size' in span.attrib:
                span.set('font-size', '40')
    save(ET.tostring(root, encoding='unicode'), 'Fig8_Delta_Geometry_Readable', 2)


if __name__ == '__main__':
    draw_control()
    enlarge_delta()
