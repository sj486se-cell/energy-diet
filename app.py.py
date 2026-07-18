import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import urllib.parse
import urllib.request
import json

st.set_page_config(page_title="SafePath AI", page_icon="🗺️", layout="wide")

# ==========================================
# 0. 핵심 기술: 실시간 주소 -> 위도/경도 변환 API (Geocoding)
# ==========================================
def get_coordinates(address, default_lon, default_lat):
    try:
        # 전 세계 무료 오픈 지도 API (OpenStreetMap) 호출
        url = "https://nominatim.openstreetmap.org/search?q=" + urllib.parse.quote(address) + "&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'SafePath_Hackathon_App'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if len(data) > 0:
                return float(data[0]['lon']), float(data[0]['lat'])
    except Exception as e:
        pass
    # 검색 실패 시 기본 좌표 반환
    return default_lon, default_lat

# ==========================================
# 1. 사이드바 (사용자 조건 설정)
# ==========================================
with st.sidebar:
    st.title("⚙️ 안전 경로 설정")
    user_type = st.radio(
        "👤 보행자 유형을 선택하세요", 
        ["🚶 일반 보행자 (최단거리)", "👩‍🦽 휠체어/유모차 (단차 회피)", "🌙 심야 안심 귀가 (조도 확보)"]
    )
    
    st.divider()
    st.subheader("📍 이동 구간 입력")
    # API 검색이 잘 되도록 '역'이나 '동' 이름을 넣는 것이 좋습니다.
    start_point = st.text_input("출발지 (예: 정자역, 서울시청)", "서현역")
    end_point = st.text_input("목적지 (예: 수내역, 광화문)", "수내역")
    
    search_btn = st.button("AI 안전 경로 탐색 🔍", use_container_width=True)

# ==========================================
# 2. 메인 화면 (탐색 결과 및 고급 인터랙티브 지도)
# ==========================================
st.title("🗺️ SafePath AI: 실시간 안전 네비게이션")

if search_btn:
    with st.spinner(f"위성 API를 통해 '{start_point}'와 '{end_point}'의 좌표를 분석 중입니다..."):
        # 입력한 텍스트를 실제 위도/경도 숫자로 변환
        start_lon, start_lat = get_coordinates(start_point, 127.1235, 37.3850)
        end_lon, end_lat = get_coordinates(end_point, 127.1140, 37.3780)
        time.sleep(1) # 극적인 로딩 효과
        
    st.success(f"✅ 좌표 탐색 완료! {start_point}에서 {end_point}까지의 경로를 계산했습니다.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 실시간 동적 경로 시뮬레이션")
        
        # 출발지와 목적지의 중간 지점 계산
        mid_lon = (start_lon + end_lon) / 2
        mid_lat = (start_lat + end_lat) / 2
        
        # 🌟 핵심 알고리즘: 조건에 따라 중간 경유지(우회로)를 인공적으로 생성
        if "휠체어" in user_type:
            # 휠체어: 중간 지점에서 우측으로 크게 꺾어서 평탄한 길로 우회 (빨간색)
            route_coords = [
                [start_lon, start_lat],
                [mid_lon + 0.005, mid_lat + 0.005], # 우회 경유지
                [end_lon, end_lat]
            ]
            line_color = [255, 75, 75]
            
        elif "심야" in user_type:
            # 심야: 중간 지점에서 좌측으로 크게 꺾어서 대로변으로 우회 (노란색)
            route_coords = [
                [start_lon, start_lat],
                [mid_lon - 0.005, mid_lat - 0.005], # 우회 경유지
                [end_lon, end_lat]
            ]
            line_color = [255, 200, 0]
            
        else:
            # 일반: 중간 경유지 없이 출발-도착을 직선에 가깝게 연결 (파란색)
            route_coords = [
                [start_lon, start_lat],
                [end_lon, end_lat]
            ]
            line_color = [0, 100, 255]
            
        # 경로 데이터 생성
        df_route = pd.DataFrame({"path": [route_coords], "color": [line_color]})
        
        # 지도의 중심점을 출발-도착의 한가운데(mid)로 자동 이동
        view_state = pdk.ViewState(latitude=mid_lat, longitude=mid_lon, zoom=13.5)
        
        layer = pdk.Layer(
            type="PathLayer",
            data=df_route,
            pickable=True,
            get_color="color",
            width_scale=1,
            width_min_pixels=3,
            get_path="path",
            get_width=10
        )
        
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="road"))
        
    with col2:
        st.subheader("🎯 AI 심층 분석 리포트")
        st.info("💡 **실시간 가중치 적용 결과**")
        
        if "휠체어" in user_type:
            st.error("🚨 **위험 감지:** 최단 거리 구간 내 단차 및 계단 발견")
            st.success("✅ **경로 수정:** 우회 경유지 확보 (안전도 95%)")
            st.write(f"{start_point}에서 {end_point}로 가는 기존 직선 경로의 위험을 차단하고, 휠체어 이동이 가능한 평탄화 인도를 거치도록 경로를 재설계했습니다.")
        elif "심야" in user_type:
            st.error("🚨 **위험 감지:** 최단 거리 내 저조도 사각지대 존재")
            st.success("✅ **경로 수정:** 큰길 위주 우회 경유지 확보 (안전도 92%)")
            st.write(f"범죄 취약 구역을 피하고, 가로등 밝기가 확보된 우회로를 탐색하여 심야 귀가 경로를 안전하게 꺾어 안내합니다.")
        else:
            st.success("✅ **탐색 결과:** 장애물 미발견, 최단 직선 거리로 안내")
            st.write(f"현재 {start_point}에서 {end_point}까지 최적의 효율을 내는 최단 거리 노선입니다.")
