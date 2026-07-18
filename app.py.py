import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.request
import urllib.parse
import json
import re
import datetime
import time

st.set_page_config(page_title="School Balance AI", page_icon="🍱", layout="wide")

# ============================================================
# 세션 상태 초기화 (제일 중요: 기록을 담을 바구니를 맨 처음 만듭니다)
# ============================================================
if "diet_history" not in st.session_state:
    st.session_state.diet_history = []
if "meal_data" not in st.session_state:
    st.session_state.meal_data = None

# ============================================================
# ★ 본인의 NEIS API KEY 입력
# ============================================================
API_KEY = "여기에_API_KEY를_입력하세요"

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.sub-title{ color:#666666; font-size:18px; }
.food-card{ background:#F7F9FA; padding:12px; border-radius:12px; margin-bottom:8px; border-left:6px solid #2E8B57; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 제목
# ============================================================
st.markdown("<div class='main-title'>🍱 School Balance AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>실시간 학교 급식 AI 영양 분석 시스템</div>", unsafe_allow_html=True)
st.divider()

# ============================================================
# 함수 모음
# ============================================================
def search_school(keyword):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(keyword)}"
        if API_KEY and API_KEY != "여기에_API_KEY를_입력하세요": url += f"&KEY={API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data["schoolInfo"][1]["row"]
        return [{"name": r["SCHUL_NM"], "region": r["ATPT_OFCDC_SC_NM"], "edu_code": r["ATPT_OFCDC_SC_CODE"], "school_code": r["SD_SCHUL_CODE"]} for r in rows]
    except: return []

def get_meal(edu_code, school_code, meal_date):
    try:
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE={edu_code}&SD_SCHUL_CODE={school_code}&MLSV_YMD={meal_date}"
        if API_KEY and API_KEY != "여기에_API_KEY를_입력하세요": url += f"&KEY={API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        row = data["mealServiceDietInfo"][1]["row"][0]
        menu = [re.sub(r"[0-9\.\(\)]", "", food).strip() for food in row["DDISH_NM"].split("<br/>")]
        return {"menu": menu, "calorie": row["CAL_INFO"], "nutrition": row["NTR_INFO"]}
    except: return None

def parse_nutrition(text):
    nutrition = {}
    if not text: return nutrition
    for item in text.split("<br/>"):
        if ":" in item:
            name, value = item.split(":", 1)
            name = re.sub(r"\(.*?\)", "", name).strip()
            match = re.search(r"[\d.]+", value)
            nutrition[name] = float(match.group()) if match else 0
    return nutrition

def calculate_score(nutrition):
    score = 100
    if nutrition.get("단백질", 0) < 20: score -= 15
    if nutrition.get("지방", 0) > 25: score -= 10
    if nutrition.get("칼슘", 0) < 250: score -= 10
    if nutrition.get("비타민C", 0) < 30: score -= 5
    return max(score, 0)

def nutrition_chart(nutrition):
    labels, values = [], []
    for key in ["탄수화물", "단백질", "지방"]:
        if key in nutrition:
            labels.append(key)
            values.append(nutrition[key])
    df = pd.DataFrame({"영양소": labels, "섭취량": values})
    fig = px.bar(df, x="영양소", y="섭취량", text="섭취량", title="3대 영양소 분석")
    fig.update_layout(height=420)
    return fig

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("⚙️ 메뉴")
    mode = st.radio("분석 모드", ["🏫 학교 급식", "🏠 자율 식단"])
    st.divider()

    if mode == "🏫 학교 급식":
        school_keyword = st.text_input("학교 이름", placeholder="예) 서현중학교")
        
        if "search_clicked" not in st.session_state: st.session_state.search_clicked = False
        if "school_options" not in st.session_state: st.session_state.school_options = []
        if "school_data_list" not in st.session_state: st.session_state.school_data_list = []

        if st.button("🔍 학교 검색", use_container_width=True):
            if school_keyword:
                with st.spinner("학교를 검색하는 중..."):
                    school_list = search_school(school_keyword)
                    if school_list:
                        st.session_state.school_data_list = school_list
                        st.session_state.school_options = [f"{s['name']} ({s['region']})" for s in school_list]
                        st.session_state.search_clicked = True
                    else:
                        st.error("검색된 학교가 없습니다.")
                        st.session_state.search_clicked = False
            else: st.warning("학교 이름을 입력해 주세요.")

        selected_school = None
        if st.session_state.search_clicked and st.session_state.school_options:
            selected = st.selectbox("학교 선택", st.session_state.school_options)
            selected_school = st.session_state.school_data_list[st.session_state.school_options.index(selected)]

        meal_date = st.date_input("급식 날짜", datetime.date(2026, 7, 2)) # 데이터 조회를 위해 기본값 고정
        meal_btn = st.button("🍱 급식 조회", use_container_width=True)

    else:
        user_food = st.text_area("오늘 먹은 음식", height=120, placeholder="예) 불닭볶음면, 참치김밥, 콜라")
        analyze_btn = st.button("🤖 AI 분석", use_container_width=True)

# ============================================================
# 메인 화면: 학교 급식 모드
# ============================================================
if mode == "🏫 학교 급식":
    if meal_btn:
        if selected_school:
            with st.spinner("급식 정보를 불러오는 중입니다..."):
                st.session_state.meal_data = get_meal(selected_school["edu_code"], selected_school["school_code"], meal_date.strftime("%Y%m%d"))
                time.sleep(0.5)

    meal = st.session_state.meal_data
    if meal:
        st.success(f"✅ {selected_school['name']} 급식 조회 완료")
        left, right = st.columns([2, 1])
        with left:
            st.subheader("🍱 오늘의 급식")
            for food in meal["menu"]:
                st.markdown(f'<div class="food-card">🍽️ {food}</div>', unsafe_allow_html=True)
        with right:
            st.subheader("📊 기본 정보")
            st.metric("총 칼로리", meal["calorie"])
            
        nutrition = parse_nutrition(meal["nutrition"])
        score = calculate_score(nutrition)

        # ✨ 수정됨: 학교 급식을 기록에 저장하는 로직 추가!
        if meal_btn:
            today_str = meal_date.strftime("%Y-%m-%d")
            food_name = f"학교 급식 ({selected_school['name']})"
            
            # 칼로리 텍스트에서 숫자만 추출
            cal_match = re.search(r"[\d.]+", meal["calorie"])
            cal_val = float(cal_match.group()) if cal_match else 0.0
            
            new_record = {
                "날짜": today_str,
                "음식": food_name,
                "칼로리(kcal)": cal_val,
                "탄수화물(g)": nutrition.get("탄수화물", 0),
                "단백질(g)": nutrition.get("단백질", 0),
                "지방(g)": nutrition.get("지방", 0),
                "Health Score": score
            }
            # 중복 저장 방지
            if not any(item["날짜"] == today_str and item["음식"] == food_name for item in st.session_state.diet_history):
                st.session_state.diet_history.append(new_record)

        st.markdown("---")
        st.header("🤖 AI 영양 분석")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("💯 Health Score", f"{score}점")
            st.progress(score / 100)
            if score >= 90: st.success("매우 균형 잡힌 급식입니다.")
            elif score >= 80: st.info("좋은 식단입니다.")
            elif score >= 70: st.warning("약간 부족한 영양소가 있습니다.")
            else: st.error("영양 균형 개선이 필요합니다.")
        with col2:
            if len(nutrition) > 0:
                st.plotly_chart(nutrition_chart(nutrition), use_container_width=True)

        st.markdown("---")
        st.subheader("📋 AI 분석 결과")
        if score >= 90: st.success("🎉 오늘 급식은 성장기 학생에게 매우 좋은 영양 밸런스를 가지고 있습니다!")
        else: st.warning("일부 영양소가 부족할 수 있습니다. 저녁 식사나 간식으로 단백질 및 채소를 섭취해 보세요.")

# ============================================================
# 메인 화면: 자율 식단 모드
# ============================================================
elif mode == "🏠 자율 식단":
    food_db = {
        "라면": {"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15},
        "불닭볶음면": {"calorie": 550, "탄수화물": 80, "단백질": 12, "지방": 18},
        "김밥": {"calorie": 450, "탄수화물": 65, "단백질": 12, "지방": 14},
        "참치김밥": {"calorie": 520, "탄수화물": 68, "단백질": 18, "지방": 18},
        "치킨": {"calorie": 700, "탄수화물": 20, "단백질": 40, "지방": 35},
        "계란": {"calorie": 80, "탄수화물": 1, "단백질": 7, "지방": 6},
        "우유": {"calorie": 130, "탄수화물": 10, "단백질": 7, "지방": 7},
        "사과": {"calorie": 100, "탄수화물": 25, "단백질": 0, "지방": 0},
        "콜라": {"calorie": 150, "탄수화물": 40, "단백질": 0, "지방": 0}
    }

    if analyze_btn:
        if user_food.strip() == "":
            st.warning("음식을 입력해주세요.")
        else:
            with st.spinner("분석 중..."): time.sleep(1)
            foods = [f.strip() for f in user_food.split(",")]
            total = {"calorie": 0, "탄수화물": 0, "단백질": 0, "지방": 0}
            not_found = []

            for food in foods:
                found = False
                for name, data in food_db.items():
                    if name in food:
                        total["calorie"] += data["calorie"]
                        total["탄수화물"] += data["탄수화물"]
                        total["단백질"] += data["단백질"]
                        total["지방"] += data["지방"]
                        found = True
                        break
                if not found: not_found.append(food)

            score = 100
            if total["단백질"] < 20: score -= 15
            if total["지방"] > 30: score -= 15
            if total["탄수화물"] > 150: score -= 10
            score = max(score, 0)

            # ✨ 수정됨: 자율 식단을 분석 즉시 기록에 저장하는 로직
            today_str = str(datetime.date.today())
            new_record = {
                "날짜": today_str,
                "음식": user_food,
                "칼로리(kcal)": total["calorie"],
                "탄수화물(g)": total["탄수화물"],
                "단백질(g)": total["단백질"],
                "지방(g)": total["지방"],
                "Health Score": score
            }
            if not any(item["날짜"] == today_str and item["음식"] == user_food for item in st.session_state.diet_history):
                st.session_state.diet_history.append(new_record)

            st.header("🤖 AI 식단 분석 결과")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 칼로리", f"{total['calorie']} kcal")
                st.metric("탄수화물", f"{total['탄수화물']} g")
                st.metric("단백질", f"{total['단백질']} g")
                st.metric("지방", f"{total['지방']} g")
            with col2:
                st.subheader("💯 Health Score")
                st.metric("점수", f"{score}점")
                st.progress(score / 100)

            if not_found:
                st.caption("⚠️ 데이터에 없는 음식: " + ", ".join(not_found))

# ============================================================
# 나의 식단 기록 & 건강 리포트 (통합 출력)
# ============================================================
st.markdown("---")
st.header("📅 나의 식단 기록 & 주간 리포트")

if len(st.session_state.diet_history) > 0:
    history_df = pd.DataFrame(st.session_state.diet_history)
    st.subheader("📋 식단 누적 기록")
    st.dataframe(history_df, use_container_width=True)
    
    avg_score = history_df["Health Score"].mean()
    avg_calorie = history_df["칼로리(kcal)"].mean()
    
    col1, col2 = st.columns(2)
    with col1: st.metric("평균 Health Score", f"{avg_score:.1f}점")
    with col2: st.metric("평균 섭취 칼로리", f"{avg_calorie:.0f} kcal")
    
    st.subheader("📈 건강 점수 변화 추이")
    fig = px.line(history_df, x="날짜", y="Health Score", markers=True, title="Health Score 변화")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🤖 AI 주간 종합 평가")
    if avg_score >= 90: st.success("🎉 매우 훌륭한 식습관입니다! 균형 잡힌 영양 섭취를 잘 유지하고 계시네요.")
    elif avg_score >= 75: st.info("👍 좋은 식습관입니다. 점수가 낮았던 날의 식단을 참고하여 단백질과 채소를 조금만 더 보충해보세요.")
    else: st.warning("⚠️ 전반적인 식단 개선이 필요합니다. 과도한 탄수화물/지방 섭취를 줄이고 신선한 과일과 채소를 추가해 보세요.")
else:
    st.info("아직 저장된 식단 기록이 없습니다. 위에서 '학교 급식'이나 '자율 식단'을 분석하면 자동으로 기록이 쌓입니다!")
