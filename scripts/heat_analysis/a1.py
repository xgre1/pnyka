import pandas as pd, numpy as np
D='/tmp/athens_env/data/'
df=pd.read_csv(D+'all.csv'); reg=pd.read_csv(D+'reg.csv'); nb=pd.read_csv(D+'nb.csv'); md=pd.read_csv(D+'md.csv')
print(len(df), df.station_id.nunique(), df.timestamp.min(), df.timestamp.max())
print('reg cols',list(reg.columns)); print('registry stations',len(reg),'coord cols in reg:',[c for c in reg.columns if 'lat' in c or 'lon' in c])
print('co2 cols',[c for c in df.columns if 'co2' in c.lower()])
print('dup station-ts',df.duplicated(['station_id','timestamp']).sum())
F=['aqi','temperature','humidity','pressure','pm1','pm2_5','pm10','co','no','no2','o3','so2']
print(df[F].describe().T.to_string())
rows=[]
for f in F:
    s=df[f];rows.append((f,s.isna().mean()*100,(s==0).mean()*100,(s<0).mean()*100))
print(pd.DataFrame(rows,columns=['f','miss%','zero%','neg%']).round(2).to_string())
lim={'temperature':(-5,50),'humidity':(0,100),'pressure':(900,1100),'pm2_5':(0,500),'pm10':(0,1000),'no2':(0,500),'o3':(0,500),'co':(0,50000),'aqi':(0,500)}
for f,(a,b) in lim.items():
    s=df[f];print(f,'implausible %.3f%% n=%d'%(((s<a)|(s>b)).mean()*100,((s<a)|(s>b)).sum()))
for f in ['pressure','co','no','no2','o3','so2']:print(f,df[f].quantile([.01,.5,.99]).tolist())
df['ts']=pd.to_datetime(df.timestamp)
g=df.groupby('station_id').agg(n=('ts','size'),first=('ts','min'),last=('ts','max'),name=('station_name','first'),nb=('neighbourhood_name','first'),md=('municipal_district_id','first'))
g['span_h']=((g['last']-g['first']).dt.total_seconds()/3600+1);g['cov%']=g.n/g.span_h*100
print(g.describe().to_string()); print(g.sort_values('n').head(8).to_string())
print('stations not in registry',set(df.station_id)-set(reg.station_id),'registry not in data',set(reg.station_id)-set(df.station_id))
print('stations per nb',g.groupby('nb').size().describe())
print(df.groupby('station_id').neighbourhood_name.nunique().max())
