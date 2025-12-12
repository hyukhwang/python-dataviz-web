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

# Sidebar Navigation with hierarchical menu
st.sidebar.title("🧭 Navigation")

# Main menu selection
main_menu = st.sidebar.selectbox(
    "Select Team:",
    ["3.1 Siddhi Shrestha", "3.2 Dandi Ram", "3.3 Arinita"]
)

st.sidebar.markdown("---")

# Sub-menu based on main menu selection
if main_menu == "3.1 Siddhi Shrestha":
    page = st.sidebar.radio(
        "Select Indicator:",
        [
            "3.1.1 Safe water access 🚰",
            "3.1.2 Water-safe communities 💧",
            "3.1.3 Basic sanitation gained 🚻",
            "3.1.4 Schools with WASH 🏫",
            # "3.1.5 HCFs with WASH 🏥",   <<< 삭제됨
            "3.1.6 Humanitarian water support ⚠️",
            "3.1.7 Humanitarian sanitation & hygiene 🧼",
            "3.1.8 End Year Progress against Annual target 📊"
        ]
    )
elif main_menu == "3.2 Dandi Ram":
    page = st.sidebar.radio(
        "Select Indicator:",
        ["Coming Soon..."]
    )
elif main_menu == "3.3 Arinita":
    page = st.sidebar.radio(
        "Select Indicator:",
        ["Coming Soon..."]
    )

st.sidebar.markdown("---")

# Sidebar for file path configuration
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

# Display current working directory
st.sidebar.info(f"**현재 작업 디렉토리:**\n{os.getcwd()}")

# Check if file exists
if os.path.exists(file_path):
    st.sidebar.success(f"✅ 파일 발견: {file_path}")
else:
    st.sidebar.error(f"❌ 파일 없음: {file_path}")
    
    st.sidebar.write("**현재 폴더의 파일들:**")
    try:
        files = os.listdir('.')
        for f in files:
            st.sidebar.text(f"- {f}")

        if os.path.exists('data'):
            st.sidebar.write("**data 폴더 내 파일들:**")
            data_files = os.listdir('data')
            for f in data_files:
                st.sidebar.text(f"- {f}")
    except:
        pass

# Nepal Field Office Coordinates (NCO 포함하여 총 5개)
OFFICE_COORDINATES = {
    'NCO': {'lat': 27.7172, 'lon': 85.3240, 'province': 'Bagmati', 'color': '#4B0082'},
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

# Process data for office summary (NCO 포함)
@st.cache_data
def process_office_data(df):
    office_col = 'office'
    progress_col = 'progress'
    wq_col = 'water quality test carried out within last one year shows safe water?'
    year_col = 'water supply beneficiaries reporting year'
    total_col = 'total beneficiary population # (current)'

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[wq_col] = df[wq_col].astype(str).str.strip().str.lower()

    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[total_col] = (
        df[total_col]
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_completed = df[progress_col].str.contains('completed', na=False)
    cond_safe = df[wq_col].str.contains(r'\byes\b', na=False)
    cond_2025 = df[year_col] == 2025

    # NCO 포함 5개 office mapping
    office_mapping = {
        'nco': {'name': 'NCO', 'target': 0},
        'janakpur': {'name': 'Janakpur', 'target': 7987},
        'dhangadi': {'name': 'Dhangadi', 'target': 6432},
        'bhairahawa': {'name': 'Bhairahawa', 'target': 9659},
        'surkhet': {'name': 'Surkhet', 'target': 13822}
    }

    offices = ['nco', 'janakpur', 'dhangadi', 'bhairahawa', 'surkhet']
    office_data = []

    for office_key in offices:
        cond_office = df[office_col].str.contains(office_key, na=False)

        df_filtered = df[
            cond_office &
            cond_completed &
            cond_safe &
            cond_2025
        ]

        total = df_filtered[total_col].sum()
        office_info = office_mapping[office_key]
        target = office_info['target']
        achievement = (total / target * 100) if target > 0 else 0

        office_data.append({
            'Office': office_info['name'],
            'Beneficiaries': int(total),
            'Target': target,
            'Achievement': achievement
        })

    return pd.DataFrame(office_data)

# Process data for palika level (NCO 포함)
@st.cache_data
def process_palika_data(df):
    office_col = 'office'
    progress_col = 'progress'
    wq_col = 'water quality test carried out within last one year shows safe water?'
    year_col = 'water supply beneficiaries reporting year'
    total_col = 'total beneficiary population # (current)'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[wq_col] = df[wq_col].astype(str).str.strip().str.lower()

    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[total_col] = (
        df[total_col]
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_completed = df[progress_col].str.contains('completed', na=False)
    cond_safe = df[wq_col].str.contains(r'\byes\b', na=False)
    cond_2025 = df[year_col] == 2025

    df_filtered = df[cond_completed & cond_safe & cond_2025].copy()

    office_mapping = {
        'nco': 'NCO',
        'janakpur': 'Janakpur',
        'dhangadi': 'Dhangadi',
        'bhairahawa': 'Bhairahawa',
        'surkhet': 'Surkhet'
    }

    def map_office(office_str):
        office_lower = str(office_str).lower()
        for key, value in office_mapping.items():
            if key in office_lower:
                return value
        return 'Unknown'

    df_filtered['office_clean'] = df_filtered[office_col].apply(map_office)

    palika_summary = df_filtered.groupby([
        'office_clean',
        palika_col,
        district_col,
        province_col
    ])[total_col].sum().reset_index()

    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)

    return palika_summary

# Create Nepal map with markers
def create_nepal_map(office_df, palika_df):
    nepal_map = folium.Map(
        location=[28.3949, 84.1240],
        zoom_start=7,
        tiles='OpenStreetMap'
    )

    for idx, row in office_df.iterrows():
        office_name = row['Office']
        if office_name in OFFICE_COORDINATES:
            coords = OFFICE_COORDINATES[office_name]
            palikas_count = len(palika_df[palika_df['Office'] == office_name])

            popup_html = f"""
            <div style="font-family: Arial; min-width: 200px;">
                <h4 style="color: {coords['color']}; margin-bottom: 10px;">{office_name}</h4>
                <b>Province:</b> {coords['province']}<br>
                <b>Total Beneficiaries:</b> {row['Beneficiaries']:,}<br>
                <b>Target:</b> {row['Target']:,}<br>
                <b>Achievement:</b> {row['Achievement']:.1f}%<br>
                <b>Palikas Covered:</b> {palikas_count}
            </div>
            """

            folium.CircleMarker(
                location=[coords['lat'], coords['lon']],
                radius=15 + (row['Beneficiaries'] / 1000),
                popup=folium.Popup(popup_html, max_width=300),
                color=coords['color'],
                fill=True,
                fillColor=coords['color'],
                fillOpacity=0.6,
                weight=3
            ).add_to(nepal_map)

            folium.Marker(
                location=[coords['lat'], coords['lon']],
                icon=folium.DivIcon(html=f"""
                    <div style="font-size: 12pt; color: {coords['color']}; 
                         font-weight: bold; text-shadow: 1px 1px 2px white;">
                        {office_name}
                    </div>
                """)
            ).add_to(nepal_map)

    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; 
                border:2px solid grey; z-index:9999; 
                background-color:white;
                padding: 10px;
                font-size: 14px;
                ">
    <p style="margin-bottom: 5px;"><b>Field Offices</b></p>
    '''

    for office, coords in OFFICE_COORDINATES.items():
        legend_html += f'<p style="margin: 3px;"><span style="color:{coords["color"]};">●</span> {office}</p>'

    legend_html += '</div>'
    nepal_map.get_root().html.add_child(folium.Element(legend_html))

    return nepal_map


# Coming soon page
def display_coming_soon(title):
    st.title(f"{title}")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("### 🚧 Under Development")
        st.markdown("""
        This section is currently under development.
        Check back later for updates.
        """)
        st.markdown("---")
        st.markdown("**Contact:** Program team")


# Main app
try:
    if main_menu == "3.1 Siddhi Shrestha":

        if page == "3.1.1 Safe water access 🚰":
            df_raw = load_data(file_path)
            plot_df = process_office_data(df_raw)
            palika_df = process_palika_data(df_raw)

            view_mode = st.radio(
                "Select View:",
                ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"],
                horizontal=True
            )

            st.markdown("---")

            if view_mode == "📊 Office Summary Dashboard":
                st.title("💧 WASH Program Dashboard - Safe Water Access")
                st.markdown("### Total Beneficiaries by Field Office (2025)")
                st.markdown("---")

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
                    st.metric("Field Offices", "5")

            else:
                st.title("🗺️ Nepal Map & Palika Analysis")
                st.markdown("---")

                nepal_map = create_nepal_map(plot_df, palika_df)
                st_folium(nepal_map, width=1000, height=600)

        else:
            display_coming_soon(page)

    else:
        display_coming_soon(page)

except Exception as e:
    st.error(f"❌ Error occurred: {str(e)}")
