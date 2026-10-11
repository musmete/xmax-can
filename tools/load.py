# .bin oturumlarını npz'ye çevirir: her ID için (t_ms_esp, 8 bayt), JSON için t + alanlar
import struct, json, glob, sys, os, numpy as np
out = sys.argv[1] if len(sys.argv) > 1 else '.'
for src in sorted(glob.glob(os.path.join(out, 'can_*.bin'))):
    b = open(src, 'rb').read()
    if not b: continue
    i = 0; fr = {}; js = []; jb = b''; last = None
    while i + 11 <= len(b):
        typ, n = b[i], struct.unpack_from('<H', b, i + 1)[0]; pt = struct.unpack_from('<Q', b, i + 3)[0]
        p = b[i + 11:i + 11 + n]; i += 11 + n
        if typ == 82 and n >= 4:
            for k in range((n - 4) // 14):
                ms, idd = struct.unpack_from('<IH', p, 4 + 14 * k)
                fr.setdefault(idd & 0x7FF, []).append((ms, p[4 + 14 * k + 6:4 + 14 * k + 14]))
                last = (pt, ms)
        elif typ == 74:
            jb += p
            while b'\n' in jb:
                l, jb = jb.split(b'\n', 1)
                try: j = json.loads(l)
                except Exception: continue
                if last: js.append((last[1] + (pt - last[0]), j))
    d = {}
    for idd, L in fr.items():
        d[f't_{idd:03X}'] = np.array([x[0] for x in L], np.int64)
        d[f'd_{idd:03X}'] = np.frombuffer(b''.join(x[1] for x in L), np.uint8).reshape(-1, 8)
    keys = sorted({k for _, j in js for k, v in j.items() if isinstance(v, (int, float, bool))})
    d['j_t'] = np.array([t for t, _ in js], np.int64)
    for k in keys: d['j_' + k] = np.array([float(j.get(k, np.nan)) if j.get(k) is not None else np.nan for _, j in js])
    name = os.path.basename(src)[4:-4]
    np.savez_compressed(os.path.join(out, name + '.npz'), **d); print(name, len(js), len(fr))
