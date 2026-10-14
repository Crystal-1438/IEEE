"""Normalize the English paper's Strict DOCX for conventional DOCX readers.

Usage: python3 scripts/convert_article5_to_transitional.py INPUT.docx OUTPUT.docx
Input and output may be the same path. Images and text are never re-encoded.
This handles the constructs present in Article5, not every possible Strict file.
Namespace mapping follows https://learn.microsoft.com/en-us/office/open-xml/about-the-open-xml-sdk
"""

import argparse
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import posixpath
import re
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

STRICT = "http://purl.oclc.org/ooxml/"
TRANSITIONAL = "http://schemas.openxmlformats.org/"
W = TRANSITIONAL + "wordprocessingml/2006/main"
M = TRANSITIONAL + "officeDocument/2006/math"
MAP = {
    STRICT + family + "/": TRANSITIONAL + family + "/2006/"
    for family in ("wordprocessingml", "drawingml", "officeDocument")
}
FACTORS = {"pt": Decimal(20), "in": Decimal(1440), "cm": Decimal(1440) / Decimal("2.54"),
           "mm": Decimal(1440) / Decimal("25.4"), "pc": Decimal(240), "pi": Decimal(240)}
MEASURE = re.compile(r"(-?\d+(?:\.\d+)?)(pt|in|cm|mm|pc|pi|%)\Z")
TWIPS = {
    "tblW": {"w"}, "tcW": {"w"}, "gridCol": {"w"}, "tblInd": {"w"},
    "top": {"w"}, "bottom": {"w"}, "start": {"w"}, "end": {"w"},
    "left": {"w"}, "right": {"w"}, "spacing": {"before", "after", "line"},
    "ind": {"start", "end", "left", "right", "firstLine", "hanging"},
    "pgSz": {"w", "h"}, "pgMar": {"top", "bottom", "left", "right", "header", "footer", "gutter"},
    "cols": {"space"}, "col": {"w", "space"}, "tab": {"pos"},
    "defaultTabStop": {"val"}, "framePr": {"hSpace", "vSpace", "x", "y", "w", "h"},
}


def integer(value):
    return str(int(value.to_integral_value(rounding=ROUND_HALF_UP)))


def normalize(raw):
    text = raw.decode("utf-8")
    for old, new in MAP.items():
        text = text.replace(old, new)
    text = text.replace(' w:conformance="strict"', "")

    def tag(match):
        prefix, local, rest = match.groups()

        def attribute(a):
            name, value = a.groups()
            unit = MEASURE.fullmatch(value)
            if unit:
                number, suffix = unit.groups()
                if prefix == "w" and suffix != "%":
                    assert name.startswith("w:") and name[2:] in TWIPS.get(local, set()), (local, name, value)
                    value = integer(Decimal(number) * FACTORS[suffix])
                elif prefix == "a" and suffix == "%":
                    value = integer(Decimal(number) * 1000)
                elif prefix == "w" and suffix == "%":
                    assert local in {"zoom", "w"} and name in {"w:percent", "w:val"}, (local, name, value)
                    value = integer(Decimal(number))
                else:
                    raise ValueError((prefix, local, name, value))
            if prefix == "w" and local in {"jc", "lvlJc", "tab"} and name == "w:val":
                value = {"start": "left", "end": "right"}.get(value, value)
            if prefix == "w" and local == "ind":
                name = {"w:start": "w:left", "w:end": "w:right", "w:startChars": "w:leftChars",
                        "w:endChars": "w:rightChars"}.get(name, name)
            return f' {name}="{value}"'

        rest = re.sub(r'\s+([\w:]+)="([^"]*)"', attribute, rest)
        return f"<{prefix}:{local}{rest}>"

    text = re.sub(r"<(w|a):(\w+)\b([^<>]*)>", tag, text)
    # Change logical cell margins/borders only; w:lvl/w:start is a numbering value.
    for container in ("tcMar", "tblCellMar", "tblBorders", "tcBorders", "pBdr"):
        pattern = rf"<w:{container}\b[^>]*>.*?</w:{container}>"
        text = re.sub(pattern, lambda m: re.sub(
            r"(<\/?w:)(start|end)(?=[\s/>])",
            lambda t: t[1] + {"start": "left", "end": "right"}[t[2]], m[0]), text, flags=re.S)
    assert STRICT not in text
    ET.fromstring(text)
    return text.encode("utf-8")


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def verify(original, converted):
    for name, raw in original.items():
        if not name.endswith((".xml", ".rels")):
            assert converted[name] == raw, name
            continue
        a, b = ET.fromstring(raw), ET.fromstring(converted[name])
        assert list(a.itertext()) == list(b.itertext()), name
        assert len(list(a.iter())) == len(list(b.iter())), name
        for x, y in zip(a.iter(), b.iter()):
            # Check measurements independent of the serialized XML replacement.
            for key, value in x.attrib.items():
                unit = MEASURE.fullmatch(value)
                if not unit:
                    continue
                mapped_key = key
                for old, new in MAP.items():
                    mapped_key = mapped_key.replace(old, new)
                if local_name(x.tag) == "ind":
                    mapped_key = mapped_key.replace("}start", "}left").replace("}end", "}right")
                number, suffix = unit.groups()
                factor = FACTORS[suffix] if suffix != "%" else (
                    Decimal(1000) if "drawingml/" in x.tag else Decimal(1))
                assert abs(Decimal(y.attrib[mapped_key]) - Decimal(number) * factor) <= Decimal("0.5"), (name, key)
        # Every equation remains structurally identical apart from its namespace.
        math_a = [e for e in a.iter() if local_name(e.tag) == "oMath"]
        math_b = [e for e in b.iter() if local_name(e.tag) == "oMath"]
        assert len(math_a) == len(math_b)
        for eq_a, eq_b in zip(math_a, math_b):
            expected = ET.tostring(eq_a, encoding="unicode")
            for old, new in MAP.items():
                expected = expected.replace(old, new)
            assert ET.tostring(ET.fromstring(expected)) == ET.tostring(eq_b), name
        if name.endswith(".rels"):
            base = "" if name == "_rels/.rels" else posixpath.dirname(posixpath.dirname(name))
            ids = [e.get("Id") for e in b]
            assert len(ids) == len(set(ids)), name
            for rel in b:
                if rel.get("TargetMode") != "External":
                    target = posixpath.normpath(posixpath.join(base, rel.get("Target"))).lstrip("/")
                    assert target in converted, (name, target)
    document = ET.fromstring(converted["word/document.xml"])
    assert document.tag == "{" + W + "}document"
    sizes = document.findall(".//{" + W + "}pgSz")
    assert all(e.get("{" + W + "}w") == "12240" and e.get("{" + W + "}h") == "15840" for e in sizes)
    print("Verified: Letter page dimensions, text, editable formulas, images and package relationships.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with ZipFile(args.source) as z:
        assert z.testzip() is None
        infos, comment = z.infolist(), z.comment
        original = {i.filename: z.read(i.filename) for i in infos}
    # Logical-to-physical mapping below assumes this English paper's LTR layout.
    for name, raw in original.items():
        if name.endswith(".xml"):
            assert not re.search(rb'<w:(?:bidi|rtl|bidiVisual)\b', raw), name
    converted = {n: normalize(b) if n.endswith((".xml", ".rels")) else b for n, b in original.items()}
    verify(original, converted)
    with tempfile.NamedTemporaryFile(dir=args.output.parent, suffix=".docx", delete=False) as f:
        temp = Path(f.name)
    try:
        with ZipFile(temp, "w") as z:
            z.comment = comment
            for info in infos:
                z.writestr(info, converted[info.filename])
        with ZipFile(temp) as z:
            assert z.testzip() is None
        temp.replace(args.output)
    finally:
        temp.unlink(missing_ok=True)
    print("Updated XML parts:", sum(original[n] != converted[n] for n in original))


if __name__ == "__main__":
    main()
