import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="서울 행정동별 출동건수",
    page_icon="🚒",
    layout="wide",
)

st.title("🚒 서울시 행정동별 출동건수")

BASE_DIR = Path(__file__).resolve().parent
GEOJSON_FILE = BASE_DIR / "dong_emergency_count.geojson"


@st.cache_data
def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    rows = []

    for feature in geojson["features"]:
        properties = feature.get("properties", {})

        rows.append(
            {
                "ADM_CD": str(properties.get("ADM_CD", "")),
                "ADM_NM": str(properties.get("ADM_NM", "")),
                "emergency_count": pd.to_numeric(
                    properties.get("emergency_count", 0),
                    errors="coerce",
                ),
            }
        )

    df = pd.DataFrame(rows)
    df["emergency_count"] = df["emergency_count"].fillna(0)

    return geojson, df


if not GEOJSON_FILE.exists():
    st.error(
        "GeoJSON 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 "
        "`dong_emergency_count.geojson` 파일을 넣어주세요."
    )
    st.stop()


geojson, df = load_data(GEOJSON_FILE)


# ------------------------------------------------------------
# 목×동 Toggle
# ------------------------------------------------------------
st.sidebar.header("지도 설정")

only_mok = st.sidebar.toggle(
    "목×동만 보기",
    value=False,
    help="켜면 '목'이 포함된 행정동만 출동건수 색상으로 표시합니다.",
)


plot_df = df.copy()

if only_mok:
    mok_mask = plot_df["ADM_NM"].str.contains("목", na=False)

    plot_df["display_count"] = plot_df["emergency_count"]
    plot_df.loc[~mok_mask, "display_count"] = 0
else:
    plot_df["display_count"] = plot_df["emergency_count"]


# ------------------------------------------------------------
# Choropleth 지도
# ------------------------------------------------------------
max_count = max(float(df["emergency_count"].max()), 1)

fig = px.choropleth_map(
    plot_df,
    geojson=geojson,
    locations="ADM_CD",
    featureidkey="properties.ADM_CD",
    color="display_count",
    color_continuous_scale=[
        [0.00, "#FFFFFF"],
        [0.10, "#FEE5D9"],
        [0.30, "#FCAE91"],
        [0.50, "#FB6A4A"],
        [0.70, "#DE2D26"],
        [0.85, "#CB181D"],
        [1.00, "#99000D"],
    ],
    range_color=[0, max_count],
    hover_name="ADM_NM",
    hover_data={
        "ADM_CD": True,
        "emergency_count": True,
        "display_count": False,
    },
    center={
        "lat": 37.5665,
        "lon": 126.9780,
    },
    zoom=9.8,
)

fig.update_traces(
    marker_line_color="#777777",
    marker_line_width=0.5,
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "행정동 코드: %{customdata[0]}<br>"
        "출동건수: %{customdata[1]:,.0f}건"
        "<extra></extra>"
    ),
)

fig.update_layout(
    map_style="carto-positron",
    height=700,
    margin=dict(l=0, r=0, t=0, b=0),
    font=dict(
        family=(
            "Noto Sans KR, Noto Sans CJK KR, "
            "Apple SD Gothic Neo, Malgun Gothic, sans-serif"
        ),
        size=13,
    ),
    coloraxis_colorbar=dict(
        title="출동건수",
        tickformat=",",
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displaylogo": False,
        "scrollZoom": True,
    },
)


# ------------------------------------------------------------
# 데이터 요약
# ------------------------------------------------------------
st.subheader("📊 데이터 요약")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("행정동 수", f"{len(df):,}개")

with col2:
    st.metric(
        "총 출동건수",
        f"{df['emergency_count'].sum():,.0f}건",
    )

with col3:
    st.metric(
        "평균 출동건수",
        f"{df['emergency_count'].mean():,.1f}건",
    )

with col4:
    max_row = df.loc[df["emergency_count"].idxmax()]

    st.metric(
        "최다 출동 행정동",
        max_row["ADM_NM"],
        f"{max_row['emergency_count']:,.0f}건",
    )


# ------------------------------------------------------------
# 출동건수 TOP 10
# ------------------------------------------------------------
with st.expander("출동건수 상위 10개 행정동 보기"):

    top10 = (
        df[["ADM_NM", "ADM_CD", "emergency_count"]]
        .sort_values("emergency_count", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    top10.index = top10.index + 1

    top10.columns = [
        "행정동",
        "행정동 코드",
        "출동건수",
    ]

    st.dataframe(
        top10,
        use_container_width=True,
    )


st.caption(
    "※ 제공된 GeoJSON의 행정동 경계를 사용합니다. "
    "출동건수가 적을수록 흰색, 많을수록 빨간색으로 표시됩니다."
)
