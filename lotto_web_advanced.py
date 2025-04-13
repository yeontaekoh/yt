import streamlit as st
import pandas as pd
import random
from collections import Counter
import matplotlib.pyplot as plt
import io

# --------------------
# 파일 로드
# --------------------
df = pd.read_csv("로또_전체_회차.csv")

# 최근 10회차 데이터 추출
recent_df = df[df['회차'] >= 1157].tail(10)

# --------------------
# 보조 어느 옵션에서나 사용
# --------------------
number_cols = [f"번호{i}" for i in range(1, 7)]
all_numbers = df[number_cols].values.flatten()
number_counter = Counter(all_numbers)

recent_numbers_flat = recent_df[number_cols].values.flatten()
recent_counter = Counter(recent_numbers_flat)

# 번호대별 색상

def get_number_color(n):
    if 1 <= n <= 10:
        return "#ffc107"  # 노랑
    elif 11 <= n <= 20:
        return "#03a9f4"  # 파랑
    elif 21 <= n <= 30:
        return "#ff6f61"  # 빨강
    elif 31 <= n <= 40:
        return "#9e9e9e"  # 회색
    else:
        return "#cddc39"  # 연두

# --------------------
# 추천 로직
# --------------------
def recommend_all():
    top20 = [int(n) for n, _ in number_counter.most_common(20)]
    return sorted(random.sample(top20, 6))

def recommend_recent():
    top15 = [int(n) for n, _ in recent_counter.most_common(15)]
    return sorted(random.sample(top15, 6))

def has_consecutive(nums):
    nums = sorted(nums)
    return any(nums[i] + 1 == nums[i+1] for i in range(len(nums)-1))

def recommend_pattern():
    recent_numbers = recent_df[number_cols].values.tolist()
    flat_numbers = [num for row in recent_numbers for num in row]
    freq_counter = Counter(flat_numbers)
    top_recent_numbers = [num for num, _ in freq_counter.most_common(15)]

    odd_count = sum(1 for n in flat_numbers if n % 2 == 1)
    even_count = len(flat_numbers) - odd_count
    low_count = sum(1 for n in flat_numbers if n <= 22)
    high_count = len(flat_numbers) - low_count

    consecutive_weeks = sum(1 for row in recent_numbers if has_consecutive(row))
    consecutive_ratio = consecutive_weeks / 10

    def recommend_based_on_pattern():
        candidate_pool = top_recent_numbers.copy()
        while True:
            pick = sorted(random.sample(candidate_pool, 6))
            odd = sum(1 for n in pick if n % 2 == 1)
            even = 6 - odd
            low = sum(1 for n in pick if n <= 22)
            high = 6 - low
            consec = has_consecutive(pick)

            if (
                2 <= odd <= 4 and
                2 <= even <= 4 and
                2 <= low <= 4 and
                2 <= high <= 4 and
                (consecutive_ratio >= 0.5 and consec)
            ):
                return pick

    return recommend_based_on_pattern()

# --------------------
# 유사도 비교
# --------------------
def compare_with_past(pick):
    max_match = 0
    best_round = None
    for _, row in df.iterrows():
        past = {row[col] for col in number_cols}
        match = len(set(pick) & past)
        if match > max_match:
            max_match = match
            best_round = (row["회차"], row["추첨일"], list(past))
    return best_round + (max_match,)

# --------------------
# 카드 형태로 추천 세트 묶기
# --------------------
def draw_card_set(title, nums, match_info):
    with st.container():
        number_html = "".join([
            f"<div style='display:inline-flex; margin:5px; width:60px; height:60px; border-radius:50%; background: {get_number_color(n)}; box-shadow: 2px 2px 6px rgba(0,0,0,0.15); align-items:center; justify-content:center; font-weight:bold; font-size:20px; color:#fff;'>{n}</div>"
            for n in nums
        ])

        summary_html = (
            f"<div style='text-align: center; font-size: 14px; color: #666; margin-top: 10px;'>"
            f"가장 유사한 회차: <b>{match_info[0]}회</b> ({match_info[1]})<br/>"
            f"일치 번호 수: <b>{match_info[3]}개</b>"
            f"</div>"
        )

        html = f"""
        <div style='background: white; padding: 20px; margin-bottom: 20px; border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); border: 1px solid #eee;'>
            <h4 style='margin-bottom: 15px;'>{title}</h4>
            <div style='display: flex; justify-content: center; flex-wrap: nowrap; gap: 10px; margin-bottom: 15px;'>
                {number_html}
            </div>
            {summary_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

# --------------------
# 게시켜이션 UI
# --------------------
st.set_page_config(page_title="로또 번호 추천기", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #f6f8fa;
        font-family: 'Segoe UI', sans-serif;
    }
    .stDownloadButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 로또 번호 추천기 (통계 기반)")

option = st.selectbox("추천 방식 선택", ["전체 회차 기반", "최근 10회차 기반", "최근 10회차 패턴 기반"])

if st.button("✨ 추천 번호 뽑기 (5세트) ✨"):
    st.markdown("---")
    for i in range(5):
        if option == "전체 회차 기반":
            pick = recommend_all()
        elif option == "최근 10회차 기반":
            pick = recommend_recent()
        elif option == "최근 10회차 패턴 기반":
            pick = recommend_pattern()

        r, date, past, match = compare_with_past(pick)
        draw_card_set(f"🌟 추천 세트 #{i+1}", pick, (r, date, past, match))

    # CSV 다운로드
    if option == "전체 회차 기반":
        csv_data = [recommend_all() for _ in range(5)]
    elif option == "최근 10회차 기반":
        csv_data = [recommend_recent() for _ in range(5)]
    else:
        csv_data = [recommend_pattern() for _ in range(5)]

    csv = pd.DataFrame(csv_data, columns=[f"번호{i+1}" for i in range(6)])
    csv_bytes = csv.to_csv(index=False).encode()
    st.download_button("⬇ 추천 결과 CSV 다운로드", data=csv_bytes, file_name="추천_번호.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("📊 전체 번호 출현 빈도 (1~45)")
    freq_df = pd.DataFrame.from_dict(number_counter, orient='index').reset_index()
    freq_df.columns = ["번호", "횟수"]
    freq_df = freq_df.sort_values("번호")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(freq_df["번호"], freq_df["횟수"], color="#6fa8dc")
    ax.set_xlabel("번호")
    ax.set_ylabel("횟수")
    ax.set_title("모든 회차 번호 횟수")
    st.pyplot(fig)
