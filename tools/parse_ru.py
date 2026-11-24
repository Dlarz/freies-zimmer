import pdfplumber, sys, re, json, collections
LABEL = re.compile(r'^(Mo|Di|Mi|Do|Fr)-(\d+)$')
ru = pdfplumber.open(sys.argv[1]); re_ = pdfplumber.open(sys.argv[2])
occ = {}   # room -> {slot: text}
order = []
colors = collections.Counter()
for pi, p in enumerate(ru.pages):
    ws = p.extract_words(x_tolerance=1.2)
    rows = {}
    for w in ws:
        if LABEL.match(w['text']) and w['x0'] < 90:
            rows[w['text']] = (w['top'], w['bottom'])
    labs = sorted(rows.items(), key=lambda kv: kv[1][0])
    # row bands: midpoint between label centers
    centers = [(k, (a + b) / 2) for k, (a, b) in labs]
    bands = []
    for i, (k, c) in enumerate(centers):
        lo = (centers[i-1][1] + c) / 2 if i else c - 6.5
        hi = (centers[i+1][1] + c) / 2 if i + 1 < len(centers) else c + 6.5
        bands.append((k, lo, hi))
    heads = sorted([w for w in ws if 55 < w['top'] < 70 and w['x0'] > 90], key=lambda w: w['x0'])
    cols = []
    for i, h in enumerate(heads):
        x0 = h['x0'] - 1.5
        x1 = heads[i+1]['x0'] - 1.5 if i + 1 < len(heads) else x0 + 82
        cols.append((h['text'], x0, x1)); occ.setdefault(h['text'], {}); order.append(h['text'])
    for w in ws:
        if w['top'] < 72 or w['x0'] < 90: continue
        cy = (w['top'] + w['bottom']) / 2
        b = [k for k, lo, hi in bands if lo <= cy < hi]
        c = [n for n, x0, x1 in cols if x0 <= w['x0'] < x1]
        if not b or not c:
            print('orphan', pi, w['text'], w['x0'], w['top']); continue
        d = occ[c[0]]
        d[b[0]] = (d.get(b[0], '') + ' ' + w['text']).strip()
    for r in p.rects:
        if 70 < r['x1'] - r['x0'] < 90:
            colors[tuple(round(v, 2) for v in (r.get('non_stroking_color') or ()))] += 1
print('rooms', len(order), order)
print('colors', colors)
# room types from RE
types = {}
for p in re_.pages:
    for line in (p.extract_text() or '').split('\n'):
        m = re.match(r'^([A-ZÄÖÜ][A-ZÄÖÜ0-9 /.\-]+?) (\S+)$', line.strip())
        if m and m.group(2) in occ and m.group(1) not in ('CH-6210 SURSEE',):
            types[m.group(2)] = m.group(1)
print('types', len(types))
for r in order: print(r, types.get(r, '?'), len(occ[r]))
json.dump({'occ': occ, 'order': order, 'types': types}, open('ru.json', 'w'), ensure_ascii=False)
