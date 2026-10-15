#!/usr/bin/env python3
"""Build the interactive theory-of-change figure in an IMA index.html.

The model figure in every IMA is the client's completed theory of change (ToC): a
16:9 Google Slides slide made with the toc-synthesizer house style. This script puts
that slide into index.html as an inline vector drawing and lays clickable regions and
the measurement overlay (priority badges, connector lines, dim layers) on top of it.

Two steps:

  1. regions  — read the slide's geometry and write a starting spec.
       python3 toc_figure.py regions slide.json > figure.json

     slide.json is a Slides `read_presentation` result (any of: the raw tool-results
     file, {"content": {...}}, or the presentation object) read with the field mask
       pageSize, slides.pageElements(objectId,size,transform,
         shape(shapeType,shapeProperties(shapeBackgroundFill,outline(dashStyle)),
         text(textElements(textRun(content)))))
     It finds the context band, one region per column (header pill down to the last
     box in that column) and each box in the lower band, and names them context,
     col1..colN, band1..bandN. Edit the ids to match the `nodes` keys you write,
     drop regions that should not be clickable (e.g. a "Where data come from" note),
     and fill in the priorities.

  2. build    — splice the figure into index.html.
       python3 toc_figure.py build index.html --pdf toc.pdf --spec figure.json

     toc.pdf is the slide exported from Drive (download_file_content,
     exportMimeType application/pdf). The script converts it to SVG with pdftocairo
     (poppler-utils), inlines it (no base64: that adds a third to the file size),
     prefixes its ids so they cannot collide with the page, and replaces the whole
     <svg id="model-svg"> element. It then checks that every region id is a key in
     `const nodes`, every node key is a region, and every priority id is a key in
     `const priorityData` whose `nodes` list only names regions.

Spec format (coordinates in slide points, 960 x 540 for a 16:9 slide):

  {
    "regions": [
      {"id": "context", "label": "Context", "box": [28.8, 90.0, 902.2, 30.2]},
      {"id": "teachers", "label": "Lando teachers deliver", "box": [28.8, 129.6, 163.2, 220.3]}
    ],
    "priorities": [
      {"id": "1", "label": "P1", "color": "#1a6fff", "nodes": ["students", "context"]}
    ]
  }

Badges sit in a strip to the right of the slide, one per priority, labelled with
`label` (use P1, P2... so they do not clash with the ToC's own numbered question
markers). Colours come from the closed set #1a6fff, #059669, #d97706, #718096.
"""
import argparse
import html as _html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

EMU_PER_PT = 12700
ALLOWED_COLORS = {'#1a6fff', '#059669', '#d97706', '#718096'}
GUTTER = 30          # px added to the right of the slide for the badge strip
BADGE_STEP = 40


# ───────────────────────────────────────────────────────────── regions
def _load_presentation(path):
    d = json.load(open(path, encoding='utf-8'))
    if isinstance(d, dict) and 'content' in d and isinstance(d['content'], dict):
        d = d['content']
    if isinstance(d, list):          # raw MCP tool-results wrapper
        d = json.loads(d[0]['text'])
        d = d.get('content', d)
    return d


def _elements(pres):
    out = []
    for el in pres['slides'][0].get('pageElements', []):
        t, s = el.get('transform', {}), el.get('size', {})
        w = s.get('width', {}).get('magnitude', 0) * t.get('scaleX', 1) / EMU_PER_PT
        h = s.get('height', {}).get('magnitude', 0) * t.get('scaleY', 1) / EMU_PER_PT
        x = t.get('translateX', 0) / EMU_PER_PT
        y = t.get('translateY', 0) / EMU_PER_PT
        sh = el.get('shape', {})
        sp = sh.get('shapeProperties', {})
        rgb = sp.get('shapeBackgroundFill', {}).get('solidFill', {}).get('color', {}).get('rgbColor', {})
        lum = 0.2126 * rgb.get('red', 0) + 0.7152 * rgb.get('green', 0) + 0.0722 * rgb.get('blue', 0) if rgb else 1.0
        txt = ''.join(te.get('textRun', {}).get('content', '') for te in sh.get('text', {}).get('textElements', []))
        out.append(dict(type=sh.get('shapeType'), x=x, y=y, w=w, h=h, lum=lum, text=txt.strip()))
    return out


def _text_in(els, box):
    x, y, w, h = box
    for e in els:
        if e['type'] == 'TEXT_BOX' and e['text'] and abs(e['y'] - y) < 2 and x - 2 <= e['x'] <= x + w:
            return e['text']
    return ''


def cmd_regions(args):
    els = _elements(_load_presentation(args.slide))
    rr = [e for e in els if e['type'] == 'ROUND_RECTANGLE']
    oq = [e['y'] for e in els if e['text'].lower().startswith('open questions')]
    bottom_limit = min(oq) if oq else 540
    pills = sorted([e for e in rr if e['h'] < 36 and e['lum'] < 0.55 and e['w'] < 400], key=lambda e: e['x'])
    if not pills:
        sys.exit('No column header pills found. Is this a toc-synthesizer slide?')
    head_y = min(p['y'] for p in pills)
    regions = []
    ctx = [e for e in rr if e['y'] < head_y and e['w'] > 400]
    for c in ctx:
        regions.append(dict(id='context', label=_text_in(els, (c['x'], c['y'], c['w'], c['h'])).split('·')[0].strip() or 'Context',
                            box=[round(c['x'], 1), round(c['y'], 1), round(c['w'], 1), round(c['h'], 1)]))
    body = [e for e in rr if e not in pills and e not in ctx and e['y'] > head_y and e['y'] < bottom_limit]
    col_bottom = 0
    for n, p in enumerate(pills, 1):
        inside = [e for e in body if e['x'] >= p['x'] - 2 and e['x'] + e['w'] <= p['x'] + p['w'] + 2]
        b = max((e['y'] + e['h'] for e in inside), default=p['y'] + p['h'])
        col_bottom = max(col_bottom, b)
        regions.append(dict(id=f'col{n}', label=_text_in(els, (p['x'], p['y'], p['w'], p['h'])),
                            box=[round(p['x'], 1), round(p['y'], 1), round(p['w'], 1), round(b - p['y'], 1)]))
    band = sorted([e for e in body if e['y'] > col_bottom - 1], key=lambda e: e['x'])
    for n, e in enumerate(band, 1):
        lead = _text_in(els, (e['x'], e['y'], e['w'], e['h'])).split(':')[0].strip()
        regions.append(dict(id=f'band{n}', label=lead, box=[round(e['x'], 1), round(e['y'], 1), round(e['w'], 1), round(e['h'], 1)]))
    spec = dict(regions=regions, priorities=[
        dict(id='1', label='P1', color='#1a6fff', nodes=['[region ids]'])])
    json.dump(spec, sys.stdout, indent=2, ensure_ascii=False)
    print()


# ───────────────────────────────────────────────────────────── build
def _slide_svg(pdf):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'toc.svg'
        subprocess.run(['pdftocairo', '-svg', '-f', '1', '-l', '1', str(pdf), str(out)], check=True)
        svg = out.read_text(encoding='utf-8')
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)(?:pt)?"[^>]*\bheight="([\d.]+)(?:pt)?"', svg)
    W, H = float(m.group(1)), float(m.group(2))
    # Collapse whitespace between tags only. Do NOT round path coordinates: it broke the render.
    svg = re.sub(r'>\s+<', '><', svg)
    svg = re.sub(r'^<\?xml[^>]*\?>', '', svg).strip()
    svg = svg.replace('id="', 'id="toc-')
    svg = re.sub(r'(xlink:href|href)="#', r'\1="#toc-', svg)
    svg = svg.replace('url(#', 'url(#toc-')
    svg = re.sub(r'^<svg [^>]*>', f'<svg x="0" y="0" width="{W:g}" height="{H:g}" viewBox="0 0 {W:g} {H:g}" pointer-events="none">', svg, count=1)
    return svg, W, H


def _js_keys(html, const):
    m = re.search(r'const ' + const + r'\s*=\s*\{', html)
    if not m:
        return None
    i, depth, keys = m.end(), 1, []
    tok = re.compile(r"""\s*(?:'([^']+)'|"([^"]+)"|([A-Za-z_$][\w$-]*))\s*:""")
    while depth and i < len(html):
        c = html[i]
        if depth == 1:
            k = tok.match(html, i)
            if k and html[i - 1] in '{,\n ':
                keys.append(next(g for g in k.groups() if g))
                i = k.end()
                continue
        if html.startswith('//', i):
            i = html.find('\n', i)
            continue
        if html.startswith('/*', i):
            i = html.find('*/', i) + 2
            continue
        if c in '`\'"':
            j = i + 1
            while j < len(html) and html[j] != c:
                j += 2 if html[j] == '\\' else 1
            i = j + 1
            continue
        depth += c == '{'
        depth -= c == '}'
        i += 1
    return keys


def cmd_build(args):
    spec = json.load(open(args.spec, encoding='utf-8'))
    html = Path(args.html).read_text(encoding='utf-8')
    regions, pris = spec['regions'], spec['priorities']
    ids = [r['id'] for r in regions]
    problems = []
    if len(set(ids)) != len(ids):
        problems.append('duplicate region ids')
    for p in pris:
        if p['color'].lower() not in ALLOWED_COLORS:
            problems.append(f"priority {p['id']}: colour {p['color']} is outside the closed set {sorted(ALLOWED_COLORS)}")
        for n in p['nodes']:
            if n not in ids:
                problems.append(f"priority {p['id']}: node '{n}' is not a region id")
    node_keys = _js_keys(html, 'nodes')
    if node_keys is not None:
        for i in ids:
            if i not in node_keys:
                problems.append(f"region '{i}' has no entry in const nodes")
        for k in node_keys:
            if k not in ids:
                problems.append(f"const nodes has '{k}', which is not a region")
    pd_keys = _js_keys(html, 'priorityData')
    if pd_keys is not None:
        for p in pris:
            if p['id'] not in pd_keys:
                problems.append(f"priority '{p['id']}' has no entry in const priorityData")
        for k in pd_keys:
            if k not in [p['id'] for p in pris]:
                problems.append(f"const priorityData has '{k}', which is not in the spec")
    if problems and not args.force:
        sys.exit('Not built:\n  ' + '\n  '.join(problems) + '\n(--force builds anyway.)')

    svg, W, H = _slide_svg(args.pdf)
    VW, VH = W + GUTTER, H
    box = {r['id']: r['box'] for r in regions}

    def ctr(n):
        x, y, w, h = box[n]
        return round(x + w / 2, 1), round(y + h / 2, 1)

    over = ''.join(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="transparent" style="cursor:pointer" '
                   f'onclick="show(\'{r["id"]}\')" rx="4"><title>{_html.escape(r.get("label", ""))}</title></rect>\n'
                   for r in regions for x, y, w, h in [r['box']])
    dims = ''.join(f'    <rect class="dim-overlay" data-node="{r["id"]}" x="{x}" y="{y}" width="{w}" height="{h}" rx="4" '
                   f'fill="rgba(255,255,255,0.7)" style="pointer-events:none;opacity:0;transition:opacity 0.2s"/>\n'
                   for r in regions for x, y, w, h in [r['box']])
    bx = W + GUTTER / 2 + 1
    top = H / 2 - (len(pris) - 1) * BADGE_STEP / 2 - 20
    conns = badges = ''
    for k, p in enumerate(pris):
        by = round(top + k * BADGE_STEP, 1)
        for n in p['nodes']:
            if n not in box:
                continue
            tx, ty = ctr(n)
            conns += (f'    <line class="connector-line" data-priority="{p["id"]}" x1="{bx}" y1="{by}" x2="{tx}" y2="{ty}" '
                      f'stroke="{p["color"]}" stroke-width="1.5" stroke-dasharray="4 3" opacity="0" '
                      f'style="pointer-events:none;transition:opacity 0.2s"/>\n')
        badges += (f'    <g class="priority-badge-group" data-priority="{p["id"]}" onclick="openPriorityCard(\'{p["id"]}\')" style="cursor:pointer">\n'
                   f'      <circle cx="{bx}" cy="{by}" r="13" fill="{p["color"]}" stroke="white" stroke-width="2.5" filter="url(#badge-shadow)"/>\n'
                   f'      <text x="{bx}" y="{by}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="9.5" '
                   f'font-weight="700" fill="white">{p.get("label", p["id"])}</text>\n    </g>\n')

    new = (f'<svg id="model-svg" viewBox="0 0 {VW:g} {VH:g}" xmlns="http://www.w3.org/2000/svg" '
           f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{VW:g}" height="{VH:g}">\n'
           '  <defs>\n    <filter id="badge-shadow" x="-30%" y="-30%" width="160%" height="160%">\n'
           '      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.3)"/>\n    </filter>\n  </defs>\n'
           f'  <rect width="{VW:g}" height="{VH:g}" fill="white"/>\n'
           '  <!-- THEORY-OF-CHANGE FIGURE: generated by toc_figure.py from the client\'s ToC slide. Do not hand-edit; re-run the script. -->\n'
           '  ' + svg + '\n'
           '  <!-- ── CLICKABLE REGIONS (one per Model Description row) ── -->\n' + over +
           '  <!-- ══ MEASUREMENT OVERLAY (toggleable via the checkbox above) ══ -->\n  <g id="meas-layer">\n'
           + dims + conns + badges + '  </g>\n</svg>')
    i = html.index('<svg id="model-svg"')
    j = html.index('</svg>', i)
    # The placeholder/previous figure may contain nested <svg> elements: find the matching close.
    depth, k = 0, i
    for m in re.finditer(r'<svg\b|</svg>', html[i:]):
        depth += 1 if m.group(0) == '<svg' else -1
        if depth == 0:
            j = i + m.end()
            break
    html = html[:i] + new + html[j:]
    Path(args.out or args.html).write_text(html, encoding='utf-8')
    print(f'Figure built: {len(regions)} regions, {len(pris)} priorities, '
          f'{len(new.encode()) // 1024} KB figure, {len(html.encode()) // 1024} KB page'
          + (' (with --force; fix: ' + '; '.join(problems) + ')' if problems else ''))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('regions', help='write a starting spec from the slide geometry')
    r.add_argument('slide')
    r.set_defaults(fn=cmd_regions)
    b = sub.add_parser('build', help='splice the figure into index.html')
    b.add_argument('html')
    b.add_argument('--pdf', required=True)
    b.add_argument('--spec', required=True)
    b.add_argument('--out')
    b.add_argument('--force', action='store_true')
    b.set_defaults(fn=cmd_build)
    a = ap.parse_args()
    a.fn(a)


if __name__ == '__main__':
    main()
