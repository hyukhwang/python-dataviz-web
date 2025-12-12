import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Page configuration
st.set_page_config(
    page_title="WASH Program Dashboard",
    page_icon="💧",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "Select Page:",
    ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"]
)

st.sidebar.markdown("---")

# Sidebar for file path configuration
st.sidebar.header("⚙️ Configuration")
file_location = st.sidebar.radio(
    "WASH.csv 파일 위치:",
    ["data/WASH.csv", "WASH.csv", "사용자 지정"]
)

if file_location == "사용자 지정":
    custom_path = st.sidebar.text_input("파일 경로 입력:", "data/WASH.csv")
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

# Process data for office summary
@st.cache_data
def process_office_data(df):
    office_col = 'office'
    progress_col = 'progress'
    # 핵심 수정/확인: Safe Water Access 필터링 컬럼
    wq_col = 'water quality test carried out within last one year shows safe water?'
    year_col = 'water supply beneficiaries reporting year'
    total_col = 'total beneficiary population # (current)'
    
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    # Safe water access: 'yes' 필터링을 위해 데이터를 소문자로 정리
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
    
    # 필터링 조건 (Safe water access 포함)
    cond_completed = df[progress_col].str.contains('completed', na=False)
    cond_safe = df[wq_col].str.contains(r'\byes\b', na=False) # 'yes'를 포함하는 경우
    cond_2025 = df[year_col] == 2025
    
    office_mapping = {
        'janakpur': {'name': 'Janakpur', 'target': 7987},
        'dhangadi': {'name': 'Dhangadi', 'target': 6432},
        'bhairahawa': {'name': 'Bhairahawa', 'target': 9659},
        'surkhet': {'name': 'Surkhet', 'target': 13822}
    }
    
    offices = ['janakpur', 'dhangadi', 'bhairahawa', 'surkhet']
    office_data = []
    
    for office_key in offices:
        cond_office = df[office_col].str.contains(office_key, na=False)
        
        # Safe water access: cond_safe를 사용하여 필터링
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

# Process data for palika level (Palika 시각화용 데이터 처리)
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
    
    # 필터링 조건 (Safe water access 포함)
    cond_completed = df[progress_col].str.contains('completed', na=False)
    cond_safe = df[wq_col].str.contains(r'\byes\b', na=False) # 'yes'를 포함하는 경우
    cond_2025 = df[year_col] == 2025
    
    # Safe water access 조건에 맞는 데이터 필터링
    df_filtered = df[cond_completed & cond_safe & cond_2025].copy()
    
    # Standardize office names
    office_mapping = {
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
    
    # Group by palika, district, province and sum beneficiaries
    palika_summary = df_filtered.groupby([
        'office_clean', 
        palika_col, 
        district_col,
        province_col
    ])[total_col].sum().reset_index()
    
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    # Palikas 시각화를 위해 Beneficiaries 기준으로 내림차순 정렬
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False).reset_index(drop=True)
    
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
            # Palikas 수 계산 (Palika 시각화 정보 활용)
            palikas_count = len(palika_df[palika_df['Office'] == office_name])
            
            popup_html = f"""
            <div style="font-family: Arial; min-width: 200px;">
                <h4 style="color: {coords['color']}; margin-bottom: 10px;">{office_name}</h4>
                <b>Province:</b> {coords['province']}<br>
                <b>Total Beneficiaries (Safe Water):</b> {row['Beneficiaries']:,}<br>
                <b>Target:</b> {row['Target']:,}<br>
                <b>Achievement:</b> {row['Achievement']:.1f}%<br>
                <b>Palikas Covered (Safe Water):</b> {palikas_count}
            </div>
            """
            
            folium.CircleMarker(
                location=[coords['lat'], coords['lon']],
                # 원의 크기를 수혜자 수에 비례하도록 조정
                radius=15 + (row['Beneficiaries'] / 3000), 
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

# Main app
try:
    df_raw = load_data(file_path)
    # Safe water access 필터링이 적용된 데이터프레임
    plot_df = process_office_data(df_raw) 
    palika_df = process_palika_data(df_raw) # Palika 시각화 데이터
    
    # PAGE 1: Office Summary Dashboard
    if page == "📊 Office Summary Dashboard":
        st.title("💧 WASH Program Dashboard - Office Summary")
        st.markdown("### Safe Water Beneficiaries by Field Office (2025)")
        st.markdown("---")
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_beneficiaries = plot_df['Beneficiaries'].sum()
        total_target = plot_df['Target'].sum()
        total_achievement = (total_beneficiaries / total_target * 100) if total_target > 0 else 0
        
        with col1:
            st.metric("Total Safe Water Beneficiaries", f"{total_beneficiaries:,}")
        with col2:
            st.metric("Total Target", f"{total_target:,}")
        with col3:
            st.metric("Overall Achievement", f"{total_achievement:.1f}%")
        with col4:
            st.metric("Field Offices", "4")
        
        st.markdown("---")
        
        # Create visualizations (Office Summary)
        plt.style.use('default')
        colors = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']
        
        # Row 1: Bar Chart and Pie Chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Safe Water Beneficiaries by Office")
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            bars = ax1.bar(plot_df['Office'], plot_df['Beneficiaries'], color=colors, edgecolor='black', linewidth=1.5)
            ax1.set_xlabel('Field Office', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Total Beneficiaries', fontsize=12, fontweight='bold')
            ax1.set_title('Beneficiaries by Office (Safe Water)', fontsize=14, fontweight='bold')
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
                                               colors=colors,
                                               autopct='%1.1f%%',
                                               startangle=90,
                                               textprops={'fontsize': 10, 'fontweight': 'bold'})
            ax2.set_title('Beneficiaries Distribution (Safe Water)', fontsize=14, fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig2)
        
        # Row 2: Target vs Achievement and Summary Table
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Target vs Achievement (Safe Water)")
            fig3, ax3 = plt.subplots(figsize=(8, 6))
            x = range(len(plot_df))
            width = 0.35
            
            bars1 = ax3.bar([i - width/2 for i in x], plot_df['Target'], width, 
                            label='Target', color='lightcoral', edgecolor='black', linewidth=1)
            bars2 = ax3.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width,
                            label='Achieved', color='lightgreen', edgecolor='black', linewidth=1)
            
            ax3.set_xlabel('Field Office', fontsize=12, fontweight='bold')
            ax3.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
            ax3.set_title('Target vs Achievement (Safe Water)', fontsize=14, fontweight='bold')
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
            st.markdown("🟢 $\ge$100% | 🟡 75-99% | 🔴 <75%")
        
        # Data Table Section
        st.markdown("---")
        st.subheader("📊 Detailed Data Table (Safe Water)")
        
        # Display the main dataframe
        st.dataframe(plot_df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = plot_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name="wash_safe_water_beneficiaries_2025.csv",
            mime="text/csv"
        )
    
    # PAGE 2: Nepal Map & Palika Analysis
    elif page == "🗺️ Nepal Map & Palika Analysis":
        st.title("💧 WASH Program Dashboard - Nepal Map & Palika Analysis")
        st.markdown("### Safe Water Beneficiaries by Field Office and Palika (2025)")
        st.markdown("---")
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_beneficiaries = plot_df['Beneficiaries'].sum()
        total_target = plot_df['Target'].sum()
        total_achievement = (total_beneficiaries / total_target * 100) if total_target > 0 else 0
        total_palikas = len(palika_df) # Palika 시각화 데이터 활용
        
        with col1:
            st.metric("Total Safe Water Beneficiaries", f"{total_beneficiaries:,}")
        with col2:
            st.metric("Total Target", f"{total_target:,}")
        with col3:
            st.metric("Overall Achievement", f"{total_achievement:.1f}%")
        with col4:
            st.metric("Total Palikas (Safe Water)", f"{total_palikas}")
        
        st.markdown("---")
        
        # Tab layout
        tab1, tab2, tab3 = st.tabs(["🗺️ Nepal Map", "📊 Office Summary", "🏘️ Palika Details"])
        
        with tab1:
            st.subheader("🗺️ Field Offices Distribution in Nepal")
            st.markdown("**Circle size reflects the number of Safe Water Beneficiaries**")
            
            # Create and display map
            nepal_map = create_nepal_map(plot_df, palika_df)
            st_folium(nepal_map, width=1200, height=600)
            
            # Office summary cards below map
            st.markdown("---")
            st.subheader("Field Office Summary")
            cols = st.columns(4)
            
            for idx, row in plot_df.iterrows():
                with cols[idx]:
                    office_name = row['Office']
                    color = OFFICE_COORDINATES[office_name]['color']
                    palikas_count = len(palika_df[palika_df['Office'] == office_name])
                    
                    st.markdown(f"""
                    <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                        <h3 style="color: {color}; margin: 0;">{office_name}</h3>
                        <p style="margin: 5px 0;"><b>Beneficiaries:</b> {row['Beneficiaries']:,}</p>
                        <p style="margin: 5px 0;"><b>Target:</b> {row['Target']:,}</p>
                        <p style="margin: 5px 0;"><b>Achievement:</b> {row['Achievement']:.1f}%</p>
                        <p style="margin: 5px 0;"><b>Palikas:</b> {palikas_count}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab2:
            st.subheader("📊 Office-Level Analysis (Safe Water)")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Safe Water Beneficiaries by Office**")
                fig1, ax1 = plt.subplots(figsize=(8, 6))
                colors_list = [OFFICE_COORDINATES[office]['color'] for office in plot_df['Office']]
                bars = ax1.bar(plot_df['Office'], plot_df['Beneficiaries'], color=colors_list, edgecolor='black', linewidth=1.5)
                ax1.set_ylabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                ax1.grid(axis='y', alpha=0.3)
                
                for bar in bars:
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                             f'{int(height):,}',
                             ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                plt.tight_layout()
                st.pyplot(fig1)
            
            with col2:
                st.markdown("**Target vs Achievement (Safe Water)**")
                fig2, ax2 = plt.subplots(figsize=(8, 6))
                x = range(len(plot_df))
                width = 0.35
                
                bars1 = ax2.bar([i - width/2 for i in x], plot_df['Target'], width, 
                                label='Target', color='lightcoral', edgecolor='black')
                bars2 = ax2.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width,
                                label='Achieved', color='lightgreen', edgecolor='black')
                
                ax2.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                ax2.set_xticks(x)
                ax2.set_xticklabels(plot_df['Office'], fontsize=10)
                ax2.legend()
                ax2.grid(axis='y', alpha=0.3)
                
                plt.tight_layout()
                st.pyplot(fig2)
        
        with tab3:
            st.subheader("🏘️ Palika-Level Safe Water Beneficiary Details")
            
            # Filter by office (Palika 시각화 필터)
            selected_office = st.selectbox(
                "Filter by Field Office:",
                ["All Offices"] + list(plot_df['Office']),
                key='palika_filter'
            )
            
            if selected_office == "All Offices":
                filtered_palika_df = palika_df
            else:
                filtered_palika_df = palika_df[palika_df['Office'] == selected_office].reset_index(drop=True)
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Palikas Covered", len(filtered_palika_df))
            with col2:
                st.metric("Total Beneficiaries", f"{filtered_palika_df['Beneficiaries'].sum():,}")
            with col3:
                avg_ben = int(filtered_palika_df['Beneficiaries'].mean()) if len(filtered_palika_df) > 0 else 0
                st.metric("Avg per Palika", f"{avg_ben:,}")
            
            st.markdown("---")
            
            # Top 10 Palikas chart (Palika 시각화 차트)
            st.markdown("**Top 10 Palikas by Beneficiaries**")
            top_10 = filtered_palika_df.head(10).sort_values('Beneficiaries', ascending=True)
            
            if len(top_10) > 0:
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                # 차트 색상을 해당 Office의 색상으로 지정
                office_colors = {office: OFFICE_COORDINATES[office]['color'] for office in OFFICE_COORDINATES}
                colors_list = [office_colors[office] for office in top_10['Office']]
                bars = ax3.barh(top_10['Palika'], top_10['Beneficiaries'], color=colors_list, edgecolor='black')
                ax3.set_xlabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                ax3.set_title(f'Top 10 Palikas in {selected_office}', fontsize=14, fontweight='bold')
                # ax3.invert_yaxis() # 이미 top_10을 오름차순으로 정렬했으므로 필요 없음
                ax3.grid(axis='x', alpha=0.3)
                
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax3.text(width, bar.get_y() + bar.get_height()/2.,
                             f'{int(width):,}',
                             ha='left', va='center', fontsize=9, fontweight='bold')
                
                # Palika 이름이 길 경우 레이블을 조정하기 위해 tight_layout 적용
                plt.tight_layout()
                st.pyplot(fig3)
            else:
                st.info("선택된 사무소에 해당하는 Palika 데이터가 없습니다.")
            
            st.markdown("---")
            
            # Full palika table (Palika 시각화 테이블)
            st.markdown("**Complete Palika List (Safe Water)**")
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
                file_name=f"palika_safe_water_beneficiaries_{selected_office.replace(' ', '_')}.csv",
                mime="text/csv"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("**Filters Applied:** Completed Projects | Safe Water (Yes) | Year 2025")
    st.caption(f"Data Source: {file_path}")

except FileNotFoundError:
    st.error(f"❌ Error: '{file_path}' file not found.")
    st.info("💡 **해결 방법:**")
    st.write("1. `WASH.csv` 파일이 올바른 위치에 있는지 확인하세요")
    st.write("2. 왼쪽 사이드바에서 파일 위치를 변경해보세요")
    st.write("3. 파일 경로를 직접 입력해보세요")
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    import traceback
    st.code(traceback.format_exc())