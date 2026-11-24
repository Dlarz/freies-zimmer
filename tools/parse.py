import pdfplumber, sys, re, json, collections
pdf = pdfplumber.open(sys.argv[1])
ROOM = re.compile(r'^(\d{3}|[UNEZ]\d{2,3}|TS\d|TE\d|THO|THU)$')
FN = re.compile(r'^(\d+)\)$')
LABEL = re.compile(r'^(Mo|Di|Mi|Do|Fr)-(\d+)$')

# ---- footnotes (pages 12-13) ----
footnotes = collections.defaultdict(list)  # n -> list of (teacher, subj, rooms, classes)
for pi in (11, 12):
    p = pdf.pages[pi]
    ws = [w for w in p.extract_words() if w['top'] > 52]
    for (xa, xk, xz) in ((25, 160, 249), (301, 437, 526)):
        lines = collections.defaultdict(list)
        for w in ws:
            if xa - 1 <= w['x0'] < xz - 1:
                lines[round(w['top'])].append(w)
        cur = None
        for top in sorted(lines):
            lw = sorted(lines[top], key=lambda w: w['x0'])
            toks = [w for w in lw if w['x0'] < xk - 1]
            cls = [w['text'].rstrip(',') for w in lw if w['x0'] >= xk - 1]
            if toks and FN.match(toks[0]['text']):
                cur = int(FN.match(toks[0]['text']).group(1)); toks = toks[1:]
            parts = [t['text'].rstrip(',') for t in toks]
            if not parts: continue
            rooms = [x for x in parts if ROOM.match(x)]
            footnotes[cur].append({'t': parts, 'rooms': rooms, 'cls': cls})

# ---- grid pages ----
entries = []  # dict(cls, day, period, subj, teacher, rooms, flags, fn)
problems = []
for pi in range(0, 11):
    p = pdf.pages[pi]
    ws = p.extract_words(x_tolerance=1.2)
    # row labels
    rows = {}
    for w in ws:
        m = LABEL.match(w['text'])
        if m and w['x0'] < 90:
            rows[w['text']] = (w['top'] + w['bottom']) / 2
    # headers
    heads = sorted([w for w in ws if 55 < w['top'] < 70 and w['x0'] > 90], key=lambda w: w['x0'])
    cols = []
    for i, h in enumerate(heads):
        x0 = h['x0'] - 1
        x1 = heads[i + 1]['x0'] - 1 if i + 1 < len(heads) else x0 + 94
        cols.append((h['text'], x0, x1))
    # blocks
    seen = set(); blocks = []
    for r in p.rects:
        if r['x1'] - r['x0'] > 80 and r['top'] > 74 and r['x0'] > 90:
            c = tuple(round(v, 2) for v in (r.get('non_stroking_color') or (1, 1, 1)))
            if c == (1.0, 1.0, 1.0): continue
            k = (round(r['x0']), round(r['top']), round(r['x1']), round(r['bottom']))
            if k in seen: continue
            seen.add(k); blocks.append((r, c))
    used = set()
    for r, c in blocks:
        col = [cname for cname, x0, x1 in cols if x0 <= r['x0'] < x1]
        if not col: problems.append(('nocol', pi, r['x0'])); continue
        cname = col[0]
        periods = [lab for lab, y in rows.items() if r['top'] < y < r['bottom']]
        inside = [w for w in ws if r['x0'] - 0.5 <= w['x0'] < r['x1'] - 1 and w['x1'] <= r['x1'] + 12 and r['top'] - 0.5 <= w['top'] and w['bottom'] <= r['bottom'] + 0.5]
        for w in inside: used.add(id(w))
        fn = [int(FN.match(w['text']).group(1)) for w in inside if FN.match(w['text'])]
        lines = collections.defaultdict(list)
        for w in inside:
            if FN.match(w['text']): continue
            lines[round(w['top'])].append(w)
        for top in sorted(lines):
            lw = sorted(lines[top], key=lambda w: w['x0'])
            bx = r['x0']
            subj = [w['text'] for w in lw if w['x0'] < bx + 20]
            teach = [w['text'] for w in lw if bx + 20 <= w['x0'] < bx + 44]
            rest = [w['text'] for w in lw if w['x0'] >= bx + 44]
            rooms = [x for x in rest if ROOM.match(x)]
            flags = [x for x in rest if not ROOM.match(x)]
            for d in periods:
                day, per = d.split('-')
                entries.append(dict(cls=cname, day=day, p=int(per), subj=' '.join(subj), t=' '.join(teach), rooms=rooms, flags=flags, fn=fn, color=c))
        if not periods: problems.append(('noper', pi, cname, r['top']))
    # words not in any block (excluding header/labels)
    for w in ws:
        if id(w) in used or w['top'] < 74 or w['x0'] < 90: continue
        problems.append(('orphan', pi, w['text'], round(w['x0']), round(w['top'])))

json.dump({'entries': entries, 'footnotes': footnotes}, open('raw.json', 'w'), indent=0)
print(len(entries), 'entries;', len(footnotes), 'footnotes')
for pr in problems: print(pr)
