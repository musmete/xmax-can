import numpy as np, glob
S = ['rpm','speed','throttle','coolant','iat','map','load','bat','inj','adv','o2','stft','baro']
F = [np.load(f) for f in sorted(glob.glob('*.npz'))]
ids = sorted({k[2:] for f in F for k in f.files if k.startswith('d_')} - {'7E8'})
J = {s: np.concatenate([f['j_'+s] for f in F]) for s in S}
out=[]
for idd in ids:
    rows=[]
    for f in F:
        t,d,jt=f['t_'+idd],f['d_'+idd],f['j_t']; k=np.searchsorted(t,jt,'right')-1; k[k<0]=0; rows.append(d[k])
    D=np.concatenate(rows).astype(np.int64)
    cands={}
    for st in range(7):
        w=D[:,st]|(D[:,st+1]<<8)
        for sh in (0,4):
            for wd in range(6,17-sh):
                cands[f'w{st} >>{sh} &{wd}b']=(w>>sh)&((1<<wd)-1)
    for st in range(8):
        cands[f'b{st}']=D[:,st]; cands[f'b{st}hi']=D[:,st]>>4; cands[f'b{st}lo']=D[:,st]&15
    for sig in S:
        y=J[sig]; m=(y>-1)&~np.isnan(y)
        if sig in('rpm',): m&=y>0
        bb=(0,None)
        for n,v in cands.items():
            v=v[m].astype(float)
            if v.std()==0: continue
            r=np.corrcoef(v,y[m])[0,1]
            if abs(r)>abs(bb[0]): bb=(r,n)
        if abs(bb[0])>0.85: out.append((sig,abs(bb[0]),idd,bb[1],bb[0]))
for sig in S:
    L=sorted([o for o in out if o[0]==sig],key=lambda x:-x[1])[:3]
    for o in L: print(f"{sig:8s} 0x{o[2]} {o[3]:16s} r={o[4]:+.4f}")
