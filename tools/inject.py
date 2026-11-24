import sys, json
tpl, data, out = sys.argv[1:4]
rooms = json.load(open(data))
s = open(tpl, encoding='utf-8').read().replace('/*DATA*/[]' if '/*DATA*/[]' in open(tpl, encoding='utf-8').read() else '/*DATA*/{}', json.dumps(rooms, ensure_ascii=False, separators=(',', ':')))
open(out, 'w', encoding='utf-8').write(s)
print('wrote', out, len(s), 'bytes')
