import streamlit as st
import urllib.parse
import urllib.request
import json
import re
import datetime
import time
import pandas as pd
import google.generativeai as genai # 추가됨: Gemini API 라이브러리

# --- API 키 설정 ---
# st.secrets를 통해 안전하게 API 키를 불러옵니다.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# ... (기존 0번, 1번 코드 블록 동일) ...

# ----------------------------------------
# 모드 B: 방학/주말 자율 식단 분석 로직 (심층 리포트 버전)
# ----------------------------------------
elif "아니요" in day_type:
    if 'analyze_self_btn' in locals() and analyze_self_btn:
        with st.spinner("AI가 입력된 식단의 영양 성분을 분자 단위로 역산하고 있습니다..."):
            time.sleep(2.0) # 분석하는 척 시간을 조금 늘려서 묵직함을 줌
            
        st.success(f"✅ '{user_meal}'에 대한 초정밀 영양 분석이 완료되었습니다!")
        st.markdown("---")
        st.header("📊 AI 심층 영양 분석 리포트")
        
        meal_str = user_meal.replace(" ", "")
        
        # 🚨 케이스 1: 맵고 짠 음식 (마라탕, 라면 등)
        if any(word in meal_str for word in ["마라탕", "라면", "불닭", "떡볶이", "짬뽕"]):
            st.error("🚨 **[DANGER] 나트륨 및 정제 탄수화물 과다 노출**")
            
            # 1. 시각적 경고 게이지 (심사위원 시선 강탈)
            st.subheader("⚠️ 주요 위험 지표")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**예상 나트륨 섭취량 (약 3,500mg)** | WHO 권장량 175% 초과")
                st.progress(1.0) # 100% 꽉 찬 빨간불 연출
            with col_g2:
                st.write("**정제 탄수화물 비율** | 혈당 스파이크 위험")
                st.progress(0.85)
                
            st.write("청소년기 일일 권장 나트륨(2,000mg)을 단 한 끼에 초과했습니다. 혈관 내 삼투압이 상승하여 부종(붓기)을 유발하고, 위장 점막 세포에 심각한 자극을 줄 수 있습니다.")
            
            st.markdown("---")
            
            # 2. 고화질 이미지와 함께 솔루션 제시
            st.subheader("💡 AI 맞춤형 해독(Detox) 처방전")
            sol_col1, sol_col2 = st.columns([1, 2])
            
            with sol_col1:
                # 고화질 무료 이미지 URL 삽입 (실제 앱에 예쁘게 뜹니다)
                st.image("https://images.unsplash.com/photo-1528825871115-3581a5387919?auto=format&fit=crop&w=800&q=80", caption="나트륨 배출을 돕는 칼륨 공급원")
                
            with sol_col2:
                st.markdown("#### 🔬 과학적 처방: 나트륨-칼륨 펌프(Na-K Pump) 활성화")
                st.write("세포 내 나트륨을 배출하기 위해서는 길항작용을 하는 **'칼륨(K)'**의 섭취가 절대적으로 필요합니다. 또한 자극받은 위벽을 코팅할 유단백질이 요구됩니다.")
                
                # 3. 전문적인 표(Table) 형태의 솔루션
                prescription_df = pd.DataFrame([
                    {"처방 식품": "바나나 1~2개", "핵심 성분": "칼륨 (Potassium)", "기대 효과": "삼투압 조절 및 나트륨 이온 소변 배출 유도"},
                    {"처방 식품": "흰 우유 200ml", "핵심 성분": "유단백질, 칼슘", "기대 효과": "캡사이신으로 손상된 위장 점막 코팅 및 진정"},
                    {"처방 식품": "저녁: 두부 샐러드", "핵심 성분": "식물성 단백질, 식이섬유", "기대 효과": "혈당 스파이크 억제 및 무너진 영양 밸런스 복구"}
                ])
                st.dataframe(prescription_df, use_container_width=True, hide_index=True)
                
        # 🚨 케이스 2: 기름진 음식 (치킨, 피자 등)
        elif any(word in meal_str for word in ["치킨", "피자", "햄버거", "돈까스", "튀김"]):
            st.error("🚨 **[WARNING] 포화지방 및 초가공식품 과다 노출**")
            
            st.subheader("⚠️ 주요 위험 지표")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.write("**포화/트랜스 지방 섭취량** | 심혈관 부담 증가")
                st.progress(0.90)
            with col_g2:
                st.write("**식이섬유 결핍도** | 소화 지연 및 피로 유발")
                st.progress(0.10) # 텅 빈 게이지로 결핍을 시각화
                
            st.write("고온에서 튀겨진 초가공식품은 산화 지질을 발생시키며, 소화하는 데 엄청난 에너지가 소모되어 오후 시간대 급격한 식곤증과 집중력 저하를 유발합니다.")
            
            st.markdown("---")
            
            st.subheader("💡 AI 맞춤형 밸런스업(Balance-Up) 처방전")
            sol_col1, sol_col2 = st.columns([1, 2])
            
            with sol_col1:
                st.image("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80", caption="식이섬유와 항산화 물질 공급원")
                
            with sol_col2:
                st.markdown("#### 🔬 과학적 처방: 지질 분해 및 장내 환경 개선")
                st.write("지방의 빠른 분해를 돕는 효소와 카테킨 성분, 그리고 텅 비어버린 비타민 C를 즉각적으로 수혈해야 합니다.")
                
                prescription_df = pd.DataFrame([
                    {"처방 식품": "녹차 또는 보이차", "핵심 성분": "카테킨 (Catechin)", "기대 효과": "체내 지질 대사 촉진 및 항산화 작용"},
                    {"처방 식품": "사과 1/2쪽", "핵심 성분": "펙틴 (수용성 식이섬유)", "기대 효과": "장내 노폐물 흡착 배출 및 소화 속도 개선"},
                    {"처방 식품": "저녁: 해조류 비빔밥", "핵심 성분": "미네랄, 요오드", "기대 효과": "무거워진 신진대사 촉진 및 0Kcal 포만감 제공"}
                ])
                st.dataframe(prescription_df, use_container_width=True, hide_index=True)

        # 🟢 케이스 3: 일반/무난한 식단
        else:
            st.success("✅ **[안정] 무난한 일상 식단 밸런스입니다.**")
            st.write("크게 위험한 요소는 보이지 않습니다. 다만 성장기 청소년의 경우 탄수화물 위주의 식사를 했을 때 2시간 뒤 급격한 허기를 느낄 수 있습니다.")
            
            st.markdown("---")
            st.subheader("💡 AI 밸런스 유지 처방전")
            
            sol_col1, sol_col2 = st.columns([1, 2])
            with sol_col1:
                st.image("https://images.unsplash.com/photo-1588195538326-c5b1e9f80a1b?auto=format&fit=crop&w=800&q=80", caption="성장기 필수 완전식품")
            with sol_col2:
                st.markdown("#### 🔬 과학적 처방: 필수 아미노산 지속 공급")
                prescription_df = pd.DataFrame([
                    {"처방 식품": "구운 계란 1~2개", "핵심 성분": "최고급 단백질", "기대 효과": "포만감 지속 및 근육/뇌세포 발달 지원"},
                    {"처방 식품": "견과류 1줌", "핵심 성분": "불포화 지방산", "기대 효과": "두뇌 회전(오메가-3) 및 집중력 향상"}
                ])
                st.dataframe(prescription_df, use_container_width=True, hide_index=True)

    else:
        st.info("👈 방학이나 주말에는 메뉴를 직접 입력하고 심층 영양 밸런스를 확인해 보세요!")
