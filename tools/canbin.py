"""moto_dash CanRawLog .bin -> metin + kayip raporu.
Kullanim: python canbin.py <can_*.bin> [cikti.txt]
Cikti satirlari cap_lossless/an.py ile ayni bicim: "[ms] ID=0x... STD DLC=8 DATA=.. #seq",
JSON satirlari "@<esp_ms_tahmini>" + JSON (telefon zamanindan ESP saatine esleme ile)."""
import struct, sys, collections
src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else None
b = open(src, 'rb').read()
i = 0; frames = []; jbuf = b''; jsons = []; pkts = 0; last_map = None
while i + 11 <= len(b):
    typ, n = b[i], struct.unpack_from('<H', b, i + 1)[0]; pt = struct.unpack_from('<Q', b, i + 3)[0]
    p = b[i + 11:i + 11 + n]; i += 11 + n
    if typ == ord('R') and n >= 4:
        pkts += 1
        seq = struct.unpack_from('<I', p, 0)[0]
        for k in range((n - 4) // 14):
            ms, idd = struct.unpack_from('<IH', p, 4 + 14 * k)
            frames.append((seq + k + 1, ms, idd & 0x7FF, (idd >> 11) & 0xF, p[4 + 14 * k + 6:4 + 14 * k + 14], pt))
            last_map = (pt, ms)
    elif typ == ord('J'):
        jbuf += p
        while b'\n' in jbuf:
            line, jbuf = jbuf.split(b'\n', 1)
            jsons.append((pt, last_map, line.decode(errors='replace')))
gaps = resets = 0
for a, c in zip(frames, frames[1:]):
    if c[0] <= a[0]: resets += 1
    elif c[0] > a[0] + 1: gaps += c[0] - a[0] - 1
tot = len(frames) + gaps
dur = (frames[-1][1] - frames[0][1]) / 1000 if frames else 0
print(f"paket {pkts}  kare {len(frames)}  KAYIP {gaps} (%{100*gaps/max(tot,1):.3f})  sira sifirlanmasi {resets}  sure {dur:.0f} s  JSON {len(jsons)}")
ids = collections.Counter(f[2] for f in frames); print("ID sayisi", len(ids))
if dst:
    with open(dst, 'w') as o:
        ji = 0
        for f in frames:
            while ji < len(jsons) and jsons[ji][0] <= f[5]:
                pt, mp, line = jsons[ji]
                if mp: o.write(f"@{mp[1] + (pt - mp[0])}\n")
                o.write(line + "\n"); ji += 1
            o.write(f"[{f[1]:8d}] ID=0x{f[2]:03X} STD DLC={f[3]} DATA={' '.join('%02X' % x for x in f[4][:f[3]])} #{f[0]}\n")
