import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="데이터 기반 입지 분석", layout="wide")

st.title("📍 학교 주변 상권 입지 분석")
st.write("공공데이터포털에서 다운로드한 상권 데이터(CSV)를 업로드하여 위치와 경쟁도를 확인하세요.")

# CSV 파일 업로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type=['csv'])

@st.cache_data
def load_data(file):
    # 인코딩 문제 발생 시 encoding='cp949' 또는 'euc-kr'로 변경
    df = pd.read_csv(file)
    cols = ['상호명', '상권업종소분류명', '위도', '경도']
    return df[cols].dropna()

if uploaded_file:
    df = load_data(uploaded_file)
    
    st.sidebar.header("분석 설정")
    # 업종 목록을 추출하여 셀렉트박스로 제공
    categories = sorted(df['상권업종소분류명'].unique())
    selected_category = st.sidebar.selectbox("상권업종소분류명 선택", categories)
    
    # 선택한 업종 데이터 필터링
    filtered_df = df[df['상권업종소분류명'] == selected_category]
    
    # 레드/블루오션 분석 (전체 상권 내 해당 업종의 빈도 순위 기반)
    category_counts = df['상권업종소분류명'].value_counts()
    selected_count = category_counts.get(selected_category, 0)
    
    # 상위 몇 %에 해당하는지 백분위 계산 (낮을수록 점포 수가 많아 경쟁이 치열함)
    rank_pct = category_counts.rank(pct=True, ascending=False)[selected_category] * 100
    
    st.subheader(f"📊 '{selected_category}' 입지 경쟁도 분석")
    col1, col2 = st.columns(2)
    with col1:
        # 에러 우회를 위해 metric 대신 markdown 사용
        st.markdown(f"### 🏪 해당 업종 점포 수\n**{selected_count}개**")
    with col2:
        if rank_pct <= 20:
            st.error(f"🚨 **레드오션 (상위 {rank_pct:.1f}%)**: 점포가 포화 상태로 경쟁이 매우 치열합니다.")
        elif rank_pct <= 60:
            st.warning(f"⚠️ **옐로우오션 (상위 {rank_pct:.1f}%)**: 중간 수준의 경쟁 강도를 보입니다.")
        else:
            st.success(f"🌊 **블루오션 (상위 {rank_pct:.1f}%)**: 점포 수가 적어 진입해볼 만한 틈새시장입니다.")
    
    st.subheader("🗺️ 점포 위치 시각화")
    if not filtered_df.empty:
        # 지도의 중심 좌표를 필터링된 점포들의 평균 위치로 설정
        center_lat = filtered_df['위도'].mean()
        center_lon = filtered_df['경도'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
        
        # 렌더링 성능을 위해 마커 표시 제한 (최대 1000개)
        for idx, row in filtered_df.head(1000).iterrows():
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=row['상호명'],
                tooltip=row['상호명'],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            
        st_folium(m, width=800, height=500)
    else:
        st.info("해당 업종의 점포가 지도 영역 내에 존재하지 않습니다.")
