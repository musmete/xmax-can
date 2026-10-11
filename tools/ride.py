import numpy as np, glob, datetime
tot_km=0; allx=[]
for fn in sorted(glob.glob('*.npz')):
    f=np.load(fn)
    t=f['t_758']/1000.; d=f['d_758'].astype(int)
    v=(d[:,0]|d[:,1]<<8)/10.; v2=(d[:,2]|d[:,3]<<8)/10.
    tr=f['t_750']/1000.; r=((f['d_750'][:,0].astype(int)|f['d_750'][:,1].astype(int)<<8)&0x1FFF)
    dt=np.diff(t,prepend=t[0]); dt[dt>1]=0
    km=(v*dt).sum()/3600; tot_km+=km
    # ivme: 0.5 sn pencere
    k=10; a=(v[k:]-v[:-k])/3.6/(t[k:]-t[:-k])
    vm=v[k:]
    ess=[];last=-99
    for i in np.where((a<-6)&(vm>40))[0]:
        if t[i]-last>5: ess.append((round(t[i]-t[0]),round(vm[i]),round(a[i],1))); last=t[i]
    mv=v>5
    print(f"{fn[:15]} {km:5.2f} km  hareket {mv.sum()*0.05/60:4.1f} dk  max {v.max():.0f}  max ivme +{a.max():.1f} / {a.min():.1f} m/s2  ESS(>40,<-6) {len(ess)} {ess[:4]}")
    # ikinci hız alani
    m=v>10
    if m.sum()>50: print(f"    v2/v ort {np.mean(v2[m]/v[m]):.3f} std {np.std(v2[m]/v[m]):.3f}   corr {np.corrcoef(v[m],v2[m])[0,1]:.3f}")
    # devir/hız (CVT)
    ri=np.interp(t,tr,r)
    for lo,hi in ((10,30),(30,50),(50,70),(70,95)):
        s=(v>=lo)&(v<hi)
        if s.sum()>40: allx.append((lo,hi,np.median(ri[s]),s.sum()))
print('toplam km',round(tot_km,2))
import collections
g=collections.defaultdict(list)
for lo,hi,rr,n in allx: g[(lo,hi)].append(rr)
for k,vv in sorted(g.items()): print('hiz',k,'medyan devir',int(np.median(vv)))
