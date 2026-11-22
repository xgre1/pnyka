import numpy as np, pandas as pd
from scipy import stats
OUT="."
d=pd.read_csv(f"{OUT}/ndvi_by_neighbourhood_year.csv")
t=pd.read_csv(".").set_index("neighbourhood")
d["w"]=d.n_pixels*d.valid_pixel_frac
mun=d.groupby("year").apply(lambda g:pd.Series(dict(n_scenes=g.n_scenes.iloc[0],mean_ndvi=np.average(g.mean_ndvi,weights=g.w),veg_pct=np.average(g.veg_share_pct,weights=g.w),dense_pct=np.average(g.dense_share_pct,weights=g.w))))
mun.round(3).to_csv(f"{OUT}/municipal_by_year.csv");print(mun.round(3))
P=lambda c:d.pivot(index="neighbourhood",columns="year",values=c)
vs,mn,ds=P("veg_share_pct"),P("mean_ndvi"),P("dense_share_pct")
def sp(a,b):
    b=b.reindex(a.index);m=a.notna()&b.notna();return round(float(stats.spearmanr(a[m],b[m]).correlation),3)
print("VALID 2018 veg~ua_stl2018",sp(vs[2018],t.ua_stl2018_pct),"dense",sp(ds[2018],t.ua_stl2018_pct))
for y in (2020,2021): print("VALID",y,"veg~wc2021",sp(vs[y],t.wc2021_tree_pct),"veg~metachm",sp(vs[y],t.metachm_ge3m_pct),"dense~wc2021",sp(ds[y],t.wc2021_tree_pct),"dense~metachm",sp(ds[y],t.metachm_ge3m_pct))
Y=[y for y in mn.columns if y!=2017]   # 2017 excluded: product anomaly (see README)
mn,vs,ds=mn[Y],vs[Y],ds[Y]
# --- normalisation
yr_eff=(mn.sub(mn.median(1),axis=0)).median()      # city-wide year effect (median over 144 nb)
mn_n=mn.sub(yr_eff,axis=1)
vyr=(vs.sub(vs.median(1),axis=0)).median();vs_n=vs.sub(vyr,axis=1)
built=[b for b in t.index[(t.wc2021_tree_pct<2)&(t.ua_stl2018_pct<1)&(t.metachm_ge3m_pct<2)] if b in mn.index]
forest=[n for n in mn.index if "ΛΥΚΑΒΗΤΤ" in n]
x=np.array(Y,float)
def resid_sd(df):  # SD of residuals about each nb's own linear trend (dof n-2)
    out={}
    for n,r in df.iterrows():
        sl,ic,_,_,_=stats.linregress(x,r.values);e=r.values-(ic+sl*x);out[n]=np.sqrt((e**2).sum()/(len(x)-2))
    return pd.Series(out)
sd_raw=mn.std(1,ddof=1);rs_raw=resid_sd(mn);rs_n=resid_sd(mn_n);rsv_n=resid_sd(vs_n)
print("year effects mean_ndvi (median nb dev):",yr_eff.round(4).to_dict())
print("year effects veg_share pp:",vyr.round(2).to_dict())
print("built-ref (n=%d) raw SD across years: median %.4f; resid-about-trend normalised: median %.4f p90 %.4f"%(len(built),sd_raw[built].median(),rs_n[built].median(),rs_n[built].quantile(.9)))
print("forest",forest,"raw SD",sd_raw[forest].round(4).tolist(),"norm resid SD",rs_n[forest].round(4).tolist())
print("built veg_share resid SD (norm) median %.2f p90 %.2f ; all-nb median %.2f"%(rsv_n[built].median(),rsv_n[built].quantile(.9),rsv_n.median()))
print("municipal-mean swing between years (mean_ndvi): range %.3f (%s)"%(mun.loc[Y].mean_ndvi.max()-mun.loc[Y].mean_ndvi.min(),Y))
# built-ref noise of year-mean differences
SIG=rs_n.median()  # typical nb noise (all-nb median) used as floor
SIGV=rsv_n.median()
print("noise floors used: ndvi",round(SIG,4),"veg pp",round(SIGV,2))
rows=[]
for n in mn.index:
    r=mn_n.loc[n];rv=vs_n.loc[n];rd=ds.loc[n]
    sl,ic,_,p,se=stats.linregress(x,r.values);slv,_,_,pv,_=stats.linregress(x,rv.values)
    first,last=Y[:2],Y[-2:]
    dn=r[last].mean()-r[first].mean();dnr=mn.loc[n,last].mean()-mn.loc[n,first].mean()
    dv=rv[last].mean()-rv[first].mean();dvr=vs.loc[n,last].mean()-vs.loc[n,first].mean()
    sig=max(SIG,rs_n[n]);sigv=max(SIGV,rsv_n[n])
    rel=(abs(dn)>2*sig) and p<0.05
    relv=(abs(dv)>2*sigv) and pv<0.05
    rows.append(dict(neighbourhood=n,first_years=f"{first[0]}-{first[1]}",last_years=f"{last[0]}-{last[1]}",
      mean_ndvi_first=mn.loc[n,first].mean(),mean_ndvi_last=mn.loc[n,last].mean(),delta_ndvi_raw=dnr,delta_ndvi_norm=dn,
      trend_ndvi_per_yr_norm=sl,trend_p=p,noise_sd_ndvi=sig,
      veg_share_first=vs.loc[n,first].mean(),veg_share_last=vs.loc[n,last].mean(),delta_veg_pp_raw=dvr,delta_veg_pp_norm=dv,trend_veg_pp_per_yr_norm=slv,trend_veg_p=pv,noise_sd_veg_pp=sigv,
      change_reliable=bool(rel),direction=("gain" if dn>0 else "loss") if rel else "none",veg_change_reliable=bool(relv),
      ndvi_resid_sd=rs_n[n],area_km2=t.area_km2.get(n)))
c=pd.DataFrame(rows).sort_values("delta_ndvi_norm",ascending=False)
c.to_csv(f"{OUT}/change_by_neighbourhood.csv",index=False,float_format="%.4f")
print("reliable:",c.change_reliable.sum(),"gains",(c.direction=="gain").sum(),"losses",(c.direction=="loss").sum(),"veg-reliable",c.veg_change_reliable.sum())
cols=["neighbourhood","delta_ndvi_raw","delta_ndvi_norm","trend_ndvi_per_yr_norm","trend_p","noise_sd_ndvi","delta_veg_pp_norm","mean_ndvi_first","area_km2"]
pd.set_option("display.width",250)
print("TOP GAINS");print(c[c.change_reliable&(c.direction=="gain")].head(10)[cols].round(3).to_string())
print("TOP LOSSES");print(c[c.change_reliable&(c.direction=="loss")].sort_values("delta_ndvi_norm").head(10)[cols].round(3).to_string())
print("raw delta median %.3f, share nb with raw decline > noise: %d"%(c.delta_ndvi_raw.median(),(c.delta_ndvi_raw<-2*SIG).sum()))
print("largest unconditional:");print(c.head(5)[cols].round(3).to_string());print(c.tail(5)[cols].round(3).to_string())
