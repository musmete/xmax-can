import numpy as np, glob, sys
F = [np.load(f) for f in sorted(glob.glob('*.npz'))]
def field(idd, order, s, w):
    rows=[]
    for f in F:
        t,d,jt=f['t_'+idd],f['d_'+idd],f['j_t']; k=np.searchsorted(t,jt,'right')-1; k[k<0]=0; rows.append(d[k])
    D=np.concatenate(rows).astype(np.int64)
    W=sum(D[:,i]<<(8*(i if order=='LE' else 7-i)) for i in range(8))
    return ((W>>s)&((1<<w)-1)).astype(float)
J=lambda s: np.concatenate([f['j_'+s] for f in F])
for spec in sys.argv[1:]:
    idd,o,s,w,sig=spec.split(':'); v=field(idd,o,int(s),int(w)); y=J(sig); m=~np.isnan(y)
    a,b=np.polyfit(v[m],y[m],1); res=y[m]-(a*v[m]+b)
    print(f"0x{idd} {o} bit{s} w{w} -> {sig}: {sig}= {a:.5f}*x {b:+.3f}  r={np.corrcoef(v[m],y[m])[0,1]:.3f} sapma(std)={res.std():.2f}  x aralik {v.min():.0f}-{v.max():.0f}  {sig} aralik {y[m].min():.1f}-{y[m].max():.1f}")
