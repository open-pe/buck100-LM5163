"""Generate assembly diagrams (footprints + values) for the buck100 PSU board variants.

Run with KiCad's bundled Python (needs pcbnew):

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        assembly/gen_assembly_diagram.py

Writes assembly/buck100-<variant>.svg. Values of the variant-specific parts come from the
"Feedback Resistor and Inductor Values" table in README.md; everything else from the PCB.
"""
import os
from html import escape

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, '..', 'buck100.kicad_pcb')

# role of each part (schematic net analysis: R1 Vout->FB, R2 FB->GND, R5 RON, R4 SW->C1/C6 ripple injection)
ROLE = {  # not drawn; kept for reference
    'U2': 'buck IC', 'R1': 'Rfb1 (top)', 'R2': 'Rfb2 (bottom)', 'R5': 'Rt / RON', 'R4': 'Ra ripple inj.',
    'L1': 'inductor', 'C1': 'Ca ripple inj.', 'C6': 'Cb FB feed-fwd', 'C7': 'bootstrap',
    'C3': 'Cin', 'C4': 'Cin', 'C5': 'Cin', 'C2': 'Cout (polarized)', 'J1': '1=Vout 2=GND 3=Vin',
}

VARIANTS = {
    '3v3': dict(title='3.3 V variant (Vout = 1.2 V x (1 + 390k/220k) = 3.33 V)',
                values={'R1': '390k', 'R2': '220k', 'R5': '100k', 'R4': '470k..715k', 'L1': '470uH'}),
    '11v': dict(title='11 V variant (Vout = 1.2 V x (1 + 470k/56k) = 11.3 V)',
                values={'R1': '470k', 'R2': '56k', 'R5': '390k', 'R4': '600k..1.5M', 'L1': '1.6mH'}),
}

SHORT_VALUE = {  # board values trimmed to what you need at the bench
    'C1': '2.2nF 100V', 'C2': '22uF 25V', 'C3': '220nF 100V', 'C4': '1uF 100V', 'C5': '1uF 100V',
    'C6': '56pF 50V', 'C7': '2.2nF 50V', 'U2': 'LM5163DDAR', 'J1': '1x3 header',
}

PKG = {'C_0805': '0805', 'C_0603': '0603', 'R_0805': '0805', 'HSOP-8': 'HSOP-8', 'CP_Elec_6.3x5.9': 'SMD elko 6.3mm',
       'L_Taiyo-Yuden_NR-80xx': 'NR8040 8x8mm', 'PinHeader_1x03': '1x3 2.54mm'}

S = 45.0  # px per mm
NO_BOX = {'J1'}  # drawn as bare pads with pin names, no courtyard box or value label
COL_VARIANT, COL_COMMON = '#d9480f', '#1c5d99'


def mm(v):
    return pcbnew.ToMM(v)


def pkg(fp):
    name = fp.GetFPID().GetLibItemName().wx_str()
    for k, v in PKG.items():
        if name.startswith(k):
            return v
    return name


def poly_points(poly):
    out = []
    for i in range(poly.OutlineCount()):
        ol = poly.Outline(i)
        out.append([(mm(ol.CPoint(j).x), mm(ol.CPoint(j).y)) for j in range(ol.PointCount())])
    return out


def load():
    board = pcbnew.LoadBoard(PCB)
    bb = board.GetBoardEdgesBoundingBox()
    box = (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom()))
    parts = []
    for fp in board.GetFootprints():
        bottom = fp.IsFlipped()
        cu = pcbnew.B_Cu if bottom else pcbnew.F_Cu
        pads = []
        for p in fp.Pads():
            if not p.IsOnLayer(cu):
                continue
            pads.append((p.GetNumber(), poly_points(p.GetEffectivePolygon(cu, pcbnew.ERROR_INSIDE)),
                         (mm(p.GetPosition().x), mm(p.GetPosition().y))))
        crt = poly_points(fp.GetCourtyard(pcbnew.B_CrtYd if bottom else pcbnew.F_CrtYd))
        if fp.GetReference() in NO_BOX:
            crt = []
        parts.append(dict(ref=fp.GetReference(), bottom=bottom, pads=pads, crt=crt, pkg=pkg(fp)))
    # the view covers the board, every drawn courtyard and every pad
    pts = [pt for p in parts for ol in p['crt'] for pt in ol] + [pt for p in parts for q in p['pads'] for ol in q[1] for pt in ol]
    view = (min([box[0]] + [x for x, _ in pts]) - 0.5, min([box[1]] + [y for _, y in pts]) - 0.5,
            max([box[2]] + [x for x, _ in pts]) + 0.5, max([box[3]] + [y for _, y in pts]) + 0.5)
    return box, view, parts


def label(p, col, val, tx, out):
    """Ref, value and package centred inside the courtyard; rotated when the box is tall and narrow."""
    pts = [tx(*pt) for ol in p['crt'] for pt in ol]
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    lines = [(p['ref'], 13, col, 'bold'), (val, 17, '#000', 'bold'), (p['pkg'], 10, '#444', 'normal')]

    def fit(width):  # shrink fonts until the widest line fits (bold Helvetica ~0.66 em per char)
        return min(1.0, (width - 6) / max(0.66 * fs * len(t) for t, fs, _, _ in lines))

    rot = h > w and fit(h) > fit(w)
    k = fit(h if rot else w)
    sizes = [fs * k for _, fs, _, _ in lines]
    tw = max(0.66 * fs * len(t) for (t, _, _, _), fs in zip(lines, sizes)) + 6
    th = sum(sizes) * 1.15 + 4
    out.append('<g transform="translate(%.1f,%.1f)%s">' % (cx, cy, ' rotate(-90)' if rot else ''))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" fill="#fff" fill-opacity="0.88" stroke="%s" '
               'stroke-width="1"/>' % (-tw / 2, -th / 2, tw, th, col))
    y = -th / 2 + 2
    for (t, _, c, wgt), fs in zip(lines, sizes):
        y += fs * 1.15
        out.append('<text x="0" y="%.1f" font-size="%.1f" font-weight="%s" fill="%s" text-anchor="middle">%s</text>'
                   % (y - fs * 0.22, fs, wgt, c, escape(t)))
    out.append('</g>')


def render_view(parts, box, view, mirror, ox, oy, values, out):
    """Draw one board side at offset (ox, oy) with the values inside each footprint box."""
    x0, y0, x1, y1 = box
    vx0, vy0, vx1, vy1 = view

    def tx(x, y):
        if mirror:
            x = vx0 + vx1 - x
        return ox + (x - vx0) * S, oy + (y - vy0) * S

    def path(pts):
        return 'M' + ' L'.join('%.1f,%.1f' % tx(*p) for p in pts) + ' Z'

    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#2f6b3a" stroke="#1d4425" stroke-width="2" rx="6"/>'
               % (min(tx(x0, y0)[0], tx(x1, y0)[0]), tx(x0, y0)[1], (x1 - x0) * S, (y1 - y0) * S))

    side = [p for p in parts if p['bottom'] == mirror]
    for p in side:
        col = COL_VARIANT if p['ref'] in values else COL_COMMON
        for ol in p['crt']:
            out.append('<path d="%s" fill="%s" fill-opacity="0.25" stroke="%s" stroke-width="2"/>' % (path(ol), col, col))
        for num, polys, ppos in p['pads']:
            for ol in polys:
                out.append('<path d="%s" fill="#d4a63a" stroke="#8a6a1c" stroke-width="0.8"/>' % path(ol))
    for p in side:  # second pass so text sits above every pad
        for num, polys, ppos in p['pads']:
            cx, cy = tx(*ppos)
            if num == '1' and p['ref'] in ('U2', 'J1', 'C2'):
                out.append('<circle cx="%.1f" cy="%.1f" r="10" fill="#fff" stroke="#000" stroke-width="1.5"/>' % (cx, cy))
                out.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="bold" text-anchor="middle">%s</text>'
                           % (cx, cy + 5, '+' if p['ref'] == 'C2' else '1'))
            if p['ref'] == 'J1':
                out.append('<text x="%.1f" y="%.1f" font-size="13" font-weight="bold" fill="#000" text-anchor="middle">'
                           '%s</text>' % (cx, cy - 22, {'1': 'Vout', '2': 'GND', '3': 'Vin'}[num]))
        col = COL_VARIANT if p['ref'] in values else COL_COMMON
        if p['crt']:
            label(p, col, values.get(p['ref'], SHORT_VALUE.get(p['ref'], '?')), tx, out)
    return (vx1 - vx0) * S, (vy1 - vy0) * S


def render(variant, box, view, parts):
    v = VARIANTS[variant]
    out = []
    oy = 70
    w1, h = render_view(parts, box, view, False, 10, oy + 20, v['values'], out)
    w2, _ = render_view(parts, box, view, True, 10 + w1 + 60, oy + 20, v['values'], out)
    W, H = max(20 + w1 + 60 + w2, 980), oy + h + 70
    head = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'font-family="Helvetica, Arial, sans-serif">' % (W, H, W, H),
            '<rect width="100%" height="100%" fill="#fff"/>',
            '<text x="12" y="30" font-size="22" font-weight="bold">buck100 PSU (LM5163) – %s</text>' % escape(str(v['title'])),
            '<text x="12" y="54" font-size="13" fill="#333"><tspan fill="%s" font-weight="bold">■ orange</tspan> = '
            'value differs per variant   <tspan fill="%s" font-weight="bold">■ blue</tspan> = same on both variants   '
            '“1” = pin 1, “+” = elko plus pad</text>' % (COL_VARIANT, COL_COMMON),
            '<text x="%d" y="%d" font-size="16" font-weight="bold">TOP side</text>' % (10, oy + 10),
            '<text x="%d" y="%d" font-size="16" font-weight="bold">BOTTOM, seen from below: L1, C2</text>'
            % (10 + w1 + 60, oy + 10)]
    foot = ['<text x="12" y="%d" font-size="12" fill="#555">Generated by assembly/gen_assembly_diagram.py from '
            'buck100.kicad_pcb + README value table. The schematic values of R1/R2/R5/L1 are not the build values.</text>'
            % (H - 18), '</svg>']
    path = os.path.join(HERE, 'buck100-%s.svg' % variant)
    with open(path, 'w') as f:
        f.write('\n'.join(head + out + foot))
    print('wrote', path)


if __name__ == '__main__':
    box, view, parts = load()
    for k in VARIANTS:
        render(k, box, view, parts)
