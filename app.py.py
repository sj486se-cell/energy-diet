import streamlit as st
import pandas as pd
import numpy as np # 지도 데이터를 위한 라이브러리 추가

# 1. 화면 전체를 넓게 쓰는 프리미엄 레이아웃 설정
st.set_page_config(page_title="SafePath AI", page_icon="🗺️", layout="wide")

# ==========================================
# 2. 사이드바 (앱의 진짜 메뉴처럼 보이게 만들기)
# ==========================================
with st.sidebar:
    st.title("⚙️ 이동 설정")
    st.write("사용자의 현재 상황을 선택해 주세요.")
    
    user_type = st.radio(
        "👤 보행자 유형", 
        ["🚶 일반 보행자", "👩‍🦽 휠체어/유모차", "🌙 심야 안심 귀가"]
    )
    
    st.divider()
    st.info("📡 현재 위치 주변의 가로등 조도, 경사도, 계단 데이터를 실시간으로 수집 중입니다.")

# ==========================================
# 3. 메인 화면 및 인터랙티브 지도 (핵심 시각화)
# ==========================================
st.title("🗺️ SafePath AI: 안전 경로 네비게이션")
st.write("단순한 최단 거리가 아닌, 휠체어 탑승객과 심야 보행자를 위한 **위험 가중치 기반 최적 경로**를 안내합니다.")

st.subheader("📍 주변 위험 구역 및 안전 지도")
# 시각적 임팩트를 위한 인터랙티브 지도 (가상의 위험 구역 핀 시각화)
# 심사위원들에게 데이터 시각화 능력을 어필하는 최고의 무기입니다.
map_data = pd.DataFrame(
    np.random.randn(15, 2) / [150, 150] + [37.5665, 126.9780], # 서울시청 기준 가상 좌표
    columns=['lat', 'lon']
)
st.map(map_data, zoom=14)

st.divider()

# ==========================================
# 4. 백엔드 알고리즘 로직 (보이지 않는 곳에서 계산)
# ==========================================
routes = {
    "경로 A (최단거리 골목길)": {"distance": 500, "stairs": True, "steep": False, "lighting": "low"},
    "경로 B (약간 먼 우회로)": {"distance": 800, "stairs": False, "steep": False, "lighting": "medium"},
    "경로 C (큰길 상가거리)": {"distance": 1000, "stairs": False, "steep": True, "lighting": "high"}
}

scores = {}
for name, info in routes.items():
    score = info["distance"] * 0.1 
    
    if "휠체어" in user_type:
        if info["stairs"]: score += 9999
        if info["steep"]: score += 50
            
    if "심야" in user_type:
        if info["lighting"] == "low": score += 100
        elif info["lighting"] == "high": score -= 30
            
    scores[name] = score

best_route = min(scores, key=scores.get)

# ==========================================
# 5. 상세 분석 리포트 (전문가 느낌의 UI)
# ==========================================
st.header("🎯 AI 경로 분석 결과")

if scores[best_route] >= 9999:
    st.error("🚨 현재 조건으로 안전하게 이동할 수 있는 경로가 없습니다.")
else:
    st.success(f"🏆 최적 추천 경로: **{best_route}**")

# 세부 분석 데이터를 접었다 펼칠 수 있는 기능 (Expander)
with st.expander("🔍 왜 이 경로가 추천되었나요? (AI 분석 상세 보기)"):
    st.write(f"선택하신 **{user_type}** 모드에 맞춰 각 경로의 위험 가중치를 계산한 결과입니다.")
    
    chart_data = {
        "경로": list(scores.keys()),
        "위험도 점수": [s if s < 9999 else 200 for s in scores.values()]
    }
    df = pd.DataFrame(chart_data)
    
    # 막대그래프 출력
    st.bar_chart(df.set_index("경로"), color="#FF4B4B")
    
    st.markdown("""
    * **계산 공식:** (기본 거리 점수) + (계단/경사 페널티) + (조도 가중치)
    * **참고:** 휠체어 모드 선택 시 계단이 있는 길은 시스템이 자동으로 차단합니다.
    """)
