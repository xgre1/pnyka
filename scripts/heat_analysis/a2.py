import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',30); pd.set_option('display.max_rows',200)
D='/tmp/athens_env/data/'
df=pd.read_csv(D+'all.csv'); nb=pd.read_csv(D+'nb.csv'); md=pd.read_csv(D+'md.csv')
df=df.drop_duplicates(['station_id','timestamp'])
df['ts']=pd.to_datetime(df.timestamp).dt.tz_localize('UTC').dt.tz_convert('Europe/Athens')
print('rows after dedup',len(df))
print('nb names match:',df.neighbourhood_name.isin(nb.name).mean(), df.neighbourhood_name.isin(nb.friendly_name).mean(), 'nb in data',df.neighbourhood_name.nunique(), 'nb total',len(nb), nb.name.nunique())
st=df.groupby('station_id').agg(name=('station_name','first'),nb=('neighbourhood_name','first'),md=('municipal_district_id','first'))
# summer
s=df[(df.ts>='2026-06-01')&(df.ts<'2026-09-01')].dropna(subset=['temperature']).copy()
s['date']=s.ts.dt.date; s['hr']=s.ts.dt.hour
print('summer rows',len(s),'stations',s.station_id.nunique(),'temp max',s.temperature.max(), 'rows>45',(s.temperature>45).sum(),'rows>42',(s.temperature>42).sum())
print(s[s.temperature>44].groupby('station_id').temperature.agg(['size','max']))
hrs=92*24
def heat(s,key):
    d=s.groupby([key,'date']).agg(mx=('temperature','max'),h=('temperature','size')).reset_index()
    d=d[d.h>=18]
    night=s[s.hr<6].groupby(key).temperature.mean()
    g=s.groupby(key).agg(mean=('temperature','mean'),n=('temperature','size'),h35=('temperature',lambda x:(x>35).sum()),h38=('temperature',lambda x:(x>38).sum()))
    g['dmax']=d.groupby(key).mx.mean(); g['night']=night; g['days']=d.groupby(key).size(); g['cov%']=g.n/hrs*100
    return g
hs=heat(s,'station_id'); hs=st.join(hs,how='inner')
# station mean-of-hours uses available hours; require cov>=50% 
print('summer stations',len(hs),'cov<50%:',(hs['cov%']<50).sum(), hs[hs['cov%']<50][['name','cov%']].to_string())
hsq=hs[hs['cov%']>=50].copy()
hsq.to_pickle('/tmp/athens_env/hsq.pkl')
print('STATIONS (cov>=50%) n=',len(hsq))
cols=['name','nb','mean','dmax','night','h35','h38','cov%']
r=hsq.sort_values('dmax',ascending=False)[cols].round(2)
print(r.head(12).to_string()); print(r.tail(12).to_string())
# neighbourhood: average station values per nb
hn=hsq.groupby('nb').agg(stations=('name','size'),mean=('mean','mean'),dmax=('dmax','mean'),night=('night','mean'),h35=('h35','mean'),h38=('h38','mean')).round(2)
hn.to_pickle('/tmp/athens_env/hn.pkl')
print('NB n=',len(hn)); h=hn.sort_values('dmax',ascending=False)
print(h.head(10).to_string()); print(h.tail(10).to_string())
for c in ['mean','dmax','night']:print(c,'hot-cool',round(hn[c].max()-hn[c].min(),2),hn[c].idxmax(),hn[c].idxmin(),'IQR-ish p90-p10',round(hn[c].quantile(.9)-hn[c].quantile(.1),2))
print('rank by mean top3',hn['mean'].nlargest(3).index.tolist(),'night top',hn.night.nlargest(3).index.tolist())
# robustness: daily spread per day, nb-level
sq=s[s.station_id.isin(hsq.index)].merge(st[['nb']],left_on='station_id',right_index=True)
dd=sq.groupby(['nb','date']).agg(mx=('temperature','max'),h=('temperature','size'))
nbd=sq.groupby(['station_id','nb','date']).temperature.agg(['max','size']).reset_index(); nbd=nbd[nbd['size']>=18]
nbd=nbd.groupby(['nb','date'])['max'].mean().unstack(0)
hot,cool=h.index[0],h.index[-1]
x=(nbd[hot]-nbd[cool]).dropna()
print('hot',hot,'cool',cool,'days both',len(x),'share days hot>cool',(x>0).mean().round(3),'median diff',x.median().round(2),'mean',x.mean().round(2))
# robust: remove hottest and coolest 3 NB; exclude neighbourhoods w/ 1 station? 
# hourly cross-nb spread
# top hot nb: share of days in top-third
rk=nbd.rank(axis=1,ascending=False,pct=True)
cons=(rk<=1/3).mean().sort_values(ascending=False)
print('share of days in hottest third (daily max):'); print(cons.head(10).round(2).to_string()); print(cons.tail(10).round(2).to_string())
# daily spread across stations
dsp=nbd.max(axis=1)-nbd.min(axis=1); print('daily nb spread of dmax: median',dsp.median().round(2),'p10',dsp.quantile(.1).round(2),'p90',dsp.quantile(.9).round(2))
dsp2=nbd.quantile(.9,axis=1)-nbd.quantile(.1,axis=1); print('daily p90-p10 across nb median',dsp2.median().round(2))
# station-level robustness: leave-out spikes: station median of daily max
sd=sq.groupby(['station_id','date']).temperature.agg(['max','size']).reset_index(); sd=sd[sd['size']>=18]
med=sd.groupby('station_id')['max'].median(); print('median-of-daily-max spread across stations',round(med.max()-med.min(),2),'IQR',round(med.quantile(.75)-med.quantile(.25),2))
# trimmed: drop stations below 85% cov
hh=hsq[hsq['cov%']>=85]; print('stations cov>=85%',len(hh),'dmax range',round(hh.dmax.max()-hh.dmax.min(),2),'p90-p10',round(hh.dmax.quantile(.9)-hh.dmax.quantile(.1),2))
# station max temp per station: faulty?
print(sq.groupby('station_id').temperature.max().sort_values().tail(5)); print(sq.groupby('station_id').temperature.min().sort_values().head(5))
