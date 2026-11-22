import pandas as pd, numpy as np
from scipy import stats
r=pd.read_pickle('/tmp/athens_treecover/res.pkl')
r=r.drop(columns=['ua2012_forest_pct','ua2012_herbaceous_pct','ua2012_green_total_pct'])
r.to_pickle('/tmp/athens_treecover/res2.pkl')
h=pd.read_csv('/tmp/athens_env/heat_station.csv')
hn=h.groupby('nb').agg(n_sensors=('station_id','count'),dmax=('dmax','mean'),night=('night','mean'),mean_temp=('mean','mean')).reset_index().rename(columns={'nb':'neighbourhood'})
hn.to_pickle('/tmp/athens_treecover/hn.pkl')
m=r.merge(hn,on='neighbourhood')
print('n joined',len(m))
A=r.area_km2
print('MUNICIPAL (area weighted over 144 polys, total km2 %.3f)'%A.sum())
tm=[c for c in r.columns if c.endswith('_pct') or 'height' in c]
for c in tm: print(f'  {c:28s} {np.average(r[c],weights=A):.2f}')
print('SOURCE CORR (n=144) pearson / spearman vs wc2021')
for c in tm:
    print(f'  {c:28s} {stats.pearsonr(r.wc2021_tree_pct,r[c])[0]:.2f} {stats.spearmanr(r.wc2021_tree_pct,r[c])[0]:.2f}')
print('area-weighted? tcd vs wc'); 
rows=[]
for c in tm:
    for t in ['dmax','night']:
        p=stats.pearsonr(m[c],m[t]);s=stats.spearmanr(m[c],m[t]);rows.append((c,t,len(m),round(p[0],3),round(p[1],3),round(s[0],3),round(s[1],3)))
print(pd.DataFrame(rows,columns=['metric','temp','n','pearson','p','spearman','p_s']).to_string())
low=m.sort_values(['wc2021_tree_pct','neighbourhood']).head(15)[['neighbourhood','area_km2','wc2021_tree_pct','tcd2018_mean_pct','metachm_ge3m_pct','n_sensors','dmax','night']]
print(low.round(2).to_string())
low.round(2).to_csv('/tmp/athens_treecover/low15.csv',index=False)
print('median dmax',m.dmax.median(),'sd',m.dmax.std())
print(m.n_sensors.value_counts().to_dict())
# only 1-sensor vs multi
m1=m[m.n_sensors>=2]
print('multi-sensor nbs',len(m1),stats.pearsonr(m1.wc2021_tree_pct,m1.dmax),stats.pearsonr(m1.wc2021_tree_pct,m1.night))
# area >=0.15 km2
m2=m[m.area_km2>=0.15];print('area>=0.15',len(m2),stats.spearmanr(m2.wc2021_tree_pct,m2.dmax),stats.spearmanr(m2.wc2021_tree_pct,m2.night))
