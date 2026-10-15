"""Create vertically compact variants of Figs. 2 and 6 from their source SVGs."""
from pathlib import Path
import xml.etree.ElementTree as ET
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / 'figures'
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)


def compact(source: str, output: str, scale_y: float) -> None:
    root = ET.parse(FIGURES / source).getroot()
    width = float(root.attrib['width'])
    old_height = float(root.attrib['height'])
    new_height = round(old_height * scale_y)
    root.set('height', str(new_height))
    root.set('viewBox', f'0 0 {width:g} {new_height}')

    for node in root.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if tag == 'rect':
            for attr in ('y', 'height'):
                if attr in node.attrib:
                    node.set(attr, f'{float(node.attrib[attr]) * scale_y:.3f}')
        elif tag == 'text' and 'y' in node.attrib:
            node.set('y', f'{float(node.attrib["y"]) * scale_y:.3f}')
        elif tag == 'circle' and 'cy' in node.attrib:
            node.set('cy', f'{float(node.attrib["cy"]) * scale_y:.3f}')
        elif tag == 'line':
            for attr in ('y1', 'y2'):
                if attr in node.attrib:
                    node.set(attr, f'{float(node.attrib[attr]) * scale_y:.3f}')
        elif tag == 'polyline' and 'points' in node.attrib:
            pairs = []
            for point in node.attrib['points'].split():
                x, y = point.split(',')
                pairs.append(f'{x},{float(y) * scale_y:.3f}')
            node.set('points', ' '.join(pairs))

    out_svg = FIGURES / output
    ET.ElementTree(root).write(out_svg, encoding='utf-8', xml_declaration=True)
    out_png = out_svg.with_suffix('.png')
    cairosvg.svg2png(url=str(out_svg), write_to=str(out_png), scale=3)
    print(out_svg, out_png)


compact('整机控制流程图.svg', 'Fig2_Control_Flow_Compact.svg', 0.90)
compact('底盘姿态控制框图.svg', 'Fig6_Attitude_Control_Compact.svg', 0.95)
