import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium import plugins

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
    ["3.1 Siddhi Shrestha", "3.2 Dandi Ram", "3.3 Arinita","End Year Progress against Annual target"]
)

st.sidebar.markdown("---")

# Sub-menu based on main menu selection
if main_menu == "3.1 Siddhi Shrestha":
    page = st.sidebar.radio(
        "Select Indicator:",
        [
            "3.1.1 Safe water access 🚰",
            "3.1.2 Water-safe communities 💧",
            "3.1.3 Basic sanitation gained 🚽",
            "3.1.4 Schools with WASH 🏫",
            "3.1.5 HCFs with WASH 🏥",
            "3.1.6 GEE Land Cover Analysis 🛰️",
            "3.1.7 Humanitarian water support ",
            "3.1.8 Humanitarian sanitation & hygiene ",
            "3.1.9 End Year Progress against Annual target "
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
    
    # List files in current directory
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

# Nepal Field Office Coordinates
OFFICE_COORDINATES = {
    'NCO': {'lat': 27.7172, 'lon': 85.3240, 'province': 'Bagmati', 'color': '#4B0082'},
    'Janakpur': {'lat': 26.7288, 'lon': 85.9244, 'province': 'Madhesh', 'color': '#0088FE'},
    'Dhangadi': {'lat': 28.6940, 'lon': 80.5831, 'province': 'Sudurpashchim', 'color': '#00C49F'},
    'Bhairahawa': {'lat': 27.5047, 'lon': 83.4503, 'province': 'Lumbini', 'color': '#FFBB28'},
    'Surkhet': {'lat': 28.6020, 'lon': 81.6177, 'province': 'Karnali', 'color': '#FF8042'}
}

# Approximate Palika coordinates (샘플 데이터 - 실제 좌표로 대체 필요)
PALIKA_COORDINATES = {
    'Kathmandu': {'lat': 27.7172, 'lon': 85.3240},
    'Pokhara': {'lat': 28.2096, 'lon': 83.9856},
    'Lalitpur': {'lat': 27.6667, 'lon': 85.3167},
    'Bhaktapur': {'lat': 27.6710, 'lon': 85.4298},
    # 더 많은 Palika 좌표 추가 필요
}

# Load data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip().str.lower()
    return df

# Process data for office summary
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
    
    office_mapping = {
        'nco': {'name': 'NCO', 'target': 13648},
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
    
    plot_df = pd.DataFrame(office_data)
    plot_df_filtered = plot_df[
        (plot_df['Beneficiaries'] > 0) | (plot_df['Target'] > 0) | (plot_df['Office'] == 'NCO')
    ]
    
    return plot_df_filtered

# Process data for palika level
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
    
    df_filtered['Office'] = df_filtered[office_col].apply(map_office)
    
    palika_summary = df_filtered.groupby([
        'Office', 
        palika_col, 
        district_col,
        province_col
    ])[total_col].sum().reset_index()
    
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    
    palika_summary = palika_summary[palika_summary['Office'] != 'Unknown']
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)
    
    return palika_summary

# 3.1.2 Water-safe communities 데이터 처리
@st.cache_data
def process_wsc_data(df):
    office_col = 'office'
    wsc_col = 'is the community declared water safe?'
    year_col = 'wsc reporting year'
    total_col = 'total beneficiary population # (current)'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col] = df[wsc_col].astype(str).str.strip().str.lower()
    
    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    
    df[total_col] = (
        df[total_col]
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
    
    cond_wsc = df[wsc_col].str.contains(r'\byes\b', na=False)
    cond_2025 = df[year_col] == 2025
    
    df_filtered = df[cond_wsc & cond_2025].copy()
    
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
    
    df_filtered['Office'] = df_filtered[office_col].apply(map_office)
    
    # Office level summary
    office_summary = df_filtered.groupby('Office')[total_col].sum().reset_index()
    office_summary.columns = ['Office', 'Beneficiaries']
    office_summary['Beneficiaries'] = office_summary['Beneficiaries'].astype(int)
    
    # Palika level summary
    palika_summary = df_filtered.groupby([
        'Office', 
        palika_col, 
        district_col,
        province_col
    ])[total_col].sum().reset_index()
    
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)
    
    return office_summary, palika_summary

# 3.1.3 Basic sanitation gained 데이터 처리
@st.cache_data
def process_sanitation_data(df):
    office_col = 'office'
    toilet_col = '# of additional toilets built'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    
    df[toilet_col] = (
        df[toilet_col]
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[toilet_col] = pd.to_numeric(df[toilet_col], errors='coerce').fillna(0)
    
    df_filtered = df[df[toilet_col] > 0].copy()
    
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
    
    df_filtered['Office'] = df_filtered[office_col].apply(map_office)
    df_filtered['Total_Beneficiaries'] = df_filtered[toilet_col] * 5
    
    # Office level summary
    office_summary = df_filtered.groupby('Office')['Total_Beneficiaries'].sum().reset_index()
    office_summary.columns = ['Office', 'Total_Beneficiaries']
    office_summary['Total_Beneficiaries'] = office_summary['Total_Beneficiaries'].astype(int)
    
    # Palika level summary
    palika_summary = df_filtered.groupby([
        'Office', 
        palika_col, 
        district_col,
        province_col
    ])['Total_Beneficiaries'].sum().reset_index()
    
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Total_Beneficiaries']
    palika_summary['Total_Beneficiaries'] = palika_summary['Total_Beneficiaries'].astype(int)
    palika_summary = palika_summary.sort_values('Total_Beneficiaries', ascending=False)
    
    return office_summary, palika_summary

# 3.1.4 Schools with WASH 데이터 처리
@st.cache_data
def process_schools_data(df):
    office_col = 'office'
    completion_col = 'completion year'
    tester_col = 'tester function'
    school_col = 'school name'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[completion_col] = df[completion_col].astype(str).str.extract(r'(\d{4})')
    df[completion_col] = pd.to_numeric(df[completion_col], errors='coerce')
    df[tester_col] = df[tester_col].astype(str).str.strip().str.lower()
    
    cond_2025 = df[completion_col] == 2025
    cond_tester = df[tester_col].str.contains(r'\byes\b', na=False)
    
    df_filtered = df[cond_2025 & cond_tester].copy()
    
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
    
    df_filtered['Office'] = df_filtered[office_col].apply(map_office)
    
    # Office level count
    office_summary = df_filtered.groupby('Office').size().reset_index(name='School_Count')
    
    # School details
    school_details = df_filtered[[
        'Office', school_col, palika_col, district_col, province_col
    ]].copy()
    school_details.columns = ['Office', 'School_Name', 'Palika', 'District', 'Province']
    
    return office_summary, school_details

# 3.1.5 HCFs with WASH 데이터 처리
@st.cache_data
def process_hcf_data(df):
    office_col = 'office'
    completion_col = 'completion year'
    standard_col = 'hcf meeting basic standard (after implementation)'
    hcf_col = 'hcf name'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[completion_col] = df[completion_col].astype(str).str.extract(r'(\d{4})')
    df[completion_col] = pd.to_numeric(df[completion_col], errors='coerce')
    df[standard_col] = df[standard_col].astype(str).str.strip().str.lower()
    
    cond_2025 = df[completion_col] == 2025
    cond_standard = df[standard_col].str.contains(r'\byes\b', na=False)
    
    df_filtered = df[cond_2025 & cond_standard].copy()
    
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
    
    df_filtered['Office'] = df_filtered[office_col].apply(map_office)
    
    # Office level count
    office_summary = df_filtered.groupby('Office').size().reset_index(name='HCF_Count')
    
    # HCF details
    hcf_details = df_filtered[[
        'Office', hcf_col, palika_col, district_col, province_col
    ]].copy()
    hcf_details.columns = ['Office', 'HCF_Name', 'Palika', 'District', 'Province']
    
    return office_summary, hcf_details

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
            
            palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique())
            
            popup_html = f"""
            <div style="font-family: Arial; min-width: 200px;">
                <h4 style="color: {coords['color']}; margin-bottom: 10px;">{office_name}</h4>
                <b>Province:</b> {coords['province']}<br>
                <b>Total Beneficiaries (2025):</b> {row['Beneficiaries']:,}<br>
                <b>Target:</b> {row['Target']:,}<br>
                <b>Achievement:</b> {row['Achievement']:.1f}%<br>
                <b>Palikas Covered:</b> {palikas_count}
            </div>
            """
            
            folium.CircleMarker(
                location=[coords['lat'], coords['lon']],
                radius=10 + (row['Beneficiaries'] / 3000),
                popup=folium.Popup(popup_html, max_width=300),
                color=coords['color'],
                fill=True,
                fillColor=coords['color'],
                fillOpacity=0.6,
                weight=1
            ).add_to(nepal_map)
            
            folium.Marker(
                location=[coords['lat'], coords['lon']],
                icon=folium.DivIcon(html=f"""
                    <div style="font-size: 10pt; color: {coords['color']}; 
                                font-weight: bold; text-shadow: 1px 1px 2px white;
                                margin-left: 15px; margin-top: -10px;">
                        {office_name} ({row['Achievement']:.0f}%)
                    </div>
                """)
            ).add_to(nepal_map)
    
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; 
                border:2px solid grey; z-index:9999; 
                background-color:white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                ">
    <p style="margin-bottom: 5px;"><b>Field Offices</b></p>
    '''
    
    for office, coords in OFFICE_COORDINATES.items():
        legend_html += f'<p style="margin: 3px;"><span style="color:{coords["color"]}; font-size: 20px;">●</span> {office} ({coords["province"]})</p>'
    
    legend_html += '</div>'
    nepal_map.get_root().html.add_child(folium.Element(legend_html))
    
    return nepal_map

# Create Palika map for WSC or Sanitation
def create_palika_map(palika_df, indicator_name="Beneficiaries"):
    nepal_map = folium.Map(
        location=[28.3949, 84.1240],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add office markers first
    for office_name, coords in OFFICE_COORDINATES.items():
        folium.CircleMarker(
            location=[coords['lat'], coords['lon']],
            radius=8,
            color=coords['color'],
            fill=True,
            fillColor=coords['color'],
            fillOpacity=0.3,
            weight=2,
            popup=f"<b>{office_name}</b><br>{coords['province']}"
        ).add_to(nepal_map)
    
    # Add palika markers (approximate locations)
    for idx, row in palika_df.iterrows():
        palika_name = row['Palika']
        office_name = row['Office']
        
        # 실제 좌표가 있으면 사용, 없으면 Office 좌표에서 약간 offset
        if palika_name in PALIKA_COORDINATES:
            lat = PALIKA_COORDINATES[palika_name]['lat']
            lon = PALIKA_COORDINATES[palika_name]['lon']
        else:
            # Office 좌표 근처에 랜덤하게 배치
            import random
            office_coords = OFFICE_COORDINATES.get(office_name, {'lat': 28.3949, 'lon': 84.1240})
            lat = office_coords['lat'] + random.uniform(-0.5, 0.5)
            lon = office_coords['lon'] + random.uniform(-0.5, 0.5)
        
        value = row.get(indicator_name, row.get('Total_Beneficiaries', 0))
        
        popup_html = f"""
        <div style="font-family: Arial; min-width: 180px;">
            <h4 style="margin-bottom: 8px;">{palika_name}</h4>
            <b>Office:</b> {office_name}<br>
            <b>District:</b> {row['District']}<br>
            <b>Province:</b> {row['Province']}<br>
            <b>{indicator_name}:</b> {value:,}
        </div>
        """
        
        color = OFFICE_COORDINATES[office_name]['color']
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=5 + (value / 1000),
            popup=folium.Popup(popup_html, max_width=250),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=1
        ).add_to(nepal_map)
    
    return nepal_map

# Create map for schools or HCFs
def create_facilities_map(facilities_df, facility_type="School"):
    nepal_map = folium.Map(
        location=[28.3949, 84.1240],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add office markers
    for office_name, coords in OFFICE_COORDINATES.items():
        folium.CircleMarker(
            location=[coords['lat'], coords['lon']],
            radius=10,
            color=coords['color'],
            fill=True,
            fillColor=coords['color'],
            fillOpacity=0.3,
            weight=2,
            popup=f"<b>{office_name}</b><br>{coords['province']}"
        ).add_to(nepal_map)
    
    # Add facility markers
    name_col = 'School_Name' if facility_type == "School" else 'HCF_Name'
    
    for idx, row in facilities_df.iterrows():
        facility_name = row[name_col]
        office_name = row['Office']
        
        # Approximate location based on office
        import random
        office_coords = OFFICE_COORDINATES.get(office_name, {'lat': 28.3949, 'lon': 84.1240})
        lat = office_coords['lat'] + random.uniform(-0.5, 0.5)
        lon = office_coords['lon'] + random.uniform(-0.5, 0.5)
        
        popup_html = f"""
        <div style="font-family: Arial; min-width: 180px;">
            <h4 style="margin-bottom: 8px;">{facility_name}</h4>
            <b>Type:</b> {facility_type}<br>
            <b>Office:</b> {office_name}<br>
            <b>Palika:</b> {row['Palika']}<br>
            <b>District:</b> {row['District']}<br>
            <b>Province:</b> {row['Province']}
        </div>
        """
        
        color = OFFICE_COORDINATES[office_name]['color']
        
        icon_symbol = '🏫' if facility_type == "School" else '🏥'
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color='blue' if facility_type == "School" else 'red', icon='info-sign')
        ).add_to(nepal_map)
    
    return nepal_map

def