import pandas as pd, numpy as np, re
pd.set_option('display.width',250); pd.set_option('display.max_columns',30); pd.set_option('display.max_rows',300); pd.set_option('display.max_colwidth',60)
D='/tmp/athens_env/data/'
df=pd.read_csv(D+'all.csv').drop_duplicates(['station_id','timestamp']); nb=pd.read_csv(D+'nb.csv'); reg=pd.read_csv(D+'reg.csv')
df['ts']=pd.to_datetime(df.timestamp).dt.tz_localize('UTC').dt.tz_convert('Europe/Athens')
st=df.groupby('station_id').agg(name=('station_name','first'),nb=('neighbourhood_name','first'),md=('municipal_district_id','first'))
# stuck sensor check (summer)
s=df[(df.ts>='2026-06-01')&(df.ts<'2026-09-01')].dropna(subset=['temperature']).copy()
sd=s.groupby('station_id').temperature.agg(['std','size','min','max'])
print('lowest summer temp std'); print(sd.sort_values('std').head(4))
# within-day variability
s['date']=s.ts.dt.date; s['hr']=s.ts.dt.hour
rng=s.groupby(['station_id','date']).temperature.agg(lambda x:x.max()-x.min()).groupby('station_id').median()
print('median daily range lowest'); print(rng.sort_values().head(4))
bad=set(rng[rng<3].index); print('excluded stuck',bad)
hrs=92*24
n=s.groupby('station_id').size(); keep=[i for i in n.index if n[i]/hrs>=.5 and i not in bad]
s=s[s.station_id.isin(keep)]
dm=s.groupby(['station_id','date']).temperature.agg(['max','size']); dm=dm[dm['size']>=18].reset_index()
H=pd.DataFrame({'mean':s.groupby('station_id').temperature.mean(),'dmax':dm.groupby('station_id')['max'].mean(),
 'night':s[s.hr<6].groupby('station_id').temperature.mean(),'h35':s.groupby('station_id').temperature.apply(lambda x:(x>35).sum()),
 'h38':s.groupby('station_id').temperature.apply(lambda x:(x>38).sum()),'cov%':n[keep]/hrs*100}).join(st)
print('stations used for heat',len(H))
H.to_csv('/tmp/athens_env/heat_station.csv')
NB=H.groupby('nb').agg(st=('name','size'),mean=('mean','mean'),dmax=('dmax','mean'),night=('night','mean'),h35=('h35','mean'),h38=('h38','mean')).round(2)
print('heat neighbourhoods',len(NB)); o=NB.sort_values('dmax',ascending=False)
print('HOT10');print(o.head(10).to_string());print('COOL10');print(o.tail(10).to_string())
for c in ['mean','dmax','night']:
    print(c,'max-min',round(NB[c].max()-NB[c].min(),2),NB[c].idxmax(),'|',NB[c].idxmin(),'| p90-p10',round(NB[c].quantile(.9)-NB[c].quantile(.1),2),'| median',round(NB[c].median(),2))
print('top mean',NB['mean'].nlargest(3).round(2).to_dict(),'low mean',NB['mean'].nsmallest(3).round(2).to_dict())
print('top night',NB.night.nlargest(3).to_dict(),'low night',NB.night.nsmallest(3).to_dict())
# robustness
hot,cool=o.index[0],o.index[-1]
dd=dm.merge(st[['nb']],left_on='station_id',right_index=True).groupby(['nb','date'])['max'].mean().unstack(0)
x=(dd[hot]-dd[cool]).dropna();print('hot',hot,'cool',cool,'days',len(x),'hot>cool share',(x>0).mean().round(3),'median diff',x.median().round(2),'p10',x.quantile(.1).round(2),'p90',x.quantile(.9).round(2))
# robust version: group top-10 mean vs bottom-10 mean per day
top=o.index[:10];bot=o.index[-10:]
y=(dd[top].mean(axis=1)-dd[bot].mean(axis=1)).dropna();print('top10 minus bottom10 daily max, days',len(y),'share>0',(y>0).mean().round(3),'median',y.median().round(2),'min',y.min().round(2))
# split-half: rank on June+July vs August
sm=dm.assign(m=pd.to_datetime(dm.date).dt.month).merge(st[['nb']],left_on='station_id',right_index=True)
a=sm[sm.m.isin([6,7])].groupby('nb')['max'].mean();b=sm[sm.m==8].groupby('nb')['max'].mean();j=pd.concat([a,b],axis=1).dropna()
print('split-half corr JunJul vs Aug nb daily max',round(j.corr().iloc[0,1],3),'spearman',round(j.corr('spearman').iloc[0,1],3))
# night stuck: any station w/ implausible? Station-level lists
SH=H.sort_values('dmax',ascending=False)
print('STATION HOT10');print(SH.head(10)[['name','nb','mean','dmax','night','h35','h38']].round(2).to_string())
print('STATION COOL10');print(SH.tail(10)[['name','nb','mean','dmax','night','h35','h38']].round(2).to_string())
print('top-5 hottest station h38 median',SH.h38.median())
# siting category
def cat(n):
    if re.search(r'Πάρκο|Άλσος|Κήπος|Λόφος|Παιδική',n,re.I):return 'park/grove/playground'
    if re.search(r'Πλατεί',n,re.I):return 'square'
    if re.search(r'Γήπεδο|Αθλητικ|Γυμναστ|Κολυμβ',n,re.I):return 'sports'
    if re.search(r'Σχολ|Δημοτικ|Βιβλιο|Θέατρο|Κέντρο|Κοινότητα',n,re.I):return 'building/school/civic'
    return 'other'
H['cat']=H.name.map(cat); print(H.groupby('cat').agg(n=('name','size'),dmax=('dmax','mean'),mean=('mean','mean'),night=('night','mean'),h38=('h38','median')).round(2))
print('hot10 cats',H.loc[SH.head(10).index,'cat'].value_counts().to_dict(),'cool10 cats',H.loc[SH.tail(10).index,'cat'].value_counts().to_dict())
# AIR
A=df.copy()
A.loc[A.pm2_5>500,['pm2_5','pm1','pm10']]=np.nan  # spike rows
A.loc[A.pm10>1000,'pm10']=np.nan
A.loc[A.no2>300,'no2']=np.nan; A.loc[A.o3>400,'o3']=np.nan
print('rows removed pm2.5>500',(df.pm2_5>500).sum(),'pm10>1000',(df.pm10>1000).sum(),'no2>300',(df.no2>300).sum(),'o3>400',(df.o3>400).sum())
tot=len(pd.date_range('2026-01-01','2026-11-21',freq='h'))
res=pd.DataFrame(index=st.index)
for f in ['pm2_5','pm10','no2','o3']:
    res[f+'_raw']=df.groupby('station_id')[f].mean(); res[f]=A.groupby('station_id')[f].mean(); res[f+'_n']=A.groupby('station_id')[f].count()
    res[f+'_med']=A.groupby('station_id')[f].median()
res=res.join(st)
ok={f:res[f+'_n']>=3000 for f in ['pm2_5','pm10','no2','o3']}
print('stations w/ >=3000 valid h:',{f:int(v.sum()) for f,v in ok.items()})
res.to_csv('/tmp/athens_env/air_station.csv')
for f in ['pm2_5','pm10','no2','o3']:
    r=res[ok[f]].sort_values(f)
    print('\n',f,'stations',len(r),'ratio worst/best',round(r[f].max()/r[f].min(),2),'median',round(r[f].median(),2),'mean',round(r[f].mean(),2))
    print('best5',r[[ 'name',f,f+'_raw',f+'_n']].head(5).round(1).to_string());print('worst5',r[['name',f,f+'_raw',f+'_n']].tail(5).round(1).to_string())
p=res[ok['pm2_5']];n2=res[ok['no2']]
print('\nPM2.5>5 (WHO):',(p.pm2_5>5).sum(),'of',len(p),' raw',(p.pm2_5_raw>5).sum(),' >25 EU:',(p.pm2_5>25).sum(),' raw',(p.pm2_5_raw>25).sum(), 'max',p.pm2_5.max().round(1),'min',p.pm2_5.min().round(1))
print('NO2>10 (WHO):',(n2.no2>10).sum(),'of',len(n2),' >40 EU:',(n2.no2>40).sum(),' raw>40',(n2.no2_raw>40).sum(),'max',n2.no2.max().round(1),'min',n2.no2.min().round(1))
print('PM10 >15 WHO',(res[ok['pm10']].pm10>15).sum(),'>40 EU',(res[ok['pm10']].pm10>40).sum())
# neighbourhood air
AN=res.groupby('nb').agg(st=('name','size'),pm2_5=('pm2_5','mean'),pm10=('pm10','mean'),no2=('no2','mean'),o3=('o3','mean')).round(2)
for f in ['pm2_5','pm10','no2','o3']:
    r=AN[f].dropna().sort_values();print(f,'nb',len(r),'best',r.head(3).round(1).to_dict(),'worst',r.tail(3).round(1).to_dict(),'ratio',round(r.max()/r.min(),2))
AN.to_csv('/tmp/athens_env/air_nb.csv')
# combined
pm=res[ok['pm2_5']].groupby('nb').pm2_5.mean()
C=NB[['dmax']].join(pm.rename('pm2_5'),how='inner'); print('combined nb',len(C))
k=int(np.ceil(len(C)/3)); hh=set(C.dmax.nlargest(k).index); pp=set(C.pm2_5.nlargest(k).index); both=sorted(hh&pp)
print('third size',k,'both',len(both)); print(C.loc[both].round(2).sort_values('dmax',ascending=False).to_string())
print('spearman dmax vs pm2.5',round(C.corr('spearman').iloc[0,1],3))
# coverage
allnb=set(nb.name); has=set(st.nb)
print('nb with >=1 station (data)',len(has&allnb),'of',len(allnb),'; reg stations',reg.station_id.nunique(),'reg nbs',reg.neighbourhood_name.nunique())
nb2=nb.set_index('name'); cnt=st.groupby('md').size(); nbs=nb.groupby('municipal_district_id').size()
cov=pd.DataFrame({'stations':cnt,'nb_total':nbs,'nb_with_station':st.groupby('md').nb.nunique()}).fillna(0).astype(int); cov['nb_cov%']=(cov.nb_with_station/cov.nb_total*100).round(0)
cov['st_per_nb']=(cov.stations/cov.nb_total).round(2); print(cov.sort_values('stations'))
print('multi-station nbs',st.groupby('nb').size()[lambda x:x>1].to_dict())
print('nb polygons centroid columns exist; station coordinates: none in registry')
print('stations total in data',len(st),'in registry',st.index.isin(reg.station_id).sum())
