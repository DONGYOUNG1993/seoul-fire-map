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



# ------------------------------------------------------------
# dong_emergency_count 데이터 표 요약
# ------------------------------------------------------------
st.subheader("📋 행정동별 출동건수 데이터 요약")

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric("최소 출동건수", f"{df['emergency_count'].min():,.0f}건")

with summary_col2:
    st.metric("중앙값", f"{df['emergency_count'].median():,.0f}건")

with summary_col3:
    st.metric("75% 분위수", f"{df['emergency_count'].quantile(0.75):,.0f}건")

with summary_col4:
    st.metric("최대 출동건수", f"{df['emergency_count'].max():,.0f}건")


with st.expander("행정동별 출동건수 전체 표 보기", expanded=True):
    table_df = (
        df[["ADM_NM", "ADM_CD", "emergency_count"]]
        .sort_values("emergency_count", ascending=False)
        .reset_index(drop=True)
    )

    table_df.columns = [
        "행정동",
        "행정동 코드",
        "출동건수",
    ]

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "행정동": st.column_config.TextColumn("행정동"),
            "행정동 코드": st.column_config.TextColumn("행정동 코드"),
            "출동건수": st.column_config.NumberColumn(
                "출동건수",
                format="%,d건",
            ),
        },
    )


# ============================================================
# 서울시 소방서 · 안전센터 · 구조대 위치 지도
# ============================================================
st.subheader("🚒 서울시 소방서 · 안전센터 · 구조대 위치")

# 소방시설 Excel 파일
# 파일명을 특정하지 않고, app.py와 같은 폴더의 .xlsx 파일을 자동으로 찾습니다.
xlsx_files = sorted(BASE_DIR.glob("*.xlsx"))

if len(xlsx_files) == 0:
    FACILITY_FILE = None
elif len(xlsx_files) == 1:
    FACILITY_FILE = xlsx_files[0]
else:
    # 여러 Excel 파일이 있다면 파일명에 소방/안전/구조가 포함된 파일을 우선 선택
    candidates = [
        f for f in xlsx_files
        if any(keyword in f.name for keyword in ["소방", "안전", "구조", "fire"])
    ]
    FACILITY_FILE = candidates[0] if candidates else xlsx_files[0]


@st.cache_data
def load_facility_data(file_path):
    facility_df = pd.read_excel(file_path)

    required_columns = ["서ㆍ센터명", "유형구분명", "X좌표", "Y좌표"]
    missing = [c for c in required_columns if c not in facility_df.columns]

    if missing:
        raise ValueError(
            "소방시설 데이터에 필요한 컬럼이 없습니다: "
            + ", ".join(missing)
        )

    facility_df = facility_df.copy()

    # 원본의 유형구분명은 '소방서'와 '안전센터/구조대'로 되어 있으므로
    # 기관명에 '구조'가 포함된 시설은 구조대로 별도 분류합니다.
    facility_df["기관구분"] = "안전센터"

    facility_df.loc[
        facility_df["유형구분명"].astype(str).eq("소방서"),
        "기관구분",
    ] = "소방서"

    structure_mask = (
        facility_df["서ㆍ센터명"]
        .astype(str)
        .str.contains("구조", na=False)
    )
    facility_df.loc[structure_mask, "기관구분"] = "구조대"

    # EPSG:5186 → WGS84(EPSG:4326)
    from pyproj import Transformer

    transformer = Transformer.from_crs(
        "EPSG:5186",
        "EPSG:4326",
        always_xy=True,
    )

    facility_df["X좌표"] = pd.to_numeric(
        facility_df["X좌표"], errors="coerce"
    )
    facility_df["Y좌표"] = pd.to_numeric(
        facility_df["Y좌표"], errors="coerce"
    )

    facility_df = facility_df.dropna(
        subset=["X좌표", "Y좌표"]
    ).copy()

    lon, lat = transformer.transform(
        facility_df["X좌표"].to_numpy(),
        facility_df["Y좌표"].to_numpy(),
    )

    facility_df["경도"] = lon
    facility_df["위도"] = lat

    return facility_df


if FACILITY_FILE is None:
    st.warning(
        "소방시설 Excel 파일을 찾을 수 없습니다. "
        "app.py와 같은 폴더에 .xlsx 파일을 넣어주세요."
    )
else:
    try:
        st.info(f"소방시설 데이터: `{FACILITY_FILE.name}`")
        facility_df = load_facility_data(FACILITY_FILE)

        facility_fig = px.scatter_map(
            facility_df,
            lat="위도",
            lon="경도",
            color="기관구분",
            hover_name="서ㆍ센터명",
            hover_data={
                "기관구분": True,
                "위도": False,
                "경도": False,
            },
            color_discrete_map={
                "소방서": "red",
                "안전센터": "black",
                "구조대": "blue",
            },
            center={
                "lat": 37.5665,
                "lon": 126.9780,
            },
            zoom=9.8,
            map_style="open-street-map",
        )

        facility_fig.update_traces(
            marker=dict(
                size=11,
                opacity=0.9,
            ),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "기관구분: %{customdata[0]}"
                "<extra></extra>"
            ),
        )

        facility_fig.update_layout(
            height=700,
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(
                family=(
                    "Noto Sans KR, Noto Sans CJK KR, "
                    "Apple SD Gothic Neo, Malgun Gothic, sans-serif"
                ),
                size=13,
            ),
            legend=dict(
                title="기관구분",
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="left",
                x=0,
            ),
        )

        st.plotly_chart(
            facility_fig,
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": True,
            },
        )

        facility_summary = (
            facility_df["기관구분"]
            .value_counts()
            .reindex(
                ["소방서", "안전센터", "구조대"],
                fill_value=0,
            )
        )

        fcol1, fcol2, fcol3 = st.columns(3)

        with fcol1:
            st.metric("소방서", f"{facility_summary['소방서']:,}개")

        with fcol2:
            st.metric("안전센터", f"{facility_summary['안전센터']:,}개")

        with fcol3:
            st.metric("구조대", f"{facility_summary['구조대']:,}개")

        with st.expander("소방시설 위치 데이터 전체 보기"):
            facility_table = facility_df[
                ["서ㆍ센터명", "기관구분", "X좌표", "Y좌표"]
            ].copy()

            facility_table.columns = [
                "기관명",
                "기관구분",
                "EPSG:5186 X",
                "EPSG:5186 Y",
            ]

            st.dataframe(
                facility_table,
                use_container_width=True,
                hide_index=True,
            )

    except Exception as e:
        st.error("소방시설 위치 데이터를 불러오는 중 오류가 발생했습니다.")
        st.exception(e)


st.caption(
    "※ 제공된 GeoJSON의 행정동 경계를 사용합니다. "
    "출동건수가 적을수록 흰색, 많을수록 빨간색으로 표시됩니다."
)
