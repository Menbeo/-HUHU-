import pandas as pd
import streamlit as st
import requests

# === App Title ===
st.title("📞 Call Center Chatbot")

# === User Guide ===
with st.expander("ℹ️ Hướng dẫn sử dụng chatbot", expanded=False):
    st.info("""
    **📘 Call Center Chatbot - Hướng Dẫn Sử Dụng**

    **1. Chọn chủ đề và từ khóa từ thanh bên**  
    📂 Sử dụng dropdown ở sidebar bên trái để chọn chủ đề (tên file CSV) và sau đó chọn từ khóa liên quan.

    **2. Xem câu trả lời**  
    🤖 Sau khi chọn từ khóa, chatbot sẽ hiển thị câu trả lời tương ứng ở phần chính.

    **3. Dữ liệu tự động cập nhật**  
    📂 Dữ liệu được lấy từ GitHub và làm sạch trước khi hiển thị.  
    Hệ thống chỉ giữ lại phiên bản mới nhất của mỗi từ khóa.

    **Lưu ý:**  
    - Nếu gặp lỗi khi kết nối, vui lòng kiểm tra kết nối mạng hoặc thử lại sau.
    - Hãy chọn chủ đề và từ khóa để tăng độ chính xác.

    **🛠 Góp ý & Báo lỗi**  
    Vui lòng liên hệ nhóm phát triển tại: [GitHub Repo](https://github.com/Menbeo/-HUHU-)
    """)

# === GitHub Repo Info ===
GITHUB_USER = "Menbeo"
GITHUB_REPO = "-HUHU-"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/"

# === Step 1: Get CSV files from GitHub ===
@st.cache_data(ttl=60)
def get_csv_file_links():
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        files = response.json()

        # Sort filenames so newer ones (e.g., with versioning) come last
        sorted_csvs = sorted(
            [file for file in files if file["name"].endswith(".csv")],
            key=lambda x: x["name"]
        )

        return {
            file["name"]: file["download_url"]
            for file in sorted_csvs
        }
    except Exception as e:
        st.error(f"❌ Lỗi khi kết nối tới GitHub: {e}")
        return {}

# === Step 2: Load & clean CSVs ===
@st.cache_data(ttl=60)
def load_csvs(csv_files):
    combined = pd.DataFrame(columns=["key word", "description", "topic"])

    for name, url in csv_files.items():
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.lower().str.strip()
            if {"key word", "description"}.issubset(df.columns):
                df["topic"] = name.replace(".csv", "")
                combined = pd.concat([combined, df[["key word", "description", "topic"]]], ignore_index=True)
        except Exception as e:
            st.warning(f"⚠️ Lỗi đọc {name}: {e}")

    # ✅ Keep only the latest version of each "key word"
    combined = combined.drop_duplicates(subset="key word", keep="last")

    # ✅ Remove duplicate descriptions (optional clean-up)
    cleaned_data = combined.drop_duplicates(subset="description", keep="first")

    return cleaned_data

# === Step 3: Load data ===
csv_files = get_csv_file_links()
data = load_csvs(csv_files)

# === Sidebar Navigation for Topic & Keyword Selection ===
st.sidebar.title("📂 Chọn Chủ Đề & Từ Khóa")
if not data.empty:
    # Get unique topics (based on CSV file names)
    topics = sorted(data["topic"].dropna().unique())
    selected_topic = st.sidebar.selectbox("Chọn chủ đề", topics)

    # Filter keywords for the selected topic
    topic_keywords = sorted(data[data["topic"] == selected_topic]["key word"].dropna().unique())
    selected_keyword = st.sidebar.selectbox("Chọn từ khóa", topic_keywords)

    # Store the selected keyword in session state
    st.session_state["selected_keyword"] = selected_keyword
else:
    st.error("⚠️ Không tìm thấy dữ liệu hợp lệ.")

# === Main Chatbot UI ===
if not data.empty and "selected_keyword" in st.session_state:
    st.subheader("🗨️ Kết quả trả lời")
    keyword = st.session_state["selected_keyword"]
    matches = data[data["key word"].str.lower().str.contains(keyword.lower(), na=False)]

    if not matches.empty:
        for _, row in matches.iterrows():
            st.write("🤖 **Bot:**", row["description"])
            st.caption(f"(📂 Chủ đề: {row['topic']} | 🔑 Từ khóa: {row['key word']})")
    else:
        st.info("Không tìm thấy mô tả cho từ khóa này.")
