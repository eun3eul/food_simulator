import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# --- 웹 페이지 설정 ---
st.set_page_config(page_title="소비기한 시뮬레이터 v2", layout="centered")

st.title("🍔 음식 맞춤형 소비기한 시뮬레이터 (Step 3)")
st.write(
    "음식 종류와 보관 환경에 따른 맞춤형 세균 생장 곡선 및 조언을 확인하세요."
)

# --- 사이드바: 음식 종류 및 환경 변수 선택 ---
st.sidebar.header("📋 설정 메뉴")

# 1. 음식 종류 선택 (이번 단계의 핵심 추가 기능!)
food_type = st.sidebar.selectbox(
    "음식 종류를 선택하세요",
    ("🥩 육류 / 생선 (신선식품)", "🥗 채소 / 샐러드", "🍞 베이커리 (빵류)"),
)

st.sidebar.markdown("---")  # 구분선

# 2. 환경 변수 슬라이더
temp = st.sidebar.slider("보관 온도 (℃)", min_value=-5, max_value=45, value=25, step=1)
humidity = st.sidebar.slider(
    "보관 습도 (%)", min_value=10, max_value=100, value=80, step=5
)
simulation_hours = st.sidebar.slider(
    "시뮬레이션 시간 (Hours)", min_value=24, max_value=300, value=200, step=12
)

# --- 백엔드 로직: 음식 종류별 파라미터 세팅 ---
K = 10**9  # 환경 수용력 (최대 균 수는 동일하게 제한)
spoilage_threshold = 10**7  # 부패 기준 (1천만 마리)

# 음식 선택에 따른 초기 세균 수(N0)와 기본 수분활성도(aw) 조정
if "육류" in food_type:
    N0 = 10**4  # 날고기는 기본 균 수가 많음 (10,000 마리 시작)
    base_aw = 0.98  # 자체 수분이 매우 높음
elif "채소" in food_type:
    N0 = 10**3  # 보통 수준 (1,000 마리 시작)
    base_aw = 0.95  # 수분 높음
else:  # 베이커리
    N0 = 10**1  # 굽는 과정에서 균이 거의 죽음 (10 마리 시작)
    base_aw = 0.80  # 비교적 건조함

# 환경 습도가 음식 자체 수분활성도(aw)에 미치는 영향 계산
# 베이커리 같은 건조 식품은 주변 습도가 높으면 급격히 눅눅해지며 aw가 올라감
aw = base_aw + (1.0 - base_aw) * (humidity / 100)
aw = min(aw, 0.99)  # 1.0을 넘을 수 없음

# --- 세균 성장 속도(mu) 계산 ---
if temp <= 4 or aw < 0.75:
    mu = 0.002  # 냉장 상태거나 아주 건조하면 거의 안 자람
else:
    # 온도와 음식의 최종 aw에 따른 속도 공식
    mu = (temp - 4) * (aw - 0.7) * 0.03
    mu = min(mu, 0.6)  # 폭발적 성장의 상한선

# --- 로지스틱 생장 시뮬레이션 ---
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
st.subheader(f"📊 {food_type} 시뮬레이션 결과")

# 소비기한 메트릭
if shelf_life:
    st.error(f"⚠️ 예상 소비기한: 약 **{shelf_life}시간** 후 부패 위험")
else:
    st.success(f"✅ 안전: {simulation_hours}시간 내에는 부패 기준에 도달하지 않습니다.")

# 음식별 맞춤 조언 (디테일 추가!)
st.info("💡 **식품 맞춤형 보관 조언**")
if "육류" in food_type:
    st.write(
        "- **신선 육류/생선**은 초기 균 수가 많고 영양분이 풍부해 가장 빠르게 부패합니다. 무조건 **4℃ 이하 냉장** 또는 장기 보관 시 **냉동(-18℃ 이하)** 하세요."
    )
elif "채소" in food_type:
    st.write(
        "- **채소 및 샐러드**는 씻은 후 물기를 잘 제거해야 균 증식을 늦출 수 있습니다. 밀폐 용기에 키친타월을 깔아 보관하는 것을 추천합니다."
    )
else:
    st.write(
        "- **베이커리류**는 주변 습도가 높으면(특히 70% 이상) 빵 표면에 곰팡이나 세균이 증식하기 쉬운 환경이 됩니다. 남은 빵은 밀봉하여 **냉동 보관** 후 에어프라이어에 데워 드세요."
    )

# --- 그래프 시각화 ---
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(
    time_steps,
    bacterial_counts,
    label=f"{food_type.split()[1]} Growth",
    color="#1f77b4" if "베이커리" in food_type else "#ff4b4b",
    lw=2,
)
ax.axhline(
    y=spoilage_threshold,
    color="gray",
    linestyle="--",
    label="Spoilage Threshold (10^7)",
)

ax.set_xlabel("Time (Hours)", fontsize=11)
ax.set_ylabel("Bacterial Count (CFU/g)", fontsize=11)
ax.set_title(f"Bacterial Growth Curve (Temp: {temp}℃, Humid: {humidity}%)")
ax.legend(loc="upper left")
ax.grid(True, which="both", linestyle=":", alpha=0.6)

st.pyplot(fig)