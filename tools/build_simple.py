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
classes = {}
for cls, slots in by.items():
    arr = []; homes = collections.Counter()
    for s in SLOTS:
        es = slots.get(s, [])
        rooms = [r for e in es for r in e['rooms']]
        if not es: arr.append(''); continue
        if es[0]['subj'] == 'K' and rooms: homes[rooms[0]] += 1
        num = [r for r in rooms if re.fullmatch(r'\d{3}', r)]
        shown = resolve(rooms[0], cls, s) if rooms else ''
        arr.append(f"{shown}|{num[0] if num else ''}|{es[0]['subj']}")  # no teacher codes in public data
    classes[cls] = {'h': homes.most_common(1)[0][0] if homes else '', 's': arr}
data = {'busy': busy, 'cls': classes}
json.dump(data, open('simple.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(cand), 'rooms:', cand)
print(len(classes), 'classes; G23v home', classes['G23v']['h'])
print([x for x in classes['G23v']['s']][:22])
print('Z resolve:', classes['G23v']['s'][SLOTS.index('Do-9')])
print('no home:', [c for c, v in classes.items() if not v['h']])
