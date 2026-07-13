import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# --- 웹 페이지 설정 ---
st.set_page_config(page_title="소비기한 시뮬레이터", layout="centered")

st.title("🌡️ 맞춤형 식품 소비기한 시뮬레이터 (Step 2)")
st.write(
    "보관 환경(온도, 습도)을 조절하며 세균 생장 곡선과 예상 소비기한을 실시간으로 확인해보세요."
)

# --- 사이드바: 사용자 입력 환경 변수 조절 ---
st.sidebar.header("🌐 보관 환경 설정")

# 사용자가 직접 조절할 수 있는 슬라이더 UI
temp = st.sidebar.slider("보관 온도 (℃)", min_value=-5, max_value=45, value=25, step=1)
humidity = st.sidebar.slider(
    "보관 습도 (%)", min_value=10, max_value=100, value=80, step=5
)
simulation_hours = st.sidebar.slider(
    "시뮬레이션 시간 (Hours)", min_value=24, max_value=300, value=200, step=12
)

# --- 백엔드 시뮬레이션 로직 ---
# 1. 초기 세팅
N0 = 10**3  # 초기 균 수 (1,000 마리)
K = 10**9  # 환경 수용력 (최대 증식 가능한 10억 마리)
spoilage_threshold = 10**7  # 부패 기준 (1천만 마리)

# 2. 온도와 습도에 따른 성장 속도(mu) 계산 (수분활성도 개념 매핑)
aw = 0.6 + 0.4 * (humidity / 100)

if temp <= 4 or aw < 0.75:
    mu = 0.005  # 냉장 상태거나 너무 건조하면 성장이 거의 멈춤
else:
    # 온도가 높고 습도가 높을수록 성장 속도 증가
    mu = (temp - 4) * (aw - 0.7) * 0.025
    mu = min(mu, 0.5)  # 상한선 제한

# 3. 시간 경과에 따른 로지스틱 생장 계산
time_steps = range(simulation_hours)
bacterial_counts = [N0]
shelf_life = None

for t in time_steps[1:]:
    current_N = bacterial_counts[-1]
    # 로지스틱 방정식: dN = mu * N * (1 - N/K)
    dN = mu * current_N * (1 - current_N / K)
    next_N = current_N + dN
    bacterial_counts.append(next_N)

    # 최초 부패 기준 돌파 시간 기록
    if next_N >= spoilage_threshold and shelf_life is None:
        shelf_life = t

# --- 화면 결과 출력 (대시보드 형태로 구성) ---
st.subheader("📊 시뮬레이션 결과 요약")

# 메트릭 컴포넌트로 소비기한 직관적으로 표시
if shelf_life:
    st.error(f"⚠️ 예상 소비기한: 약 **{shelf_life}시간** 후 부패 위험")
else:
    st.success(f"✅ 안전: {simulation_hours}시간 내에는 부패 기준에 도달하지 않습니다.")

# 맞춤형 보관 조언 제공
st.info("💡 **보관 환경 맞춤 조언**")
advice_texts = []
if temp > 10:
    advice_texts.append(
        "- 현재 온도가 높습니다. **4℃ 이하 냉장 보관** 시 세균 증식을 극적으로 억제할 수 있습니다."
    )
if humidity > 70:
    advice_texts.append(
        "- 습도가 높은 환경입니다. 수분이 많으면 균이 빠르게 자라므로 **밀봉 용기 보관**이나 밀가루 제품의 경우 **건조 보관**이 필요합니다."
    )
if temp <= 4:
    advice_texts.append(
        "- 올바른 냉장 온도를 유지 중입니다. 다만 밀폐되지 않으면 교차 오염이 발생할 수 있으니 주의하세요."
    )

if advice_texts:
    for text in advice_texts:
        st.write(text)
else:
    st.write("- 현재 보관 환경이 훌륭하게 유지되고 있습니다.")


# --- 그래프 시각화 ---
st.subheader("📈 세균 생장 곡선")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(time_steps, bacterial_counts, label="Bacterial Growth", color="#ff4b4b", lw=2)
ax.axhline(
    y=spoilage_threshold,
    color="gray",
    linestyle="--",
    label="Spoilage Threshold (10^7)",
)

# 그래프 스타일링 (Y축 단위를 일반 숫자로 표시하되 가독성 확보)
ax.set_xlabel("Time (Hours)", fontsize=11)
ax.set_ylabel("Bacterial Count (CFU/g)", fontsize=11)
ax.set_title(
    f"Bacterial Growth Curve (Temp: {temp}℃, Humidity: {humidity}%)",
    fontsize=13,
    pad=15,
)
ax.legend(loc="upper left")
ax.grid(True, which="both", linestyle=":", alpha=0.6)

# Streamlit에 matplotlib 그래프 전달하여 그리기
st.pyplot(fig)