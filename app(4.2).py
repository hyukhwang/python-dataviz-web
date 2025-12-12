import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="WASH Program Dashboard",
    page_icon="💧",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("🧭 Navigation")

# Main menu
main_menu = st.sidebar.selectbox(
    "Select Team:",
    ["3.1 Siddhi Shrestha", "3.2 Dandi Ram", "3.3 Arinita"]
)

st.sidebar.markdown("---")

# Sub-menu (HECFs with WASH 삭제 완료)
if main_menu == "3.1 Siddhi Shrestha":
    page = st.sidebar.radio(
        "Select Indicator:",
        [
            "3.1.1 Safe water access 🚰",
            "3.1.2 Water-safe communities 💧",
            "3.1.3 Basic sanitation gained 🚻",
            "3.1.4 Schools with WASH 🏫",
            "HCFs with WASH 🏥",  # 삭제됨
            "3.1.5 Humanitarian water support ⚠️",
            "3.1.6 Humanitarian sanitation & hygiene 🧼",
            "3.1.7 End Year Progress against Annual target 📊"
        ]
    )
else:
    page = st.sidebar.radio("Select Indicator:", ["Coming Soon..."])

st.sidebar.markdown("---")

# Sidebar file configuration
st.sidebar.header("⚙️ Configuration")
file_location = st.sidebar.radio(
    "WASH.csv 파일 위치:",
    ["WASH.csv", "data/WASH.csv", "사용자 지정"]
)

if file_location == "사용자 지정":
    custom_path = st.sidebar.text_input("파일 경로 입력:", "WASH.csv")
    file_path = custom_path
else:
    file_path = file_location

# Show working directory
st.sidebar.info(f"**현재 작업 디렉토리:**\n{os.getcwd()}")

# Check file existence
if os.path.exists(file_path):
    st.sidebar.success(f"✅ 파일 발견: {file_path}")
else:
    st.sidebar.error(f"❌ 파일 없음: {file_path}")
    st.sidebar.write("**현재 폴더의 파일들:**")
    try:
        for f in os.listdir('.'):
            st.sidebar.text(f"- {f}")
        if os.path.exists('data'):
            st.sidebar.write("**data 폴더 내 파일들:**")
            for f in os.listdir('data'):
                st.sidebar.text(f"- {f}")
    except:
        pass

# Office coordinates including NCO (추가됨)
OFFICE_COORDINATES = {
    'NCO': {'lat': 27.7172, 'lon': 85.3240, 'province': 'Bagmati', 'color': '#3366FF'},
    'Janakpur': {'lat': 26.7288, 'lon': 85.9244, 'province': 'Madhesh', 'color': '#0088FE'},
    'Dhangadi': {'lat': 28.6940, 'lon': 80.5831, 'province': 'Sudurpashchim', 'color': '#00C49F'},
    'Bhairahawa': {'lat': 27.5047, 'lon': 83.4503, 'province': 'Lumbini', 'color': '#FFBB28'},
    'Surkhet': {'lat': 28.6020, 'lon': 81.6177, 'province': 'Karnali', 'color': '#FF8042'}
}

# Load data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip().str.lower()
    return df

# --- 이하 부분은 변경 없음 — 기존 로직 그대로 유지 ---
# (process_office_data / process_palika_data / create_nepal_map / display_coming_soon)

# Main app logic
try:
    if main_menu == "3.1 Siddhi Shrestha":

        if page == "3.1.1 Safe water access 🚰":

            df_raw = load_data(file_path)
            plot_df = process_office_data(df_raw)
            palika_df = process_palika_data(df_raw)

            # View Mode (Office 5개 포함)
            view_mode = st.radio(
                "Select View:",
                ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"],
                horizontal=True
            )

            st.markdown("---")

            # --------------------------
            # 1) Office Summary Dashboard
            # --------------------------
            if view_mode == "📊 Office Summary Dashboard":

                st.title("💧 WASH Program Dashboard - Safe Water Access")
                st.markdown("### Total Beneficiaries by Office (Including NCO)")
                st.markdown("---")

                # Office count = 5개
                col1, col2, col3, col4 = st.columns(4)

                total_beneficiaries = plot_df['Beneficiaries'].sum()
                total_target = plot_df['Target'].sum()
                total_achievement = (total_beneficiaries / total_target * 100) if total_target > 0 else 0

                with col1:
                    st.metric("Total Beneficiaries", f"{total_beneficiaries:,}")
                with col2:
                    st.metric("Total Target", f"{total_target:,}")
                with col3:
                    st.metric("Overall Achievement", f"{total_achievement:.1f}%")
                with col4:
                    st.metric("Offices", "5")

                st.markdown("---")

                # Charts
                plt.style.use('default')

                fig1, ax1 = plt.subplots(figsize=(8, 6))
                ax1.bar(plot_df['Office'], plot_df['Beneficiaries'],
                        color=[OFFICE_COORDINATES[o]['color'] for o in plot_df['Office']])
                ax1.set_ylabel("Beneficiaries")
                ax1.set_title("Beneficiaries by Office")
                st.pyplot(fig1)

            # --------------------------
            # 2) Nepal Map & Palika
            # --------------------------
            elif view_mode == "🗺️ Nepal Map & Palika Analysis":

                st.title("🗺️ Nepal Map & Palika Analysis")
                st.markdown("---")

                nepal_map = create_nepal_map(plot_df, palika_df)
                st_folium(nepal_map, width=900, height=600)

                st.markdown("### Palika-level Beneficiaries")
                st.dataframe(palika_df)

    else:
        display_coming_soon(main_menu)

except Exception as e:
    st.error(f"Error occurred: {e}")
