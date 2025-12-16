
# app.py (Streamlit WASH Dashboard) - CLEAN & FIXED
# Author: Hyeok Hwang + Copilot
# Last update: 2025-12-16

import os
import re
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="WASH Program Dashboard",
    page_icon="💧",
    layout="wide"
)

# -------------------------------------------------
# Constants / Assumptions
# -------------------------------------------------
SAN_BENEFICIARY_PER_TOILET = 5  # assumption for 3.1.3

SANITATION_TARGETS = {
    'nco': {'name': 'NCO', 'target': 13648},
    'janakpur': {'name': 'Janakpur', 'target': 7987},
    'dhangadi': {'name': 'Dhangadi', 'target': 6432},
    'bhairahawa': {'name': 'Bhairahawa', 'target': 9659},
    'surkhet': {'name': 'Surkhet', 'target': 13822}
}

# -------------------------------------------------
# Sidebar Navigation (요청사항 반영)
# -------------------------------------------------
st.sidebar.title("🧭 Navigation")
main_menu = st.sidebar.selectbox(
    "Select Team:",
    ["3.1 Siddhi Shrestha", "3.2 Dandi Ram", "3.3 Arinita", "Progress against target"]  # 이름 변경 반영
)

st.sidebar.markdown("---")

# 3.1 메뉴(3.1.7 제거)
if main_menu == "3.1 Siddhi Shrestha":
    page = st.sidebar.radio(
        "Select Indicator:",
        [
            "3.1.1 Safe water access 🚰",
            "3.1.2 Water-safe communities 🏘️",
            "3.1.3 Basic sanitation gained ",
            "3.1.4 Schools with WASH ",
            "HCFs with WASH ",
            "3.1.5 Humanitarian water support ",
            "3.1.6 Humanitarian sanitation & hygiene "
        ]
    )

elif main_menu == "3.2 Dandi Ram":
    page = st.sidebar.radio("Select Indicator:", ["Coming Soon..."])

elif main_menu == "3.3 Arinita":
    # Field Office 서브메뉴
    arinita_office = st.sidebar.selectbox(
        "Select Field Office:",
        ["Janakpur", "Dhangadi", "Bhairahawa", "Surkhet"]
    )
    # Arinita 인디케이터
    arinita_indicator = st.sidebar.radio(
        "Select Indicator:",
        ["Flood Map 2024", "Cholera Outbreak 2024", "Groundwater Monitoring"]
    )

st.sidebar.markdown("---")

# -------------------------------------------------
# Sidebar - File config
# -------------------------------------------------
st.sidebar.header("⚙️ Configuration")
file_location = st.sidebar.radio("WASH.csv 파일 위치:", ["WASH.csv", "data/WASH.csv", "사용자 지정"])
if file_location == "사용자 지정":
    custom_path = st.sidebar.text_input("파일 경로 입력:", "WASH.csv")
    file_path = custom_path
else:
    file_path = file_location

# Current working dir / listing
st.sidebar.info(f"**현재 작업 디렉토리:**\n{os.getcwd()}")
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
    except Exception:
        pass

# 컬럼 디버그 표시 여부
show_columns = st.sidebar.checkbox("🔍 CSV 컬럼 확인(디버그)", value=False)

# -------------------------------------------------
# Nepal Field Office Coordinates
# -------------------------------------------------
OFFICE_COORDINATES = {
    'NCO': {'lat': 27.7172, 'lon': 85.3240, 'province': 'Bagmati', 'color': '#4B0082'},
    'Janakpur': {'lat': 26.7288, 'lon': 85.9244, 'province': 'Madhesh', 'color': '#0088FE'},
    'Dhangadi': {'lat': 28.6940, 'lon': 80.5831, 'province': 'Sudurpashchim', 'color': '#00C49F'},
    'Bhairahawa': {'lat': 27.5047, 'lon': 83.4503, 'province': 'Lumbini', 'color': '#FFBB28'},
    'Surkhet': {'lat': 28.6020, 'lon': 81.6177, 'province': 'Karnali', 'color': '#FF8042'}
}

# -------------------------------------------------
# Helpers: Normalize & robust column resolver
# -------------------------------------------------
def _normalize_col(s: str) -> str:
    """소문자화 + 앞뒤 공백 제거 + 다중 공백 축소 + 특수문자 주변 공백 제거 + zero-width 제거"""
    s = str(s)
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s+([\?#])', r'\1', s)  # '?' '#' 앞의 공백 제거
    s = re.sub(r'[\u200B-\u200D\uFEFF]', '', s)  # zero-width 제거
    return s

def robust_rename_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """CSV의 실제 컬럼명을 표준명으로 일괄 rename."""
    current_cols = {_normalize_col(c): c for c in df.columns}
    rename_dict = {}
    for std_name, variants in mapping.items():
        target = None
        for v in variants:
            nv = _normalize_col(v)
            if nv in current_cols:
                target = current_cols[nv]
                break
        if not target:
            std_norm = _normalize_col(std_name)
            for nv_cur, orig in current_cols.items():
                if nv_cur == std_norm or std_norm.rstrip('?') in nv_cur:
                    target = orig
                    break
        if target:
            rename_dict[target] = std_name
    if rename_dict:
        df = df.rename(columns=rename_dict)
    return df

def ensure_columns(df: pd.DataFrame, required: list):
    """필요한 컬럼 확인"""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            "필요 컬럼 누락: "
            + ", ".join(missing)
            + "\n현재 CSV 컬럼(일부): "
            + ", ".join(list(df.columns)[:30])
        )

# -------------------------------------------------
# Data loader
# -------------------------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype=str)
    df.columns = [_normalize_col(c) for c in df.columns]
    df = robust_rename_columns(df, {
        # --- 3.1.2 ---
        'community declared water safe?': [
            'community declared water safe?', 'community declared water safe',
            'is community declared water safe?', 'community declared watersafe?',
            'wsc confirmed water safe?', 'community water safe?'
        ],
        'wsc reporting year': [
            'wsc reporting year', 'water safe community reporting year',
            'wsc (reporting year)', 'reporting year (wsc)', 'year (wsc)'
        ],
        # --- 3.1.3 (NEW) ---
        'additional toilets built': [
            'additional toilets built', 'no. of additional toilets built',
            '# of additional toilets built', 'additional toilets constructed',
            'new toilets built', 'toilets built (additional)'
        ],
        'sanitation beneficiaries reporting year': [
            'sanitation beneficiaries reporting year',
            'reporting year (sanitation beneficiaries)',
            'toilet beneficiaries reporting year',
            'sanitation reporting year',
            'reporting year', 'year', 'year of reporting', 'fiscal year', 'fy'
        ],
        # --- 공통/3.1.1 ---
        'office': ['office', 'field office', 'fo'],
        'palika': ['palika', 'municipality', 'rural municipality'],
        'district': ['district'],
        'province2': ['province2', 'province', 'province name', 'province-2', 'province_no'],
        'total beneficiary population # (current)': [
            'total beneficiary population # (current)',
            'total beneficiary population (current)',
            'total beneficiary population',
            'beneficiary_total_current',
            'total beneficiaries'
        ],
        'progress': ['progress', 'status'],
        'water quality test carried out within last one year shows safe water?': [
            'water quality test carried out within last one year shows safe water?',
            'water quality test safe within last one year?',
            'safe water last year?', 'wqt last one year safe?',
            'water quality test (last one year) safe?'
        ],
        'water supply beneficiaries reporting year': [
            'water supply beneficiaries reporting year',
            'reporting year (water supply beneficiaries)',
            'beneficiaries reporting year', 'wsb reporting year',
            'reporting year', 'year', 'fiscal year', 'fy'
        ],
    })
    return df

# -------------------------------------------------
# Processing: 3.1.2 (Water-safe communities)
# -------------------------------------------------
@st.cache_data
def process_office_data_312(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    wsc_col = 'community declared water safe?'
    wsc_year_col = 'wsc reporting year'
    total_col = 'total beneficiary population # (current)'
    ensure_columns(df, [office_col, wsc_col, wsc_year_col, total_col])

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col] = df[wsc_col].astype(str).str.strip().str.lower()
    df[wsc_year_col] = df[wsc_year_col].astype(str).str.extract(r'(\d{4})', expand=False)
    df[wsc_year_col] = pd.to_numeric(df[wsc_year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_water_safe = df[wsc_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025 = df[wsc_year_col] == 2025

    office_mapping = {
        'nco': {'name': 'NCO', 'target': 13648},
        'janakpur': {'name': 'Janakpur', 'target': 7987},
        'dhangadi': {'name': 'Dhangadi', 'target': 6432},
        'bhairahawa': {'name': 'Bhairahawa', 'target': 9659},
        'surkhet': {'name': 'Surkhet', 'target': 13822}
    }

    office_rows = []
    for key, info in office_mapping.items():
        cond_office = df[office_col].str.contains(rf'\b{re.escape(key)}\b', na=False)
        df_filtered = df[cond_office & cond_water_safe & cond_2025]
        total = df_filtered[total_col].sum()
        target = info['target']
        ach = (total / target * 100) if target > 0 else 0.0
        office_rows.append({
            'Office': info['name'],
            'Beneficiaries': int(total),
            'Target': target,
            'Achievement': ach
        })

    plot_df = pd.DataFrame(office_rows)
    return plot_df[plot_df['Target'] > 0].copy()

@st.cache_data
def process_palika_data_312(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    wsc_col = 'community declared water safe?'
    wsc_year_col = 'wsc reporting year'
    total_col = 'total beneficiary population # (current)'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    ensure_columns(df, [office_col, wsc_col, wsc_year_col, total_col, palika_col, district_col, province_col])

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col] = df[wsc_col].astype(str).str.strip().str.lower()
    df[wsc_year_col] = df[wsc_year_col].astype(str).str.extract(r'(\d{4})', expand=False)
    df[wsc_year_col] = pd.to_numeric(df[wsc_year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_water_safe = df[wsc_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025 = df[wsc_year_col] == 2025
    df_filtered = df[cond_water_safe & cond_2025].copy()

    office_mapping = {
        'nco': 'NCO', 'janakpur': 'Janakpur', 'dhangadi': 'Dhangadi',
        'bhairahawa': 'Bhairahawa', 'surkhet': 'Surkhet'
    }

    def map_office(s: str) -> str:
        lower = str(s).lower()
        for k, v in office_mapping.items():
            if re.search(rf'\b{re.escape(k)}\b', lower):
                return v
        return 'Unknown'

    df_filtered['Office'] = df_filtered[office_col].apply(map_office)

    palika_summary = (
        df_filtered
        .groupby(['Office', palika_col, district_col, province_col])[total_col]
        .sum()
        .reset_index()
    )
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    palika_summary = palika_summary[palika_summary['Office'] != 'Unknown']
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)
    return palika_summary

# -------------------------------------------------
# Processing: 3.1.1 (Safe water access)
# -------------------------------------------------
@st.cache_data
def process_office_data(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    progress_col = 'progress'
    wq_col = 'water quality test carried out within last one year shows safe water?'
    year_col = 'water supply beneficiaries reporting year'
    total_col = 'total beneficiary population # (current)'
    ensure_columns(df, [office_col, progress_col, wq_col, year_col, total_col])

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[wq_col] = df[wq_col].astype(str).str.strip().str.lower()
    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})', expand=False)
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_safe = df[wq_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025 = df[year_col] == 2025

    office_mapping = {
        'nco': {'name': 'NCO', 'target': 13648},
        'janakpur': {'name': 'Janakpur', 'target': 7987},
        'dhangadi': {'name': 'Dhangadi', 'target': 6432},
        'bhairahawa': {'name': 'Bhairahawa', 'target': 9659},
        'surkhet': {'name': 'Surkhet', 'target': 13822}
    }

    office_rows = []
    for key, info in office_mapping.items():
        cond_office = df[office_col].str.contains(rf'\b{re.escape(key)}\b', na=False)
        df_filtered = df[cond_office & cond_completed & cond_safe & cond_2025]
        total = df_filtered[total_col].sum()
        target = info['target']
        ach = (total / target * 100) if target > 0 else 0.0
        office_rows.append({
            'Office': info['name'],
            'Beneficiaries': int(total),
            'Target': target,
            'Achievement': ach
        })

    plot_df = pd.DataFrame(office_rows)
    return plot_df[plot_df['Target'] > 0].copy()

@st.cache_data
def process_palika_data(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    progress_col = 'progress'
    wq_col = 'water quality test carried out within last one year shows safe water?'
    year_col = 'water supply beneficiaries reporting year'
    total_col = 'total beneficiary population # (current)'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'
    ensure_columns(df, [office_col, progress_col, wq_col, year_col, total_col, palika_col, district_col, province_col])

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[wq_col] = df[wq_col].astype(str).str.strip().str.lower()
    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})', expand=False)
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_safe = df[wq_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025 = df[year_col] == 2025

    df_filtered = df[cond_completed & cond_safe & cond_2025].copy()

    office_mapping = {
        'nco': 'NCO', 'janakpur': 'Janakpur', 'dhangadi': 'Dhangadi',
        'bhairahawa': 'Bhairahawa', 'surkhet': 'Surkhet'
    }

    def map_office(s: str) -> str:
        lower = str(s).lower()
        for k, v in office_mapping.items():
            if re.search(rf'\b{re.escape(k)}\b', lower):
                return v
        return 'Unknown'

    df_filtered['Office'] = df_filtered[office_col].apply(map_office)

    palika_summary = (
        df_filtered
        .groupby(['Office', palika_col, district_col, province_col])[total_col]
        .sum()
        .reset_index()
    )
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].astype(int)
    palika_summary = palika_summary[palika_summary['Office'] != 'Unknown']
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)
    return palika_summary

# -------------------------------------------------
# Processing: 3.1.3 (Basic sanitation gained)
# -------------------------------------------------
@st.cache_data
def process_office_data_313(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    progress_col = 'progress'
    toilets_col = 'additional toilets built'
    year_col = 'sanitation beneficiaries reporting year'

    if year_col not in df.columns:
        st.warning(
            "ℹ️ 'sanitation beneficiaries reporting year' 컬럼이 없어 2025로 폴백 적용했습니다. "
            "CSV에 실제 연도 컬럼이 있다면 알려주세요. 곧 연결해 드리겠습니다."
        )
        df[year_col] = '2025'

    ensure_columns(df, [office_col, progress_col, toilets_col, year_col])

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})', expand=False)
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[toilets_col] = (
        df[toilets_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[toilets_col] = pd.to_numeric(df[toilets_col], errors='coerce').fillna(0)

    df['_beneficiaries_313'] = (df[toilets_col] * SAN_BENEFICIARY_PER_TOILET).astype(float)

    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_2025 = df[year_col] == 2025

    office_rows = []
    for key, info in SANITATION_TARGETS.items():
        cond_office = df[office_col].str.contains(rf'\b{re.escape(key)}\b', na=False)
        df_filtered = df[cond_office & cond_completed & cond_2025]
        total = df_filtered['_beneficiaries_313'].sum()
        target = info['target']
        ach = (total / target * 100) if target > 0 else 0.0
        office_rows.append({
            'Office': info['name'],
            'Beneficiaries': int(round(total)),
            'Target': target,
            'Achievement': ach
        })

    plot_df = pd.DataFrame(office_rows)
    return plot_df[plot_df['Target'] > 0].copy()

@st.cache_data
def process_palika_data_313(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    progress_col = 'progress'
    toilets_col = 'additional toilets built'
    year_col = 'sanitation beneficiaries reporting year'
    palika_col = 'palika'
    district_col = 'district'
    province_col = 'province2'

    if year_col not in df.columns:
        st.warning(
            "ℹ️ 'sanitation beneficiaries reporting year' 컬럼이 없어 2025로 폴백 적용했습니다. "
            "CSV에 실제 연도 컬럼이 있다면 알려주세요. 곧 연결해 드리겠습니다."
        )
        df[year_col] = '2025'

    ensure_columns(df, [office_col, progress_col, toilets_col, year_col, palika_col, district_col, province_col])

    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})', expand=False)
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[toilets_col] = (
        df[toilets_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[toilets_col] = pd.to_numeric(df[toilets_col], errors='coerce').fillna(0)

    df['_beneficiaries_313'] = (df[toilets_col] * SAN_BENEFICIARY_PER_TOILET).astype(float)

    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_2025 = df[year_col] == 2025
    df_filtered = df[cond_completed & cond_2025].copy()

    office_mapping = {
        'nco': 'NCO', 'janakpur': 'Janakpur', 'dhangadi': 'Dhangadi',
        'bhairahawa': 'Bhairahawa', 'surkhet': 'Surkhet'
    }

    def map_office(s: str) -> str:
        lower = str(s).lower()
        for k, v in office_mapping.items():
            if re.search(rf'\b{re.escape(k)}\b', lower):
                return v
        return 'Unknown'

    df_filtered['Office'] = df_filtered[office_col].apply(map_office)

    palika_summary = (
        df_filtered
        .groupby(['Office', palika_col, district_col, province_col])['_beneficiaries_313']
        .sum()
        .reset_index()
    )
    palika_summary.columns = ['Office', 'Palika', 'District', 'Province', 'Beneficiaries']
    palika_summary['Beneficiaries'] = palika_summary['Beneficiaries'].round().astype(int)
    palika_summary = palika_summary[palika_summary['Office'] != 'Unknown']
    palika_summary = palika_summary.sort_values('Beneficiaries', ascending=False)
    return palika_summary

# -------------------------------------------------
# Map builder
# -------------------------------------------------
def create_nepal_map(office_df: pd.DataFrame, palika_df: pd.DataFrame):
    nepal_map = folium.Map(location=[28.3949, 84.1240], zoom_start=7, tiles='OpenStreetMap')

    for _, row in office_df.iterrows():
        office_name = row['Office']
        coords = OFFICE_COORDINATES.get(office_name, None)
        color = (coords or {}).get('color', '#555555')
        province = (coords or {}).get('province', 'Unknown')
        lat = (coords or {}).get('lat', 28.3949)
        lon = (coords or {}).get('lon', 84.1240)

