import streamlit as st
import pandas as pd
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", layout="wide")

# ============================================================
# API 및 핵심 함수 (동일)
# ============================================================
API_KEY = "여기에_API_KEY를_입력하세요"

# [함수 생략: 이전과 동일하게 작성되어 있다고 가정합니다]
# search_school, get_meal, parse_nutrition, calculate_score, get_dinner_prescription, get_activity_prescription, generate_ai_report_stream 함수들...

# (위의 함수들이 이 위치에 그대로 있어야 합니다!)

# ============================================================
# 메인 화면 로직 (데이터 바인딩 확실하게)
# ============================================================
st.title("🍱 School Balance AI")

# 사이드바 데이터 입력
with st.sidebar:
    user_weight = st.number_input("몸무게 (kg)", value=50.0)
    leftover_rate = st.slider("잔반 비율 (%)", 0, 100, 0)
    mode = st.radio("모드", ["🏫 학교 급식", "🏠 자율 식단"])
    
    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교 검색", "서현중학교")
        meal_date = st.date_input("날짜", datetime.date(2026, 7, 2))
    else:
        user_food = st.text_area("먹은 음식", "불닭볶음면, 참치김밥, 콜라")
    
    run_btn = st.button("🚀 통합 분석 시작", type="primary")

# 버튼을 눌렀을 때만 로직 실행 후 세션에 저장
if run_btn:
    with st.spinner("분석 중..."):
        if mode == "🏫 학교 급식":
            schools = search_school(school_keyword)
            if schools:
                meal = get_meal(schools[0]["edu_code"], schools[0]["school_code"], meal_date.strftime("%Y%m%d"))
                if meal:
                    st.session_state.result = {
                        "type": "급식", "name": schools[0]["name"], 
                        "cal": float(re.search(r"[\d.]+", meal["calorie"]).group()) if re.search(r"[\d.]+", meal["calorie"]) else 0,
                        "nutri": parse_nutrition(meal["nutrition"]), "left": leftover_rate
                    }
                else: st.error("급식 정보 없음")
        else:
            # 자율 식단 데이터 저장
            st.session_state.result = {
                "type": "자율", "name": "자율 식단", "cal": 700, 
                "nutri": {"탄수화물": 80, "단백질": 20, "지방": 30}, "left": leftover_rate
            }

# 데이터가 저장되어 있다면 항상 화면에 표시
if "result" in st.session_state:
    res = st.session_state.result
    st.success(f"{res['name']} 분석 완료")
    st.metric("칼로리", f"{res['cal']} kcal")
    
    if st.button("✨ 상세 처방전 보기"):
        st.write("---")
        # 여기서 처방전 로직이 실행됩니다.
        st.write("상세 리포트 출력 및 열역학 처방전 생성...")
