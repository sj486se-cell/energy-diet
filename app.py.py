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

# ==========================================
# 2. 메인 화면 - 방학/주말 자율 식단 분석 로직
# ==========================================
elif "아니요" in day_type:
    if analyze_self_btn:
        with st.spinner("AI가 입력된 식단을 분석하여 맞춤형 영양 처방전을 작성하고 있습니다..."):
            
            # 💡 핵심: LLM에게 역할을 부여하고, UI에 뿌려줄 데이터를 JSON 형식으로 요구합니다.
            prompt = f"""
            당신은 10대 청소년을 위한 전문 AI 영양사입니다. 
            사용자가 방금 먹은 식단을 분석하고, 반드시 아래의 JSON 형식으로만 답변해 주세요. 
            다른 인사말이나 설명은 절대 추가하지 마세요.
            
            분석할 식단: {user_meal}

            {{
                "status": "DANGER" | "WARNING" | "SAFE" (이 중 하나 선택),
                "summary": "영양 상태에 대한 한 줄 요약",
                "risk_scores": {{
                    "sodium": 0.0부터 1.0 사이의 숫자 (나트륨 위험도),
                    "sugar_fat": 0.0부터 1.0 사이의 숫자 (당/지방 위험도)
                }},
                "analysis_text": "왜 이 식단이 좋거나 위험한지 과학적이고 친절하게 설명 (3~4문장)",
                "solution_title": "솔루션의 멋진 제목 (예: 붓기 쫙 빼는 나트륨 디톡스)",
                "prescriptions": [
                    {{"food": "추천 식품 1", "nutrient": "핵심 성분", "effect": "기대 효과"}},
                    {{"food": "추천 식품 2", "nutrient": "핵심 성분", "effect": "기대 효과"}}
                ]
            }}
            """

            try:
                # LLM 호출
                response = model.generate_content(prompt)
                
                # 마크다운 찌꺼기(```json)를 제거하고 순수 딕셔너리로 변환
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean_text)

                st.success(f"✅ '{user_meal}'에 대한 초정밀 영양 분석이 완료되었습니다!")
                st.markdown("---")
                st.header("📊 AI 심층 영양 분석 리포트")
                
                # 1. 상태에 따른 경고창 출력
                if result["status"] == "DANGER":
                    st.error(f"🚨 **[DANGER] {result['summary']}**")
                elif result["status"] == "WARNING":
                    st.warning(f"⚠️ **[WARNING] {result['summary']}**")
                else:
                    st.success(f"✅ **[SAFE] {result['summary']}**")
                    
                # 2. 동적 프로그래스 바 (게이지)
                st.subheader("⚠️ 주요 지표")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.write("**나트륨(염분) 과다 지수**")
                    st.progress(float(result["risk_scores"]["sodium"]))
                with col_g2:
                    st.write("**당/포화지방 과다 지수**")
                    st.progress(float(result["risk_scores"]["sugar_fat"]))
                    
                # 3. AI의 상세 분석 코멘트
                st.write(result["analysis_text"])
                st.markdown("---")
                
                # 4. 동적 맞춤형 처방전 테이블
                st.subheader(f"💡 {result['solution_title']}")
                
                prescription_df = pd.DataFrame(result["prescriptions"])
                # 컬럼명 한글로 예쁘게 변경
                prescription_df.columns = ["처방 식품", "핵심 성분", "기대 효과"] 
                st.dataframe(prescription_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"AI 분석 중 오류가 발생했습니다. 다시 시도해 주세요. (에러: {e})")
