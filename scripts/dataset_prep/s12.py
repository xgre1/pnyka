import pandas as pd, numpy as np
D='/tmp/athens_env/data/'
df=pd.read_csv(D+'all.csv'); reg=pd.read_csv(D+'reg.csv'); nb=pd.read_csv(D+'nb.csv')
print('rows',len(df),'dups',df.duplicated(['station_id','timestamp']).sum())
df=df.drop_duplicates(['station_id','timestamp'],keep='first')
print('after dedupe',len(df))
df['ts']=pd.to_datetime(df.timestamp,utc=True)
df['loc']=df.ts.dt.tz_convert('Europe/Athens')
print('max ts',df.ts.max())
s=df[(df['loc']>=pd.Timestamp('2026-06-01',tz='Europe/Athens'))&(df['loc']<pd.Timestamp('2026-09-01',tz='Europe/Athens'))].copy()
s['date']=s['loc'].dt.date; s['h']=s['loc'].dt.hour
t=s.dropna(subset=['temperature'])
print('summer rows with temp',len(t))
dm=t.groupby(['station_id','date']).temperature.agg(['max','size']); dm=dm[dm['size']>=18]
res=pd.DataFrame({'heat_mean':t.groupby('station_id').temperature.mean(),
 'heat_night':t[t.h<=5].groupby('station_id').temperature.mean(),
 'hours_above_35':t[t.temperature>35].groupby('station_id').size(),
 'hours_above_38':t[t.temperature>38].groupby('station_id').size(),
 'summer_temp_hours':t.groupby('station_id').size()})
res['heat_daily_max']=dm.groupby('station_id')['max'].mean()
res['valid_days']=dm.groupby('station_id').size()
res=res.fillna({'hours_above_35':0,'hours_above_38':0}); res['valid_days']=res.valid_days.fillna(0).astype(int)
print(res.loc[[65,151,55,7]].round(3).to_string())
res['heat_flag']=''
res.loc[7,'heat_flag']='excluded_stuck_sensor'
res.to_pickle('/tmp/athens_prep/heat_all.pkl')
print((res.valid_days>=46).sum(),'stations >=46 days of',len(res)); print(res[res.valid_days<46].valid_days)
# air
a=df[df['loc']>=pd.Timestamp('2026-01-01',tz='Europe/Athens')].copy()
print('air rows',len(a), a.ts.max())
lim={'pm2_5':500,'pm10':1000,'no2':300,'o3':400}
out=pd.DataFrame(index=sorted(a.station_id.unique()))
for c,l in lim.items():
    v=a[['station_id',c]].dropna(); cl=v[v[c]<=l]
    out[c]=cl.groupby('station_id')[c].mean(); out[c+'_n']=cl.groupby('station_id').size()
    out[c+'_raw']=v.groupby('station_id')[c].mean()
    out[c+'_dropped']=v[v[c]>l].groupby('station_id').size()
out=out.fillna({k+'_dropped':0 for k in lim})
out['pm_spiky']=((out.pm2_5_raw-out.pm2_5).abs()/out.pm2_5>0.2)
out.to_pickle('/tmp/athens_prep/air_all.pkl')
print(out.round(2).to_string())
print(sorted(set(df.station_id)-set(reg.station_id)))
print(reg.neighbourhood_id.isin(nb.neighbourhood_id).all(), reg.station_id.is_unique, len(reg))
