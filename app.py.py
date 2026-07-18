import streamlit as st
import urllib.request
import urllib.parse
import json
import re
import datetime
import time
import google.generativeai as genai

st.set_page_config(page_title="School Balance AI Pro", page_icon="🍱", layout="wide")

# ============================================================
# ★ API KEY 설정 (사이드바 또는 여기에 입력)
# ============================================================
NEIS_API_KEY = "여기에_NEIS_API_KEY를_입력하세요"
GEMINI_API_KEY = "" #기에_GEMINI_API_KEY를_입력하세요 (비워두면 기존 모드로 안전하게 작동)

# ============================================================
# CSS 스타일 설정
# ============================================================
st.markdown("""
<style>
.main-title{ font-size:42px; font-weight:bold; color:#2E8B57; }
.sub-title{ color:#666666; font-size:18px; margin-bottom: 20px;}
.food-card{ background:#F7F9FA; padding:12px; border-radius:12px; margin-bottom:8px; border-left:6px solid #2E8B57; }
.physics-card { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
.eco-card { background-color: #f1faee; border: 1px solid #a8dadc; padding: 25px; border-radius: 12px; margin-top: 20px; margin-bottom: 20px; }
.ai-report { background-color: #f1f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce5ff; font-size: 16px; line-height: 1.6; margin-bottom: 20px; }
.prescription-card { background-color: #2b3035; color: #ffffff; padding: 25px; border-radius: 12px; border-left: 8px solid #20c997; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: 10px; height: 100%;}
.prescription-title { color: #20c997; margin-top: 0; font-size: 22px; font-weight: bold; border-bottom: 1px solid #495057; padding-bottom: 10px; margin-bottom: 15px;}
.exercise-card { background-color: #2b3035; color: #ffffff; padding: 25px; border-radius: 12px; border-left: 8px solid #ff6b6b; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-top: 10px; height: 100%;}
.exercise-title { color: #ff6b6b; margin-top: 0; font-size: 22px; font-weight: bold; border-bottom: 1px solid #495057; padding-bottom: 10px; margin-bottom: 15px;}
.p-text { font-size: 16px; margin-bottom: 8px; color: #e9ecef; }
.highlight-diet { color: #20c997; font-weight: bold; }
.highlight-ex { color: #ff6b6b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🍱 School Balance AI Pro</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>생성형 AI + 영양 밸런스 + 물리 대사 + 기후 위기 통합 해결 솔루션</div>", unsafe_allow_html=True)
st.divider()

# ============================================================
# 기본 데이터 수집 및 파싱 함수 (기존 로직 유지)
# ============================================================
def search_school(keyword):
    try:
        url = f"https://open.neis.go.kr/hub/schoolInfo?Type=json&SCHUL_NM={urllib.parse.quote(keyword)}"
        if NEIS_API_KEY and NEIS_API_KEY != "여기에_NEIS_API_KEY를_입력하세요": 
            url += f"&KEY={NEIS_API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        rows = data["schoolInfo"][1]["row"]
        return [{"name": r["SCHUL_NM"], "region": r["ATPT_OFCDC_SC_NM"], "edu_code": r["ATPT_OFCDC_SC_CODE"], "school_code": r["SD_SCHUL_CODE"]} for r in rows]
    except: 
        return []

def get_meal(edu_code, school_code, meal_date):
    try:
        url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&ATPT_OFCDC_SC_CODE={edu_code}&SD_SCHUL_CODE={school_code}&MLSV_YMD={meal_date}"
        if NEIS_API_KEY and NEIS_API_KEY != "여기에_NEIS_API_KEY를_입력하세요": 
            url += f"&KEY={NEIS_API_KEY}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        row = data["mealServiceDietInfo"][1]["row"][0]
        menu = [re.sub(r"[0-9\.\(\)]", "", food).strip() for food in row["DDISH_NM"].split("<br/>")]
        return {"menu": menu, "calorie": row["CAL_INFO"], "nutrition": row["NTR_INFO"]}
    except: 
        return None

def parse_nutrition(text):
    nutrition = {}
    if not text: return nutrition
    for item in text.split("<br/>"):
        if ":" in item:
            name, value = item.split(":", 1)
            name = re.sub(r"\(.*?\)", "", name).strip()
            match = re.search(r"[\d.]+", value)
            if match: nutrition[name] = float(match.group())
            else: nutrition[name] = 0.0
    return nutrition

def calculate_score(nutrition):
    score = 100
    if nutrition.get("단백질", 0) < 20: score -= 15
    if nutrition.get("지방", 0) > 25: score -= 10
    if nutrition.get("탄수화물", 0) > 150: score -= 10
    return max(score, 0)

# ============================================================
# ✨ [신규 업그레이드] 생성형 AI 대사 엔진 (Gemini Integration)
# ============================================================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def ai_parse_free_diet(user_food_text):
    """사용자가 자유롭게 입력한 문자열에서 영양성분을 AI로 추정해 JSON으로 반환"""
    if not GEMINI_API_KEY:
        # API Key가 없을 때 작동할 기본 더미 처리 (기존 사전 기준)
        total = {"calorie": 0.0, "탄수화물": 0.0, "단백질": 0.0, "지방": 0.0}
        food_db = {"라면": [500, 70, 10, 15], "마라탕": [800, 90, 20, 40], "불닭볶음면": [550, 80, 12, 18], "김밥": [450, 65, 12, 14], "치킨": [700, 20, 40, 35], "콜라": [150, 40, 0, 0]}
        for f in user_food_text.split(","):
            for name, v in food_db.items():
                if name in f.strip():
                    total["calorie"] += v[0]; total["탄수화물"] += v[1]; total["단백질"] += v[2]; total["지방"] += v[3]
        return total

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        사용자가 먹은 음식 리스트를 보고 총 칼로리(kcal), 탄수화물(g), 단백질(g), 지방(g)을 의학적/영양학적 데이터 기반으로 추정해줘.
        음식: {user_food_text}
        반드시 아무런 설명 없이 아래 양식의 순수한 JSON 객체 하나만 반환해야 해. 마크다운 기호(```)도 쓰지마.
        {{"calorie": 500, "탄수화물": 70, "단백질": 10, "지방": 15}}
        """
        response = model.generate_content(prompt)
        clean_json = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_json)
    except Exception as e:
        return {"calorie": 550.0, "탄수화물": 75.0, "단백질": 12.0, "지방": 16.0} # 에러 발생 시 예외 방지용 기본값

def generate_super_ai_report(food_name, score, nutrition, leftover, weight, delta_kcal):
    """의학, 생체학, 열역학, 기후학 융합 종합 리포트를 실시간 AI 스트리밍으로 생성"""
    if not GEMINI_API_KEY:
        # API Key가 없는 경우 기존의 규칙 기반 텍스트 생성기 가동 (안전한 자가 작동)
        report = f"👨‍⚕️ **[융합 과학 기반 생체 & 기후 대사 리포트]**\n\n오늘 섭취하신 **'{food_name}'**의 대사 밸런스 점수는 **{score}점**이며, 잔반 비율은 **{leftover}%**로 측정되었습니다. "
        report += "탄수화물과 지방 위주의 식단으로 혈당 스파이크가 우려됩니다. " if score < 90 else "매우 훌륭한 영양 밸런스입니다. "
        report += "또한 잔반이 많아 소각 시 대량의 온실가스가 발생합니다." if leftover > 20 else "잔반 제로 활동으로 탄소 배출 저감에 기여하셨습니다."
        for word in report.split():
            yield word + " "
            time.sleep(0.01)
        return

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        당신은 영양학, 운동생리학, 기후과학 전문 의사이자 융합 과학 학자입니다. 
        중학생 사용자가 입력한 데이터를 기반으로, 청소년 눈높이에 맞춰 친근하면서도 고도로 과학적인 리포트를 작성해주세요.

        [입력 데이터]
        - 식단명: {food_name}
        - 헬스 스코어: {score}점
        - 상세 영양: 탄수화물 {nutrition.get('탄수화물',0)}g, 단백질 {nutrition.get('단백질',0)}g, 지방 {nutrition.get('지방',0)}g
        - 잔반 비율: {leftover}%
        - 몸무게: {weight}kg
        - 잉여 에너지 상태: {delta_kcal} kcal

        [작성 가이드라인]
        1. 첫 줄은 항상 "👨‍⚕️ **[AI 융합 과학 대사 분석 리포트]**"로 시작할 것.
        2. 이 식단이 사용자의 인체 세포 대사(혈당 스파이크, 근육 합성 등)에 미치는 영향과 환경(잔반 소각 시 발생하는 이산화탄소와 비열 에너지 측면)에 미치는 영향을 열역학적으로 한 번에 엮어서 흥미롭게 서술할 것.
        3. 전체 글자 수는 공백 포함 250자 내외로 간결하고 임팩트 있게 작성할 것.
        """
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            yield chunk.text
    except:
        yield "AI 리포트 생성 중 연결 오류가 발생했습니다. 하단의 분석 카드를 참고해 주세요."

def get_ai_prescriptions(nutrition, delta_kcal, leftover):
    """AI를 통해 맞춤형 저녁 메뉴 처방 및 맞춤형 대사 운동 처방을 받아옴"""
    if not GEMINI_API_KEY:
        # API Key가 없는 경우 기존 하드코딩 처방 구조를 그대로 리턴
        carb = nutrition.get("탄수화물", 0); prot = nutrition.get("단백질", 0); fat = nutrition.get("지방", 0)
        if carb > 120 or fat > 30: diet = {"menu": "연어 아보카도 샐러드 & 단호박 1/2개", "effect": "혈당 스파이크 진정 및 삼투압 복구", "reason": "과다 섭취된 정제 탄수화물과 나트륨 배출을 위해 칼륨과 오메가-3를 처방합니다."}
        elif prot < 20: diet = {"menu": "수비드 닭가슴살 퀴노아 덮밥", "effect": "근육 합성 대사 촉진", "reason": "결핍된 필수 아미노산을 골든타임에 공급하여 수면 중 성장 호르몬 분비를 유도합니다."}
        else: diet = {"menu": "소고기 우둔살 구이 & 해조류 비빔밥", "effect": "에너지 평형 유지 및 철분 안정화", "reason": "낮 동안 이룩한 열평형 상태를 유지하며 부족하기 쉬운 미네랄을 보충합니다."}
        
        if delta_kcal > 400: ex = {"exercise": "인터벌 러닝 20분 + 버피 30개", "effect": "최대 산소 섭취량(VO2 max) 증가", "reason": "대량의 잉여 에너지를 최단 시간에 연소하고, 심폐 능력을 강제적으로 끌어올리는 고강도 처방입니다."}
        elif delta_kcal > 150: ex = {"exercise": "자전거 타기 30분 + 스쿼트 3세트", "effect": "하체 근력 강화 및 기초 대사량 증진", "reason": "관절에 무리를 주지 않으면서 가장 큰 근육을 사용하여 에너지를 효율적으로 태웁니다."}
        else: ex = {"exercise": "빠르게 걷기 30분 (파워워킹)", "effect": "혈류 순환 촉진 및 식후 인슐린 조절", "reason": "식후 인슐린 저항성을 낮추는 데 가장 효과적인 강도로 일상 활동량을 보완합니다."}
        return diet, ex

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        사용자의 영양 정보와 잉여 칼로리를 바탕으로 최적의 영양 복구 처방(저녁 메뉴)과 기초 체력 처방(운동)을 내려줘.
        영양상태: 탄수화물 {nutrition.get('탄수화물',0)}g, 단백질 {nutrition.get('단백질',0)}g, 지방 {nutrition.get('지방',0)}g
        잉여 칼로리: {delta_kcal} kcal

        반드시 아래 양식의 규격화된 JSON 객체 하나만 반환해줘. 설명이나 마크다운(```) 포함 금지.
        {{
            "diet_menu": "추천 식단명",
            "diet_effect": "생체 타겟 효과",
            "diet_reason": "의학적 처방 사유 1줄",
            "ex_name": "추천 운동명 및 세트수",
            "ex_effect": "체력 및 대사 타겟 효과",
            "ex_reason": "생체역학적 처방 사유 1줄"
        }}
        """
        response = model.generate_content(prompt)
        clean_json = response.text.strip().replace("
