import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# --- 웹 페이지 설정 ---
st.set_page_config(page_title="소비기한 시뮬레이터 v3 (레이아웃 개선)", layout="centered")

st.title("🍳 맞춤형 식품 소비기한 시뮬레이터 (v3 - Layout Fix)")
st.write(
"사용자 피드백과 학술 논문 데이터를 반영하여 한층 더 정교해진 시뮬레이터입니다.
⚠️주의: 몇 가지 변수에만 의존한 '시뮬레이터' 이기 때문에, 실제 상황과 완벽히 일치하지 않을 수 있습니다."
)

# --- 사이드바: 설정 메뉴 ---
st.sidebar.header("⚙️ 설정 및 환경 선택")

# [해결책 1] 가장 먼저 골라야 할 "음식 종류"를 사이드바 맨 위로 올렸습니다!
food_type = st.sidebar.selectbox(
    "🍔 음식 종류를 선택하세요",
    (
        "🥩 육류 / 생선 (신선식품)",
        "🥗 채소 / 샐러드",
        "🍞 베이커리 (빵류)",
        "🥚 계란 (식용란)",
        "🥛 유제품 (우유 및 치즈)",
    ),
)

st.sidebar.markdown("---")  # 구분선

# 보관 상태 프리셋 선택 기능
storage_preset = st.sidebar.selectbox(
    "💾 보관 장소를 선택하세요 (프리셋)",
    (
        "사용자 직접 설정",
        "❄️ 냉동실 (-18℃ / 습도 40%)",
        "🥬 김치냉장고 (-1℃ / 습도 85%)",
        "🍎 일반 냉장고 (4℃ / 습도 70%)",
        "🏠 실온 보관 (22℃ / 습도 60%)",
        "☀️ 무더운 여름철 실외 (32℃ / 습도 80%)",
    ),
)

# 프리셋 선택에 따른 온도/습도 기본값 설정
default_temp = 25
default_humidity = 80

if "냉동실" in storage_preset:
    default_temp = -18
    default_humidity = 40
elif "김치냉장고" in storage_preset:
    default_temp = -1
    default_humidity = 85
elif "일반 냉장고" in storage_preset:
    default_temp = 4
    default_humidity = 70
elif "실온" in storage_preset:
    default_temp = 22
    default_humidity = 60
elif "여름철" in storage_preset:
    default_temp = 32
    default_humidity = 80

# 사용자가 프리셋 선택 후에도 슬라이더로 미세조정 가능하게 연동
temp = st.sidebar.slider(
    "보관 온도 (℃)", min_value=-20, max_value=45, value=default_temp, step=1
)
humidity = st.sidebar.slider(
    "보관 습도 (%)", min_value=10, max_value=100, value=default_humidity, step=5
)
simulation_hours = st.sidebar.slider(
    "시뮬레이션 시간 (Hours)", min_value=24, max_value=800, value=300, step=12
)

# [해결책 2] 사이드바 맨 밑에 여유 공간(150픽셀 높이의 빈 박스)을 강제로 밀어 넣어
# 화면이 작은 노트북에서도 스크롤이 부드럽게 되도록 여백을 만들었습니다.
st.sidebar.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)


# --- 백엔드 시뮬레이션 로직 ---
K = 10**9  # 최대 환경 수용력
spoilage_threshold = 10**7  # 일반적인 부패 기준 (1천만 마리)

# 식품별 초기 세균 수(N0) 및 기본 수분활성도(base_aw) 설정 (논문 데이터 기반 반영)
if "육류" in food_type:
    N0 = 10**4
    base_aw = 0.98
elif "채소" in food_type:
    N0 = 10**3
    base_aw = 0.95
elif "베이커리" in food_type:
    N0 = 10**1
    base_aw = 0.80
elif "계란" in food_type:
    N0 = 5 * (10**3)
    base_aw = 0.96
elif "유제품" in food_type:
    N0 = 10**2
    base_aw = 0.97

# 주변 습도가 식품 자체 수분 상태(aw)에 미치는 영향 계산
aw = base_aw + (1.0 - base_aw) * (humidity / 100)
aw = min(aw, 0.99)

# --- 세균 성장 속도(mu) 계산 ---
if temp <= 0:
    mu = 0.0  # 냉동 환경에서는 균 증식이 완전히 멈춤
elif temp <= 4:
    mu = 0.001  # 일반 냉장 환경에서는 성장이 극도로 제한됨
else:
    mu = (temp - 4) * (aw - 0.7) * 0.02

    if "계란" in food_type:
        if temp < 25:
            mu = mu * 0.3
        else:
            mu = mu * 1.2
    elif "유제품" in food_type:
        if temp > 25:
            mu = mu * 1.5

    mu = min(mu, 0.65)  # 성장 속도 상한선

# --- 로지스틱 생장 시뮬레이션 계산 ---
time_steps = range(simulation_hours)
bacterial_counts = [N0]
shelf_life = None

for t in time_steps[1:]:
    current_N = bacterial_counts[-1]
    dN = mu * current_N * (1 - current_N / K)
    next_N = current_N + dN
    bacterial_counts.append(next_N)

    if next_N >= spoilage_threshold and shelf_life is None:
        shelf_life = t

# --- 화면 결과 출력 ---
st.subheader(f"📊 시뮬레이션 결과 ({food_type})")

# 메트릭 대시보드
col1, col2 = st.columns(2)
with col1:
    st.metric(label="설정 온도", value=f"{temp} ℃")
with col2:
    if shelf_life:
        st.error(f"⚠️ 예상 소비기한: 약 {shelf_life}시간")
    else:
        st.success(f"✅ {simulation_hours}시간 내 안전 보관 가능")

# 맞춤형 피드백 조언 출력
st.info("💡 **학술 자료 기반 맞춤 보관 조언**")
if "계란" in food_type:
    st.write(
        "- **논문 Fact:** 계란을 상온(32℃) 보관할 경우 껍질 기공을 통해 수분이 날아가고 일반 세균 수가 급격히 증가($2.8 \\times 10^7$)합니다. 냉장 보관 시에는 품질 지수(Haugh Unit)와 미생물 통제가 완벽히 유지됩니다."
    )
    if temp > 20:
        st.write(
            "⚠️ **경고:** 현재 온도가 높습니다. 실온 보관이 불가피하다면 계란 표면에 **식물성 오일을 살짝 코팅**해 주는 것만으로도 냉장 보관에 준하는 수분 보호 및 세균 차단 효과를 얻을 수 있습니다."
        )
elif "유제품" in food_type:
    st.write(
        "- **논문 Fact:** 치즈와 버터 제품은 $10℃$ 냉장 보관 시에는 10~22개월 이상 품질이 유지되나, 실온($25℃$ 이상) 및 고온($35℃$)에 방치될 경우 산도 급증과 이치화학적 파괴로 유통기한이 며칠 이내로 극단적으로 짧아집니다."
    )
    if temp > 10:
        st.write(
            "⚠️ **경고:** 유제품은 반드시 **10℃ 이하(권장 4℃ 이하) 냉장 보관**을 엄수해 주세요."
        )
elif "육류" in food_type:
    st.write(
        "- **가이드:** 날고기는 수분활성도와 단백질 함량이 높아 세균 폭발 위험이 가장 높습니다. 프리셋을 통해 일반 냉장고 혹은 김치냉장고 보관 모드를 활용하는 것이 안전합니다."
    )
else:
    st.write(
        "- **가이드:** 현재 선택하신 식품은 설정하신 환경 하에서 그래프와 같은 생장 곡선을 그립니다. 보관 장소 프리셋을 움직여 보며 변화를 관찰해 보세요."
    )

# --- 그래프 시각화 ---
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(
    time_steps,
    bacterial_counts,
    label=f"{food_type} Growth Curve",
    color="#e74c3c",
    lw=2.5,
)
ax.axhline(
    y=spoilage_threshold,
    color="gray",
    linestyle="--",
    label="Spoilage Threshold (10^7 CFU/g)",
)

ax.set_xlabel("Time (Hours)", fontsize=11)
ax.set_ylabel("Bacterial Count (CFU/g)", fontsize=11)
ax.set_title(
    f"Bacterial Growth: {food_type} / Temp: {temp}℃, Humid: {humidity}%",
    fontsize=12,
    pad=10,
)
ax.legend(loc="upper left")
ax.grid(True, which="both", linestyle=":", alpha=0.6)

st.pyplot(fig)
