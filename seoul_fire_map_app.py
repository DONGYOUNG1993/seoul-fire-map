import json
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="서울 출동건수", layout="wide")
st.title("서울 행정동 출동건수")

with open("dong_emergency_count.geojson","r",encoding="utf-8") as f:
    geojson=json.load(f)

rows=[]
for feat in geojson["features"]:
    p=feat["properties"]
    rows.append({"ADM_CD":p["ADM_CD"],"ADM_NM":p["ADM_NM"],"emergency_count":p["emergency_count"]})
df=pd.DataFrame(rows)

only_mok=st.toggle("목×동만 보기",False)
if only_mok:
    df=df[df["ADM_NM"].str.contains("목",na=False)]

fig=px.choropleth_mapbox(
    df,
    geojson=geojson,
    locations="ADM_CD",
    featureidkey="properties.ADM_CD",
    color="emergency_count",
    color_continuous_scale=[[0,"white"],[1,"red"]],
    hover_name="ADM_NM",
    hover_data={"ADM_CD":True,"emergency_count":False},
    center={"lat":37.5665,"lon":126.9780},
    zoom=10,
    opacity=0.75
)
fig.update_layout(mapbox_style="carto-positron",margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig,use_container_width=True)
