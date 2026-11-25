# Builds the compact data for the simple app: free/busy per candidate room + where each class is.
import json, re, collections
raw = json.load(open('raw.json')); ru = json.load(open('ru.json'))
occ = ru['occ']
DAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr']
SLOTS = [f'{d}-{p}' for d in DAYS for p in range(1, 12)]
EXCLUDE = {'017', '221', '213'}  # Sitzungszimmer, Beratungszimmer, never-booked 213
cand = [r for r in ru['order'] if re.fullmatch(r'[0-2]\d\d', r) and r not in EXCLUDE]
busy = {r: ''.join('1' if s in occ[r] else '0' for s in SLOTS) for r in cand}
# class locations
by = collections.defaultdict(lambda: collections.defaultdict(list))
for e in raw['entries']:
    by[e['cls']][f"{e['day']}-{e['p']}"].append(e)
def resolve(room, cls, slot):
    if room in occ: return room
    for r in occ:  # truncated like Z20 -> Z204/Z206/Z207
        if r.startswith(room) and occ[r].get(slot, '').replace(' ', '').startswith(cls): return r
    return room
# elective groups (Schwerpunktfach / Ergaenzungsfach / Wahlfach): footnotes shared by a whole year group like G23X
F = raw['footnotes']
def kind_of(subjs):
    if all(len(x) == 3 and x[0] == 'S' for x in subjs): return 'SF'
    if all(len(x) == 3 and x[0] == 'E' for x in subjs): return 'EF'
    return 'WF'
choice = {}
for k, v in F.items():
    xs = {c for x in v for c in x['cls'] if c.endswith('X')}
    subjs = [x['t'][1] for x in v]
    if xs and len(set(subjs)) >= 2:
        choice[k] = {'x': sorted(xs)[0], 'k': kind_of(subjs), 'v': v}
xg = {}   # x-group -> kind -> subject -> {teacher: index}
for k, c in choice.items():
    for x in c['v']:
        g = xg.setdefault(c['x'], {}).setdefault(c['k'], {}).setdefault(x['t'][1], {})
        g.setdefault(x['t'][0], len(g))
fnout = {}
rooms_of = collections.defaultdict(collections.Counter)  # (x, kind, subj, gid) -> room counts
for k, c in choice.items():
    o = []
    for x in c['v']:
        subj, gid = x['t'][1], xg[c['x']][c['k']][x['t'][1]][x['t'][0]]
        o.append([subj, gid, x['rooms']])
        for r in x['rooms']: rooms_of[(c['x'], c['k'], subj, gid)][r] += 1
    fnout[k] = {'x': c['x'], 'k': c['k'], 'o': o}
xout = {}
for x, kinds in xg.items():
    for kd, subjs in kinds.items():
        for subj, groups in subjs.items():
            # ask for the group only if at some slot this subject meets in different rooms at once
            ask = any(len({tuple(r) for s2, g2, r in fo['o'] if s2 == subj}) > 1 for fo in fnout.values() if fo['x'] == x and fo['k'] == kd)
            labels = [' / '.join(r for r, _ in rooms_of[(x, kd, subj, gid)].most_common()) for gid in range(len(groups))]
            xout.setdefault(x, {}).setdefault(kd, {})[subj] = {'ask': ask, 'g': labels}

classes = {}
for cls, slots in by.items():
    arr = []; homes = collections.Counter()
    for s in SLOTS:
        es = slots.get(s, [])
        rooms = [r for e in es for r in e['rooms']]
        if not es: arr.append(''); continue
        fx = [str(f) for e in es for f in e['fn'] if str(f) in choice]
        if fx: arr.append('#' + fx[0]); continue
        if es[0]['subj'] == 'K' and rooms: homes[rooms[0]] += 1
        num = [r for r in rooms if re.fullmatch(r'\d{3}', r)]
        shown = resolve(rooms[0], cls, s) if rooms else ''
        arr.append(f"{shown}|{num[0] if num else ''}|{es[0]['subj']}")  # no teacher codes in public data
    classes[cls] = {'h': homes.most_common(1)[0][0] if homes else '', 's': arr}
data = {'busy': busy, 'cls': classes, 'fn': fnout, 'x': xout}
json.dump(data, open('simple.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(cand), 'rooms:', cand)
print(len(classes), 'classes; G23v home', classes['G23v']['h'])
print([x for x in classes['G23v']['s']][:22])
print('Z resolve:', classes['G23v']['s'][SLOTS.index('Do-9')])
print(json.dumps(xout, ensure_ascii=False, indent=1))
print('no home:', [c for c, v in classes.items() if not v['h']])
