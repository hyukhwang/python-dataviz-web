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
# 3.1.1 Safe water access 🚰 - 이모지 추가
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
            "3.1.1 Safe water access 🚰", # 이모지 추가
            "3.1.2 Water-safe communities 🏘️",
            "3.1.3 Basic sanitation gained ",
            "3.1.4 Schools with WASH ",
            "HCFs with WASH ",
            "3.1.5 Humanitarian water support ",
            "3.1.6 Humanitarian sanitation & hygiene ",
            "3.1.7 End Year Progress against Annual target "
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

# Load data
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip().str.lower()
    return df

# Process data for 3.1.2 Water-safe communities
@st.cache_data
def process_office_data_312(df):
    office_col = 'office'
    wsc_col = 'community declared water safe?'  # AU column
    wsc_year_col = 'wsc reporting year'  # AY column
    total_col = 'total beneficiary population # (current)'
    
    # Data Cleaning and Preparation
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col] = df[wsc_col].astype(str).str.strip().str.lower()
    
    df[wsc_year_col] = df[wsc_year_col].astype(str).str.extract(r'(\d{4})')
    df[wsc_year_col] = pd.to_numeric(df[wsc_year_col], errors='coerce')
    
    df[total_col] = (
        df[total_col]
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
    
    # Filtering Conditions for 3.1.2
    cond_water_safe = df[wsc_col].str.contains(r'\byes\b', na=False)
    cond_2025 = df[wsc_year_col] == 2025
    
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
            cond_water_safe &
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

# Process data for 3.1.2 palika level
@st.cache_data
def process_palika_data_312(df):
    office_col = 'office'
    wsc_col = 'community declared water safe?'
    wsc_year_col = 'wsc reporting year'
    total_col = 'total beneficiary population # (current)'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    
    # Data Cleaning and Preparation
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col] = df[wsc_col].astype(str).str.strip().str.lower()
    
    df[wsc_year_col] = df[wsc_year_col].astype(str).str.extract(r'(\d{4})')
    df[wsc_year_col] = pd.to_numeric(df[wsc_year_col], errors='coerce')
    
    df[total_col] = (
        df[total_col]
        .astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
    
    # Filtering Conditions
    cond_water_safe = df[wsc_col].str.contains(r'\byes\b', na=False)
    cond_2025 = df[wsc_year_col] == 2025
    
    df_filtered = df[cond_water_safe & cond_2025].copy()
    
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

# Process data for office summary (Updated to ensure NCO is included)
@st.cache_data
def process_office_data(df):
    office_col = 'office'
    progress_col = 'progress'
    wq_col = 'water quality test carried out within last one year shows safe water?'
    year_col = 'water supply beneficiaries reporting year'
    total_col = 'total beneficiary population # (current)'
    
    # Data Cleaning and Preparation
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
    
    # Filtering Conditions
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
        # Use str.contains with regex for flexible matching
        # Add a word boundary \b to ensure 'nco' matches 'nco' and not part of another word, 
        # but in this case, direct string check is safer due to how 'office' column might be filled.
        # Original code uses str.contains, which is fine, but we ensure all keys are processed.
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
    
    # Remove NCO if no data (optional, but NCO is the country office)
    plot_df = pd.DataFrame(office_data)
    # Remove offices with 0 beneficiaries and 0 target if they are not NCO, assuming NCO should always be displayed.
    plot_df_filtered = plot_df[
        (plot_df['Beneficiaries'] > 0) | (plot_df['Target'] > 0) | (plot_df['Office'] == 'NCO')
    ]
    
    return plot_df_filtered

# Process data for palika level (Updated to ensure NCO is included)
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
    
    # Data Cleaning and Preparation
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
    
    # Filtering Conditions
    cond_completed = df[progress_col].str.contains('completed', na=False)
    cond_safe = df[wq_col].str.contains(r'\byes\b', na=False)
    cond_2025 = df[year_col] == 2025
    
    df_filtered = df[cond_completed & cond_safe & cond_2025].copy()
    
    # NCO 포함 5개 office mapping
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
    
    # Group by palika, keeping Province and District for context
    palika_summary = df_filtered.groupby([
        'Office', 
        palika_col, 
        district_col,
        province_col
    ])[total_col].sum().reset_index()
    
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    
    # Remove rows where Office is 'Unknown' and Palika/District/Province is empty (cleanup)
    palika_summary = palika_summary[palika_summary['Office'] != 'Unknown']
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)
    
    return palika_summary

# Create Nepal map with markers (Updated: Now uses both office_df and palika_df)
def create_nepal_map(office_df, palika_df):
    nepal_map = folium.Map(
        location=[28.3949, 84.1240], # Center of Nepal
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    for idx, row in office_df.iterrows():
        office_name = row['Office']
        if office_name in OFFICE_COORDINATES:
            coords = OFFICE_COORDINATES[office_name]
            
            # Count the number of unique Palikas covered by this office
            palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique())
            
            # Popup content
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
            
            # Circle Marker (Size based on Beneficiaries, Color based on Office)
            folium.CircleMarker(
                location=[coords['lat'], coords['lon']],
                radius=10 + (row['Beneficiaries'] / 3000), # Base size 10 + scaling
                popup=folium.Popup(popup_html, max_width=300),
                color=coords['color'],
                fill=True,
                fillColor=coords['color'],
                fillOpacity=0.6,
                weight=1
            ).add_to(nepal_map)
            
            # Text Marker
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
    
    # Custom Legend (moved from original location)
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

# Function to display "Coming Soon" page (as in original code)
def display_coming_soon(title):
    st.title(f"{title}")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("### 🚧 Under Development")
        st.markdown("""
        This section is currently under development and will be available soon.
        
        **Status:** Ongoing
        
        Please check back later for updates.
        """)
        
        st.markdown("---")
        st.markdown("**Contact:** For more information, please contact the program team.")

# Main app logic
try:
    # Handle different team menus
    if main_menu == "3.1 Siddhi Shrestha":
        # Only 3.1.1 has full dashboard, others show "ongoing"
        if page == "3.1.1 Safe water access 🚰":
            # --- Load and Process Data ---
            df_raw = load_data(file_path)
            # Use data processing functions
            plot_df = process_office_data(df_raw)
            palika_df = process_palika_data(df_raw)
            
            # Check if any data exists after filtering
            if plot_df.empty:
                st.warning("⚠️ No data found for 'Completed Projects', 'Safe Water (Yes)', and 'Year 2025' in the loaded file.")
                
            
            # Display page selection tabs
            view_mode = st.radio(
                "Select View:",
                ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"],
                horizontal=True
            )
            
            st.markdown("---")
            
            # Calculate overall metrics once
            total_beneficiaries = plot_df['Beneficiaries'].sum()
            total_target = plot_df['Target'].sum()
            total_achievement = (total_beneficiaries / total_target * 100) if total_target > 0 else 0
            total_palikas = len(palika_df['Palika'].unique())
            
            # --- PAGE 1: Office Summary Dashboard (Refined) ---
            if view_mode == "📊 Office Summary Dashboard":
                st.title("💧 WASH Program Dashboard - Safe Water Access")
                st.markdown("### Total Beneficiaries by Field Office (2025)")
                st.markdown("---")
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Beneficiaries", f"{total_beneficiaries:,}")
                with col2:
                    st.metric("Total Target", f"{total_target:,}")
                with col3:
                    st.metric("Overall Achievement", f"{total_achievement:.1f}%")
                with col4:
                    st.metric("Field Offices", f"{len(plot_df)}")
                
                st.markdown("---")
                
                # Create visualizations
                plt.style.use('default')
                # Use office colors for consistency
                office_colors = [OFFICE_COORDINATES[office]['color'] for office in plot_df['Office']]
                
                # Row 1: Bar Chart and Pie Chart
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Beneficiaries by Office")
                    fig1, ax1 = plt.subplots(figsize=(8, 6))
                    bars = ax1.bar(plot_df['Office'], plot_df['Beneficiaries'], color=office_colors, edgecolor='black', linewidth=1.5)
                    ax1.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax1.set_ylabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                    ax1.set_title('Beneficiaries by Office', fontsize=14, fontweight='bold')
                    ax1.grid(axis='y', alpha=0.3)
                    ax1.tick_params(axis='x', labelsize=10)
                    
                    for bar in bars:
                        height = bar.get_height()
                        ax1.text(bar.get_x() + bar.get_width()/2., height,
                                 f'{int(height):,}',
                                 ha='center', va='bottom', fontsize=10, fontweight='bold')
                    
                    plt.tight_layout()
                    st.pyplot(fig1)
                
                with col2:
                    st.subheader("🥧 Distribution")
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    wedges, texts, autotexts = ax2.pie(plot_df['Beneficiaries'], 
                                                       labels=plot_df['Office'],
                                                       colors=office_colors,
                                                       autopct='%1.1f%%',
                                                       startangle=90,
                                                       textprops={'fontsize': 10, 'fontweight': 'bold'})
                    ax2.set_title('Beneficiaries Distribution', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig2)
                
                # Row 2: Target vs Achievement and Summary Table
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 Target vs Achievement")
                    fig3, ax3 = plt.subplots(figsize=(8, 6))
                    x = range(len(plot_df))
                    width = 0.35
                    
                    bars1 = ax3.bar([i - width/2 for i in x], plot_df['Target'], width, 
                                     label='Target', color='lightcoral', edgecolor='black', linewidth=1)
                    bars2 = ax3.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width,
                                     label='Achieved', color='lightgreen', edgecolor='black', linewidth=1)
                    
                    ax3.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                    ax3.set_title('Target vs Achievement', fontsize=14, fontweight='bold')
                    ax3.set_xticks(x)
                    ax3.set_xticklabels(plot_df['Office'], fontsize=10)
                    ax3.legend(fontsize=10)
                    ax3.grid(axis='y', alpha=0.3)
                    
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            ax3.text(bar.get_x() + bar.get_width()/2., height,
                                      f'{int(height):,}',
                                      ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
                    plt.tight_layout()
                    st.pyplot(fig3)
                
                with col2:
                    st.subheader("📋 Summary Table")
                    
                    # Create styled dataframe
                    summary_df = plot_df.copy()
                    summary_df['Beneficiaries'] = summary_df['Beneficiaries'].apply(lambda x: f"{x:,}")
                    summary_df['Target'] = summary_df['Target'].apply(lambda x: f"{x:,}")
                    summary_df['Achievement'] = summary_df['Achievement'].apply(lambda x: f"{x:.1f}%")
                    
                    # Add total row
                    total_row = pd.DataFrame([{
                        'Office': 'TOTAL',
                        'Beneficiaries': f"{total_beneficiaries:,}",
                        'Target': f"{total_target:,}",
                        'Achievement': f"{total_achievement:.1f}%"
                    }])
                    
                    summary_df = pd.concat([summary_df, total_row], ignore_index=True)
                    
                    st.dataframe(
                        summary_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Achievement color indicators
                    st.markdown("**Achievement Status:**")
                    st.markdown("🟢 ≥100% | 🟡 75-99% | 🔴 <75%")
                
                # Data Table Section
                st.markdown("---")
                st.subheader("📊 Detailed Data Table (Office Level)")
                
                # Display the main dataframe
                st.dataframe(plot_df, use_container_width=True, hide_index=True)
                
                # Download button
                csv = plot_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Office Data as CSV",
                    data=csv,
                    file_name="wash_beneficiaries_office_2025.csv",
                    mime="text/csv"
                )
            
            # --- PAGE 2: Nepal Map & Palika Analysis (NEW) ---
            elif view_mode == "🗺️ Nepal Map & Palika Analysis":
                st.title("💧 WASH Program Dashboard - Safe Water Access")
                st.markdown("### Field Offices Map and Palika-Level Analysis (2025)")
                st.markdown("---")
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Beneficiaries", f"{total_beneficiaries:,}")
                with col2:
                    st.metric("Total Target", f"{total_target:,}")
                with col3:
                    st.metric("Overall Achievement", f"{total_achievement:.1f}%")
                with col4:
                    st.metric("Total Palikas", f"{total_palikas:,}")
                
                st.markdown("---")
                
                # Tab layout
                tab1, tab2, tab3 = st.tabs(["🗺️ Nepal Map (Office Level)", "📊 Office Summary Charts", "🏘️ Palika Details"])
                
                with tab1:
                    st.subheader("🗺️ Field Offices Distribution in Nepal")
                    st.markdown("**Click on the markers to see detailed information.** Marker size reflects the number of beneficiaries.")
                    
                    # Create and display map
                    nepal_map = create_nepal_map(plot_df, palika_df)
                    st_folium(nepal_map, width=1200, height=600)
                    
                    # Office summary cards below map
                    st.markdown("---")
                    st.subheader("Field Office Summary Quick View")
                    # Dynamically create columns based on number of offices
                    cols = st.columns(len(plot_df)) 
                    
                    for idx, row in plot_df.iterrows():
                        if idx < len(cols):
                            with cols[idx]:
                                office_name = row['Office']
                                color = OFFICE_COORDINATES[office_name]['color']
                                # Recalculate palikas count as a check
                                palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique()) 
                                
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                                    <h3 style="color: {color}; margin: 0;">{office_name}</h3>
                                    <p style="margin: 5px 0;"><b>Beneficiaries:</b> {row['Beneficiaries']:,}</p>
                                    <p style="margin: 5px 0;"><b>Target:</b> {row['Target']:,}</p>
                                    <p style="margin: 5px 0;"><b>Achievement:</b> **{row['Achievement']:.1f}%**</p>
                                    <p style="margin: 5px 0;"><b>Palikas:</b> {palikas_count}</p>
                                </div>
                                """, unsafe_allow_html=True)
                
                with tab2:
                    st.subheader("📊 Office-Level Analysis Charts (Repeated for detail)")
                    # Charts from Page 1 (for consistency/convenience)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Beneficiaries by Office**")
                        fig1, ax1 = plt.subplots(figsize=(8, 6))
                        colors = [OFFICE_COORDINATES[office]['color'] for office in plot_df['Office']]
                        bars = ax1.bar(plot_df['Office'], plot_df['Beneficiaries'], color=colors, edgecolor='black', linewidth=1.5)
                        ax1.set_ylabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax1.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig1)
                    
                    with col2:
                        st.markdown("**Target vs Achievement**")
                        fig2, ax2 = plt.subplots(figsize=(8, 6))
                        x = range(len(plot_df))
                        width = 0.35
                        bars1 = ax2.bar([i - width/2 for i in x], plot_df['Target'], width, label='Target', color='lightcoral', edgecolor='black')
                        bars2 = ax2.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width, label='Achieved', color='lightgreen', edgecolor='black')
                        ax2.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                        ax2.set_xticks(x)
                        ax2.set_xticklabels(plot_df['Office'], fontsize=10)
                        ax2.legend()
                        ax2.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig2)
                
                with tab3:
                    st.subheader("🏘️ Palika-Level Beneficiary Details")
                    
                    # Filter by office
                    selected_office = st.selectbox(
                        "Filter by Field Office:",
                        ["All Offices"] + list(plot_df['Office'].unique())
                    )
                    
                    if selected_office == "All Offices":
                        filtered_palika_df = palika_df
                    else:
                        filtered_palika_df = palika_df[palika_df['Office'] == selected_office]
                        
                    # Summary statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Palikas", len(filtered_palika_df))
                    with col2:
                        st.metric("Total Beneficiaries", f"{filtered_palika_df['Beneficiaries'].sum():,}")
                    with col3:
                        avg_ben = int(filtered_palika_df['Beneficiaries'].mean()) if len(filtered_palika_df) > 0 else 0
                        st.metric("Avg per Palika", f"{avg_ben:,}")
                    
                    st.markdown("---")
                    
                    # Top 10 Palikas chart
                    st.markdown("**Top 10 Palikas by Beneficiaries**")
                    top_10 = filtered_palika_df.head(10).copy()
                    
                    if len(top_10) > 0:
                        # Use mapped colors for Palika chart
                        top_10['Color'] = top_10['Office'].apply(lambda x: OFFICE_COORDINATES.get(x, {}).get('color', 'gray'))
                        
                        fig3, ax3 = plt.subplots(figsize=(12, 6))
                        bars = ax3.barh(top_10['Palika'], top_10['Beneficiaries'], color=top_10['Color'], edgecolor='black')
                        ax3.set_xlabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax3.invert_yaxis()
                        ax3.grid(axis='x', alpha=0.3)
                        
                        # Add office name to the y-label
                        palika_labels = [f"{row['Palika']} ({row['Office']})" for index, row in top_10.iterrows()]
                        ax3.set_yticklabels(palika_labels)
                        
                        for i, bar in enumerate(bars):
                            width = bar.get_width()
                            ax3.text(width, bar.get_y() + bar.get_height()/2.,
                                     f'{int(width):,}',
                                     ha='left', va='center', fontsize=9, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig3)
                    else:
                        st.info("No Palika data to display for the selected filter.")
                    
                    st.markdown("---")
                    
                    # Full palika table
                    st.markdown("**Complete Palika List**")
                    st.dataframe(
                        filtered_palika_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = filtered_palika_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Palika Data as CSV",
                        data=csv,
                        file_name=f"palika_beneficiaries_{selected_office.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
        
        elif page == "3.1.2 Water-safe communities 🏘️":
            # --- Load and Process Data for 3.1.2 ---
            df_raw = load_data(file_path)
            # Use 3.1.2 specific data processing functions
            plot_df = process_office_data_312(df_raw)
            palika_df = process_palika_data_312(df_raw)
            
            # Check if any data exists after filtering
            if plot_df.empty:
                st.warning("⚠️ No data found for 'Water-safe Communities (Yes)' and 'WSC Year 2025' in the loaded file.")
            
            # Display page selection tabs
            view_mode = st.radio(
                "Select View:",
                ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"],
                horizontal=True
            )
            
            st.markdown("---")
            
            # Calculate overall metrics once
            total_beneficiaries = plot_df['Beneficiaries'].sum()
            total_target = plot_df['Target'].sum()
            total_achievement = (total_beneficiaries / total_target * 100) if total_target > 0 else 0
            total_palikas = len(palika_df['Palika'].unique())
            
            # --- PAGE 1: Office Summary Dashboard ---
            if view_mode == "📊 Office Summary Dashboard":
                st.title("💧 WASH Program Dashboard - Water-safe Communities")
                st.markdown("### Total Beneficiaries by Field Office (2025)")
                st.markdown("---")
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Beneficiaries", f"{total_beneficiaries:,}")
                with col2:
                    st.metric("Total Target", f"{total_target:,}")
                with col3:
                    st.metric("Overall Achievement", f"{total_achievement:.1f}%")
                with col4:
                    st.metric("Field Offices", f"{len(plot_df)}")
                
                st.markdown("---")
                
                # Create visualizations
                plt.style.use('default')
                office_colors = [OFFICE_COORDINATES[office]['color'] for office in plot_df['Office']]
                
                # Row 1: Bar Chart and Pie Chart
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Beneficiaries by Office")
                    fig1, ax1 = plt.subplots(figsize=(8, 6))
                    bars = ax1.bar(plot_df['Office'], plot_df['Beneficiaries'], color=office_colors, edgecolor='black', linewidth=1.5)
                    ax1.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax1.set_ylabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                    ax1.set_title('Beneficiaries by Office', fontsize=14, fontweight='bold')
                    ax1.grid(axis='y', alpha=0.3)
                    ax1.tick_params(axis='x', labelsize=10)
                    
                    for bar in bars:
                        height = bar.get_height()
                        ax1.text(bar.get_x() + bar.get_width()/2., height,
                                 f'{int(height):,}',
                                 ha='center', va='bottom', fontsize=10, fontweight='bold')
                    
                    plt.tight_layout()
                    st.pyplot(fig1)
                
                with col2:
                    st.subheader("🥧 Distribution")
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    wedges, texts, autotexts = ax2.pie(plot_df['Beneficiaries'], 
                                                       labels=plot_df['Office'],
                                                       colors=office_colors,
                                                       autopct='%1.1f%%',
                                                       startangle=90,
                                                       textprops={'fontsize': 10, 'fontweight': 'bold'})
                    ax2.set_title('Beneficiaries Distribution', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig2)
                
                # Row 2: Target vs Achievement and Summary Table
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 Target vs Achievement")
                    fig3, ax3 = plt.subplots(figsize=(8, 6))
                    x = range(len(plot_df))
                    width = 0.35
                    
                    bars1 = ax3.bar([i - width/2 for i in x], plot_df['Target'], width, 
                                     label='Target', color='lightcoral', edgecolor='black', linewidth=1)
                    bars2 = ax3.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width,
                                     label='Achieved', color='lightgreen', edgecolor='black', linewidth=1)
                    
                    ax3.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                    ax3.set_title('Target vs Achievement', fontsize=14, fontweight='bold')
                    ax3.set_xticks(x)
                    ax3.set_xticklabels(plot_df['Office'], fontsize=10)
                    ax3.legend(fontsize=10)
                    ax3.grid(axis='y', alpha=0.3)
                    
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            ax3.text(bar.get_x() + bar.get_width()/2., height,
                                      f'{int(height):,}',
                                      ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
                    plt.tight_layout()
                    st.pyplot(fig3)
                
                with col2:
                    st.subheader("📋 Summary Table")
                    
                    # Create styled dataframe
                    summary_df = plot_df.copy()
                    summary_df['Beneficiaries'] = summary_df['Beneficiaries'].apply(lambda x: f"{x:,}")
                    summary_df['Target'] = summary_df['Target'].apply(lambda x: f"{x:,}")
                    summary_df['Achievement'] = summary_df['Achievement'].apply(lambda x: f"{x:.1f}%")
                    
                    # Add total row
                    total_row = pd.DataFrame([{
                        'Office': 'TOTAL',
                        'Beneficiaries': f"{total_beneficiaries:,}",
                        'Target': f"{total_target:,}",
                        'Achievement': f"{total_achievement:.1f}%"
                    }])
                    
                    summary_df = pd.concat([summary_df, total_row], ignore_index=True)
                    
                    st.dataframe(
                        summary_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Achievement color indicators
                    st.markdown("**Achievement Status:**")
                    st.markdown("🟢 ≥100% | 🟡 75-99% | 🔴 <75%")
                
                # Data Table Section
                st.markdown("---")
                st.subheader("📊 Detailed Data Table (Office Level)")
                
                st.dataframe(plot_df, use_container_width=True, hide_index=True)
                
                # Download button
                csv = plot_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Office Data as CSV",
                    data=csv,
                    file_name="wash_water_safe_communities_office_2025.csv",
                    mime="text/csv"
                )
            
            # --- PAGE 2: Nepal Map & Palika Analysis ---
            elif view_mode == "🗺️ Nepal Map & Palika Analysis":
                st.title("💧 WASH Program Dashboard - Water-safe Communities")
                st.markdown("### Field Offices Map and Palika-Level Analysis (2025)")
                st.markdown("---")
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Beneficiaries", f"{total_beneficiaries:,}")
                with col2:
                    st.metric("Total Target", f"{total_target:,}")
                with col3:
                    st.metric("Overall Achievement", f"{total_achievement:.1f}%")
                with col4:
                    st.metric("Total Palikas", f"{total_palikas:,}")
                
                st.markdown("---")
                
                # Tab layout
                tab1, tab2, tab3 = st.tabs(["🗺️ Nepal Map (Office Level)", "📊 Office Summary Charts", "🏘️ Palika Details"])
                
                with tab1:
                    st.subheader("🗺️ Field Offices Distribution in Nepal")
                    st.markdown("**Click on the markers to see detailed information.** Marker size reflects the number of beneficiaries.")
                    
                    # Create and display map
                    nepal_map = create_nepal_map(plot_df, palika_df)
                    st_folium(nepal_map, width=1200, height=600)
                    
                    # Office summary cards below map
                    st.markdown("---")
                    st.subheader("Field Office Summary Quick View")
                    cols = st.columns(len(plot_df)) 
                    
                    for idx, row in plot_df.iterrows():
                        if idx < len(cols):
                            with cols[idx]:
                                office_name = row['Office']
                                color = OFFICE_COORDINATES[office_name]['color']
                                palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique()) 
                                
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                                    <h3 style="color: {color}; margin: 0;">{office_name}</h3>
                                    <p style="margin: 5px 0;"><b>Beneficiaries:</b> {row['Beneficiaries']:,}</p>
                                    <p style="margin: 5px 0;"><b>Target:</b> {row['Target']:,}</p>
                                    <p style="margin: 5px 0;"><b>Achievement:</b> **{row['Achievement']:.1f}%**</p>
                                    <p style="margin: 5px 0;"><b>Palikas:</b> {palikas_count}</p>
                                </div>
                                """, unsafe_allow_html=True)
                
                with tab2:
                    st.subheader("📊 Office-Level Analysis Charts")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Beneficiaries by Office**")
                        fig1, ax1 = plt.subplots(figsize=(8, 6))
                        colors = [OFFICE_COORDINATES[office]['color'] for office in plot_df['Office']]
                        bars = ax1.bar(plot_df['Office'], plot_df['Beneficiaries'], color=colors, edgecolor='black', linewidth=1.5)
                        ax1.set_ylabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax1.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig1)
                    
                    with col2:
                        st.markdown("**Target vs Achievement**")
                        fig2, ax2 = plt.subplots(figsize=(8, 6))
                        x = range(len(plot_df))
                        width = 0.35
                        bars1 = ax2.bar([i - width/2 for i in x], plot_df['Target'], width, label='Target', color='lightcoral', edgecolor='black')
                        bars2 = ax2.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width, label='Achieved', color='lightgreen', edgecolor='black')
                        ax2.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                        ax2.set_xticks(x)
                        ax2.set_xticklabels(plot_df['Office'], fontsize=10)
                        ax2.legend()
                        ax2.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig2)
                
                with tab3:
                    st.subheader("🏘️ Palika-Level Beneficiary Details")
                    
                    # Filter by office
                    selected_office = st.selectbox(
                        "Filter by Field Office:",
                        ["All Offices"] + list(plot_df['Office'].unique())
                    )
                    
                    if selected_office == "All Offices":
                        filtered_palika_df = palika_df
                    else:
                        filtered_palika_df = palika_df[palika_df['Office'] == selected_office]
                        
                    # Summary statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Palikas", len(filtered_palika_df))
                    with col2:
                        st.metric("Total Beneficiaries", f"{filtered_palika_df['Beneficiaries'].sum():,}")
                    with col3:
                        avg_ben = int(filtered_palika_df['Beneficiaries'].mean()) if len(filtered_palika_df) > 0 else 0
                        st.metric("Avg per Palika", f"{avg_ben:,}")
                    
                    st.markdown("---")
                    
                    # Top 10 Palikas chart
                    st.markdown("**Top 10 Palikas by Beneficiaries**")
                    top_10 = filtered_palika_df.head(10).copy()
                    
                    if len(top_10) > 0:
                        top_10['Color'] = top_10['Office'].apply(lambda x: OFFICE_COORDINATES.get(x, {}).get('color', 'gray'))
                        
                        fig3, ax3 = plt.subplots(figsize=(12, 6))
                        bars = ax3.barh(top_10['Palika'], top_10['Beneficiaries'], color=top_10['Color'], edgecolor='black')
                        ax3.set_xlabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax3.invert_yaxis()
                        ax3.grid(axis='x', alpha=0.3)
                        
                        palika_labels = [f"{row['Palika']} ({row['Office']})" for index, row in top_10.iterrows()]
                        ax3.set_yticklabels(palika_labels)
                        
                        for i, bar in enumerate(bars):
                            width = bar.get_width()
                            ax3.text(width, bar.get_y() + bar.get_height()/2.,
                                     f'{int(width):,}',
                                     ha='left', va='center', fontsize=9, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig3)
                    else:
                        st.info("No Palika data to display for the selected filter.")
                    
                    st.markdown("---")
                    
                    # Full palika table
                    st.markdown("**Complete Palika List**")
                    st.dataframe(
                        filtered_palika_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = filtered_palika_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Palika Data as CSV",
                        data=csv,
                        file_name=f"palika_water_safe_communities_{selected_office.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )

        else:
            # Other indicators under Siddhi Shrestha - show "Ongoing"
            display_coming_soon(page)
    
    elif main_menu == "3.2 Dandi Ram":
        display_coming_soon("3.2 Dandi Ram - Dashboard")
    
    elif main_menu == "3.3 Arinita":
        display_coming_soon("3.3 Arinita - Dashboard")
        
    elif main_menu == "End Year Progress against Annual target":
        display_coming_soon("End Year Progress against Annual target")
        
    # Footer
    else:
        st.markdown("**Data loading or indicator under development.**")

    
    # Update footer based on current page
    if main_menu == "3.1 Siddhi Shrestha":
        if page == "3.1.1 Safe water access 🚰":
            st.markdown(f"**Filters Applied:** Completed Projects | Safe Water (Yes) | Year 2025 (Based on WASH.csv)")
        elif page == "3.1.2 Water-safe communities 🏘️":
            st.markdown(f"**Filters Applied:** Community Declared Water Safe (Yes) | WSC Year 2025 (Based on WASH.csv)")
        else:
            st.markdown(f"**Data Source:** {file_path}")
    else:
        st.markdown(f"**Data Source:** {file_path}")
    
    st.caption(f"Data Source: {file_path}")

except FileNotFoundError:
    st.error(f"❌ Error: '{file_path}' file not found.")
    st.info("💡 **해결 방법:**")
    st.write("1. `WASH.csv` 파일이 올바른 위치에 있는지 확인하세요 (예: 현재 디렉토리 또는 data 폴더)")
    st.write("2. 왼쪽 사이드바에서 파일 위치를 변경해보세요")
    st.write("3. 파일 경로를 직접 입력해보세요")
except Exception as e:
    st.error(f"❌ Error loading data or rendering dashboard: {str(e)}")
    # Optional: Display traceback for debugging
    # import traceback
    # st.code(traceback.format_exc())