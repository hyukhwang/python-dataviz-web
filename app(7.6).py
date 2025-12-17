
# app.py (Streamlit WASH Dashboard) - Added 3.1.3 Basic sanitation gained with robust year fallback
# Author: Hyeok Hwang + Copilot
# Last update: 2025-12-15

import os
import re
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# ------------------------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="WASH Program Dashboard",
    page_icon="💧",
    layout="wide"
)

# ------------------------------------------------------------------------------
# Constants / Assumptions
# ------------------------------------------------------------------------------
# Assumption for 3.1.3:
SAN_BENEFICIARY_PER_TOILET = 5  # assumption: 5 people benefit per additional toilet

# Default office targets (adjust as needed for sanitation)
SANITATION_TARGETS = {
    'nco':       {'name': 'NCO',        'target': 13648},
    'janakpur':  {'name': 'Janakpur',   'target': 7987},
    'dhangadi':  {'name': 'Dhangadi',   'target': 6432},
    'bhairahawa':{'name': 'Bhairahawa', 'target': 9659},
    'surkhet':   {'name': 'Surkhet',    'target': 13822}
}

# ------------------------------------------------------------------------------
# Sidebar Navigation
# ------------------------------------------------------------------------------
st.sidebar.title("🧭 Navigation")

main_menu = st.sidebar.selectbox("Select Team:", ["3.1 Siddhi Shrestha", "3.2 Dandi Ram", "Janakpur", "Dhangadi", "Bhairahawa", "Surkhet", "End Year Progress against Annual target"])
st.sidebar.markdown("---")

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
            "3.1.6 Humanitarian sanitation & hygiene ",
           
        ]
    )
elif main_menu == "3.2 Dandi Ram":
    page = st.sidebar.radio("Select Indicator:", ["LGPAS", "Palikas"])
elif main_menu == "3.3 Arinita":
    page = st.sidebar.radio("Select Indicator:", ["Coming Soon..."])

st.sidebar.markdown("---")

# ------------------------------------------------------------------------------
# Sidebar - File config
# ------------------------------------------------------------------------------
st.sidebar.header("⚙️ Configuration")
file_location = st.sidebar.radio("WASH.csv 파일 위치:", ["WASH.csv", "data/WASH.csv", "사용자 지정"])

if file_location == "사용자 지정":
    custom_path = st.sidebar.text_input("파일 경로 입력:", "WASH.csv")
    file_path = custom_path
else:
    file_path = file_location

# Show current working directory & quick listing
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

# ------------------------------------------------------------------------------
# Nepal Field Office Coordinates
# ------------------------------------------------------------------------------
OFFICE_COORDINATES = {
    'NCO':        {'lat': 27.7172, 'lon': 85.3240, 'province': 'Bagmati',       'color': '#4B0082'},
    'Janakpur':   {'lat': 26.7288, 'lon': 85.9244, 'province': 'Madhesh',        'color': '#0088FE'},
    'Dhangadi':   {'lat': 28.6940, 'lon': 80.5831, 'province': 'Sudurpashchim',  'color': '#00C49F'},
    'Bhairahawa': {'lat': 27.5047, 'lon': 83.4503, 'province': 'Lumbini',        'color': '#FFBB28'},
    'Surkhet':    {'lat': 28.6020, 'lon': 81.6177, 'province': 'Karnali',        'color': '#FF8042'}
}

# ------------------------------------------------------------------------------
# Helpers: Normalize & robust column resolver
# ------------------------------------------------------------------------------
def _normalize_col(s: str) -> str:
    """소문자화 + 앞뒤 공백 제거 + 다중 공백 축소 + 특수문자 주변 공백 제거 + zero-width 제거"""
    s = str(s)
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s+([?#])', r'\1', s)  # '?' '#' 앞의 공백 제거
    s = re.sub(r'[\u200B-\u200D\uFEFF]', '', s)  # zero-width 제거
    return s

def robust_rename_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    mapping: {'표준명(정확히 사용될 이름)': [가능한 변형들]}
    CSV의 실제 컬럼명을 표준명으로 일괄 rename.
    """
    current_cols = { _normalize_col(c): c for c in df.columns }
    rename_dict = {}

    for std_name, variants in mapping.items():
        target = None
        # 1) 사전 정의 변형에서 탐색
        for v in variants:
            nv = _normalize_col(v)
            if nv in current_cols:
                target = current_cols[nv]
                break
        # 2) 느슨한 탐색(부분일치/물음표 유무)
        if not target:
            std_norm = _normalize_col(std_name)
            for nv_cur, orig in current_cols.items():
                if nv_cur == std_norm:
                    target = orig; break
                if std_norm.rstrip('?') in nv_cur:
                    target = orig; break

        if target:
            rename_dict[target] = std_name

    if rename_dict:
        df = df.rename(columns=rename_dict)

    return df

def ensure_columns(df: pd.DataFrame, required: list):
    """필요한 컬럼이 모두 있는지 확인하고 없으면 자세한 메시지로 에러 발생"""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            "필요 컬럼 누락: "
            + ", ".join(missing)
            + "\n현재 CSV 컬럼(일부): "
            + ", ".join(list(df.columns)[:30])
        )

# ------------------------------------------------------------------------------
# Data loader
# ------------------------------------------------------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, dtype=str)
    # 1) 1차 정리(소문자/공백)
    df.columns = [ _normalize_col(c) for c in df.columns ]

    # 2) 표준 컬럼명으로 강건하게 rename
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
            # 일반화된 연도 표기(폴백 지원)
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
            # 일반화된 연도 표기
            'reporting year', 'year', 'fiscal year', 'fy'
        ],
    })

    return df

# ------------------------------------------------------------------------------
# Processing: 3.1.2 (Water-safe communities)
# ------------------------------------------------------------------------------
@st.cache_data
def process_office_data_312(df: pd.DataFrame) -> pd.DataFrame:
    office_col = 'office'
    wsc_col = 'community declared water safe?'
    wsc_year_col = 'wsc reporting year'
    total_col = 'total beneficiary population # (current)'

    ensure_columns(df, [office_col, wsc_col, wsc_year_col, total_col])

    # Cleaning
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col] = df[wsc_col].astype(str).str.strip().str.lower()

    # Year: 괄호 유무 모두 허용
    df[wsc_year_col] = df[wsc_year_col].astype(str).str.extract(r'(\d{4})')[0]
    df[wsc_year_col] = pd.to_numeric(df[wsc_year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    # Filters
    cond_water_safe = df[wsc_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025 = df[wsc_year_col] == 2025

    office_mapping = {
        'nco':       {'name': 'NCO',        'target': 13648},
        'janakpur':  {'name': 'Janakpur',   'target': 7987},
        'dhangadi':  {'name': 'Dhangadi',   'target': 6432},
        'bhairahawa':{'name': 'Bhairahawa', 'target': 9659},
        'surkhet':   {'name': 'Surkhet',    'target': 13822}
    }
    offices = list(office_mapping.keys())

    office_rows = []
    for key in offices:
        cond_office = df[office_col].str.contains(rf'\b{re.escape(key)}\b', na=False)
        df_filtered = df[cond_office & cond_water_safe & cond_2025]
        total = df_filtered[total_col].sum()

        info = office_mapping[key]
        target = info['target']
        ach = (total / target * 100) if target > 0 else 0.0

        office_rows.append({
            'Office': info['name'],
            'Beneficiaries': int(total),
            'Target': target,
            'Achievement': ach
        })

    plot_df = pd.DataFrame(office_rows)
    plot_df_filtered = plot_df[plot_df['Target'] > 0].copy()
    return plot_df_filtered

@st.cache_data
def process_palika_data_312(df: pd.DataFrame) -> pd.DataFrame:
    office_col   = 'office'
    wsc_col      = 'community declared water safe?'
    wsc_year_col = 'wsc reporting year'
    total_col    = 'total beneficiary population # (current)'
    palika_col   = 'palika'
    district_col = 'district'
    province_col = 'province2'

    ensure_columns(df, [office_col, wsc_col, wsc_year_col, total_col, palika_col, district_col, province_col])

    # Cleaning
    df[office_col] = df[office_col].astype(str).str.strip().str.lower()
    df[wsc_col]    = df[wsc_col].astype(str).str.strip().str.lower()

    df[wsc_year_col] = df[wsc_year_col].astype(str).str.extract(r'(\d{4})')[0]
    df[wsc_year_col] = pd.to_numeric(df[wsc_year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    # Filters
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

# ------------------------------------------------------------------------------
# Processing: 3.1.1 (Safe water access)
# ------------------------------------------------------------------------------
@st.cache_data
def process_office_data(df: pd.DataFrame) -> pd.DataFrame:
    office_col  = 'office'
    progress_col= 'progress'
    wq_col      = 'water quality test carried out within last one year shows safe water?'
    year_col    = 'water supply beneficiaries reporting year'
    total_col   = 'total beneficiary population # (current)'

    ensure_columns(df, [office_col, progress_col, wq_col, year_col, total_col])

    # Cleaning
    df[office_col]   = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[wq_col]       = df[wq_col].astype(str).str.strip().str.lower()

    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')[0]
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    # Filters
    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_safe      = df[wq_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025      = df[year_col] == 2025

    office_mapping = {
        'nco':       {'name': 'NCO',        'target': 13648},
        'janakpur':  {'name': 'Janakpur',   'target': 7987},
        'dhangadi':  {'name': 'Dhangadi',   'target': 6432},
        'bhairahawa':{'name': 'Bhairahawa', 'target': 9659},
        'surkhet':   {'name': 'Surkhet',    'target': 13822}
    }
    offices = list(office_mapping.keys())

    office_rows = []
    for key in offices:
        cond_office = df[office_col].str.contains(rf'\b{re.escape(key)}\b', na=False)
        df_filtered = df[cond_office & cond_completed & cond_safe & cond_2025]
        total = df_filtered[total_col].sum()

        info = office_mapping[key]
        target = info['target']
        ach = (total / target * 100) if target > 0 else 0.0

        office_rows.append({
            'Office': info['name'],
            'Beneficiaries': int(total),
            'Target': target,
            'Achievement': ach
        })

    plot_df = pd.DataFrame(office_rows)
    plot_df_filtered = plot_df[plot_df['Target'] > 0].copy()
    return plot_df_filtered

@st.cache_data
def process_palika_data(df: pd.DataFrame) -> pd.DataFrame:
    office_col  = 'office'
    progress_col= 'progress'
    wq_col      = 'water quality test carried out within last one year shows safe water?'
    year_col    = 'water supply beneficiaries reporting year'
    total_col   = 'total beneficiary population # (current)'
    palika_col  = 'palika'
    district_col= 'district'
    province_col= 'province2'

    ensure_columns(df, [office_col, progress_col, wq_col, year_col, total_col, palika_col, district_col, province_col])

    # Cleaning
    df[office_col]   = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()
    df[wq_col]       = df[wq_col].astype(str).str.strip().str.lower()

    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')[0]
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[total_col] = (
        df[total_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)

    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_safe      = df[wq_col].str.contains(r'\b(yes|y)\b', na=False)
    cond_2025      = df[year_col] == 2025
    df_filtered    = df[cond_completed & cond_safe & cond_2025].copy()

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

# ------------------------------------------------------------------------------
# Processing: 3.1.3 (Basic sanitation gained)  NEW
# ------------------------------------------------------------------------------
@st.cache_data
def process_office_data_313(df: pd.DataFrame) -> pd.DataFrame:
    """
    Beneficiaries are calculated as: additional_toilets_built * SAN_BENEFICIARY_PER_TOILET
    Filters mirror the structure used in 3.1.1/3.1.2 (completed + year 2025).
    """
    office_col   = 'office'
    progress_col = 'progress'
    toilets_col  = 'additional toilets built'
    year_col     = 'sanitation beneficiaries reporting year'

    # ── 연도 컬럼 폴백: 없으면 생성(2025) + 경고 ──
    if year_col not in df.columns:
        st.warning("ℹ️ 'sanitation beneficiaries reporting year' 컬럼이 없어 2025로 폴백 적용했습니다. "
                   "CSV에 실제 연도 컬럼이 있다면 알려주세요. 곧 연결해 드리겠습니다.")
        df[year_col] = '2025'

    ensure_columns(df, [office_col, progress_col, toilets_col, year_col])

    # Cleaning
    df[office_col]   = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()

    # year normalization
    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')[0]
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    # toilets numeric
    df[toilets_col] = (
        df[toilets_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[toilets_col] = pd.to_numeric(df[toilets_col], errors='coerce').fillna(0)

    # Beneficiaries derived
    df['_beneficiaries_313'] = (df[toilets_col] * SAN_BENEFICIARY_PER_TOILET).astype(float)

    # Filters
    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_2025      = df[year_col] == 2025

    offices = list(SANITATION_TARGETS.keys())
    office_rows = []
    for key in offices:
        cond_office = df[office_col].str.contains(rf'\b{re.escape(key)}\b', na=False)
        df_filtered = df[cond_office & cond_completed & cond_2025]
        total = df_filtered['_beneficiaries_313'].sum()

        info = SANITATION_TARGETS[key]
        target = info['target']
        ach = (total / target * 100) if target > 0 else 0.0

        office_rows.append({
            'Office': info['name'],
            'Beneficiaries': int(round(total)),
            'Target': target,
            'Achievement': ach
        })

    plot_df = pd.DataFrame(office_rows)
    plot_df_filtered = plot_df[plot_df['Target'] > 0].copy()
    return plot_df_filtered

@st.cache_data
def process_palika_data_313(df: pd.DataFrame) -> pd.DataFrame:
    """
    Palika-level beneficiaries for 3.1.3 using the same derivation:
    beneficiaries = additional_toilets_built * SAN_BENEFICIARY_PER_TOILET
    """
    office_col   = 'office'
    progress_col = 'progress'
    toilets_col  = 'additional toilets built'
    year_col     = 'sanitation beneficiaries reporting year'
    palika_col   = 'palika'
    district_col = 'district'
    province_col = 'province2'

    # ── 연도 컬럼 폴백: 없으면 생성(2025) + 경고 ──
    if year_col not in df.columns:
        st.warning("ℹ️ 'sanitation beneficiaries reporting year' 컬럼이 없어 2025로 폴백 적용했습니다. "
                   "CSV에 실제 연도 컬럼이 있다면 알려주세요. 곧 연결해 드리겠습니다.")
        df[year_col] = '2025'

    ensure_columns(df, [office_col, progress_col, toilets_col, year_col, palika_col, district_col, province_col])

    # Cleaning
    df[office_col]   = df[office_col].astype(str).str.strip().str.lower()
    df[progress_col] = df[progress_col].astype(str).str.strip().str.lower()

    df[year_col] = df[year_col].astype(str).str.extract(r'(\d{4})')[0]
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')

    df[toilets_col] = (
        df[toilets_col].astype(str)
        .str.replace(r'[^\d.]', '', regex=True)
        .replace('', '0')
    )
    df[toilets_col] = pd.to_numeric(df[toilets_col], errors='coerce').fillna(0)

    # Beneficiaries derived
    df['_beneficiaries_313'] = (df[toilets_col] * SAN_BENEFICIARY_PER_TOILET).astype(float)

    # Filters
    cond_completed = df[progress_col].str.contains(r'\bcompleted\b', na=False)
    cond_2025      = df[year_col] == 2025
    df_filtered    = df[cond_completed & cond_2025].copy()

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

# ------------------------------------------------------------------------------
# Map builder
# ------------------------------------------------------------------------------
def create_nepal_map(office_df: pd.DataFrame, palika_df: pd.DataFrame):
    nepal_map = folium.Map(location=[28.3949, 84.1240], zoom_start=7, tiles='OpenStreetMap')

    for _, row in office_df.iterrows():
        office_name = row['Office']
        coords = OFFICE_COORDINATES.get(office_name, None)
        color = (coords or {}).get('color', '#555555')
        province = (coords or {}).get('province', 'Unknown')
        lat = (coords or {}).get('lat', 28.3949)
        lon = (coords or {}).get('lon', 84.1240)

        palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique())

        popup_html = f"""
        <div style="font-family: Arial; min-width: 220px;">
            <h4 style="color: {color}; margin-bottom: 10px;">{office_name}</h4>
            <b>Province:</b> {province}<br>
            <b>Total Beneficiaries (2025):</b> {row['Beneficiaries']:,}<br>
            <b>Target:</b> {row['Target']:,}<br>
            <b>Achievement:</b> {row['Achievement']:.1f}%<br>
            <b>Palikas Covered:</b> {palikas_count}
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=10 + (row['Beneficiaries'] / 3000.0),
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(nepal_map)

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=f"""
                <div style="font-size: 10pt; color: {color};
                            font-weight: bold; text-shadow: 1px 1px 2px white;
                            margin-left: 15px; margin-top: -10px;">
                    {office_name} ({row['Achievement']:.0f}%)
                </div>
            """)
        ).add_to(nepal_map)

    # Legend
    legend_html = '''
    <div style="position: fixed;
        bottom: 50px; left: 50px;
        border: 2px solid grey; z-index: 9999;
        background-color: white;
        padding: 10px;
        font-size: 14px;
        border-radius: 5px;">
        <p style="margin-bottom: 5px;"><b>Field Offices</b></p>
    '''
    for office, c in OFFICE_COORDINATES.items():
        legend_html += f'<p style="margin: 3px;"><span style="color:{c["color"]}; font-size: 20px;">●</span> {office} ({c["province"]})</p>'
    legend_html += '</div>'

    nepal_map.get_root().html.add_child(folium.Element(legend_html))
    return nepal_map

# ------------------------------------------------------------------------------
# Coming soon
# ------------------------------------------------------------------------------
def display_coming_soon(title: str):
    st.title(f"{title}")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("### 🚧 Under Development")
        st.markdown("""
        이 섹션은 현재 개발 중이며 곧 제공될 예정입니다.  
        **Status:** Ongoing  
        업데이트를 위해 나중에 다시 확인해 주세요.
        """)
    st.markdown("---")
    st.markdown("**Contact:** For more information, please contact the program team.")

# ------------------------------------------------------------------------------
# Main app logic
# ------------------------------------------------------------------------------
try:
    if main_menu == "3.1 Siddhi Shrestha":

        # -------------------- 3.1.1 --------------------
        if page == "3.1.1 Safe water access 🚰":
            df_raw = load_data(file_path)
            if show_columns:
                st.sidebar.write("📄 CSV Columns (현재 표준명 적용 후):")
                st.sidebar.write(list(df_raw.columns))
            plot_df = process_office_data(df_raw)
            palika_df = process_palika_data(df_raw)

            if plot_df.empty:
                st.warning("⚠️ 'Completed Projects', 'Safe Water (Yes/Y)', 'Year 2025' 조건을 만족하는 데이터가 없습니다.")

            view_mode = st.radio("Select View:", ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"], horizontal=True)
            st.markdown("---")

            total_ben = plot_df['Beneficiaries'].sum()
            total_target = plot_df['Target'].sum()
            total_ach = (total_ben / total_target * 100) if total_target > 0 else 0.0
            total_palikas = len(palika_df['Palika'].unique())

            if view_mode == "📊 Office Summary Dashboard":
                st.title("💧 WASH Program Dashboard - Safe Water Access")
                st.markdown("### Total Beneficiaries by Field Office (2025)")
                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Beneficiaries", f"{total_ben:,}")
                with c2: st.metric("Total Target", f"{total_target:,}")
                with c3: st.metric("Overall Achievement", f"{total_ach:.1f}%")
                with c4: st.metric("Field Offices", f"{len(plot_df)}")

                st.markdown("---")

                plt.style.use('default')
                office_colors = [OFFICE_COORDINATES.get(o, {}).get('color', '#888888') for o in plot_df['Office']]

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
                    for b in bars:
                        h = b.get_height()
                        ax1.text(b.get_x() + b.get_width()/2., h, f'{int(h):,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig1)
                with col2:
                    st.subheader("🥧 Distribution")
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    ax2.pie(
                        plot_df['Beneficiaries'],
                        labels=plot_df['Office'],
                        colors=office_colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        textprops={'fontsize': 10, 'fontweight': 'bold'}
                    )
                    ax2.set_title('Beneficiaries Distribution', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig2)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🎯 Target vs Achievement")
                    fig3, ax3 = plt.subplots(figsize=(8, 6))
                    x = range(len(plot_df))
                    width = 0.35
                    bars1 = ax3.bar([i - width/2 for i in x], plot_df['Target'], width, label='Target', color='lightcoral', edgecolor='black', linewidth=1)
                    bars2 = ax3.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width, label='Achieved', color='lightgreen', edgecolor='black', linewidth=1)
                    ax3.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                    ax3.set_title('Target vs Achievement', fontsize=14, fontweight='bold')
                    ax3.set_xticks(list(x))
                    ax3.set_xticklabels(plot_df['Office'], fontsize=10)
                    ax3.legend(fontsize=10)
                    ax3.grid(axis='y', alpha=0.3)
                    for bars in [bars1, bars2]:
                        for b in bars:
                            h = b.get_height()
                            ax3.text(b.get_x() + b.get_width()/2., h, f'{int(h):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig3)
                with col2:
                    st.subheader("📋 Summary Table")
                    summary_df = plot_df.copy()
                    summary_df['Beneficiaries'] = summary_df['Beneficiaries'].apply(lambda x: f"{x:,}")
                    summary_df['Target']        = summary_df['Target'].apply(lambda x: f"{x:,}")
                    summary_df['Achievement']   = summary_df['Achievement'].apply(lambda x: f"{x:.1f}%")

                    total_row = pd.DataFrame([{
                        'Office': 'TOTAL',
                        'Beneficiaries': f"{total_ben:,}",
                        'Target': f"{total_target:,}",
                        'Achievement': f"{total_ach:.1f}%"
                    }])
                    summary_df = pd.concat([summary_df, total_row], ignore_index=True)

                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

                    st.markdown("**Achievement Status:**")
                    st.markdown("🟢 ≥100%  \n🟡 75-99%  \n🔴 <75%")

                    st.markdown("---")
                    st.subheader("📊 Detailed Data Table (Office Level)")
                    st.dataframe(plot_df, use_container_width=True, hide_index=True)

                    csv = plot_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Office Data as CSV",
                        data=csv,
                        file_name="wash_beneficiaries_office_2025.csv",
                        mime="text/csv"
                    )

            elif view_mode == "🗺️ Nepal Map & Palika Analysis":
                st.title("💧 WASH Program Dashboard - Safe Water Access")
                st.markdown("### Field Offices Map and Palika-Level Analysis (2025)")
                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Beneficiaries", f"{total_ben:,}")
                with c2: st.metric("Total Target", f"{total_target:,}")
                with c3: st.metric("Overall Achievement", f"{total_ach:.1f}%")
                with c4: st.metric("Total Palikas", f"{total_palikas:,}")

                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["🗺️ Nepal Map (Office Level)", "📊 Office Summary Charts", "🏘️ Palika Details"])

                with tab1:
                    st.subheader("🗺️ Field Offices Distribution in Nepal")
                    st.markdown("**마커를 클릭하면 상세 정보를 볼 수 있습니다.** 마커 크기는 수혜자 수를 반영합니다.")
                    nepal_map = create_nepal_map(plot_df, palika_df)
                    st_folium(nepal_map, width=1200, height=600)

                    st.markdown("---")
                    st.subheader("Field Office Summary Quick View")
                    cols = st.columns(len(plot_df) if len(plot_df) > 0 else 1)
                    for idx, row in plot_df.iterrows():
                        if idx < len(cols):
                            with cols[idx]:
                                office_name = row['Office']
                                color = OFFICE_COORDINATES.get(office_name, {}).get('color', '#888888')
                                palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique())
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                                    <h3 style="color: {color}; margin: 0;">{office_name}</h3>
                                    <p style="margin: 5px 0;"><b>Beneficiaries:</b> {row['Beneficiaries']:,}</p>
                                    <p style="margin: 5px 0;"><b>Target:</b> {row['Target']:,}</p>
                                    <p style="margin: 5px 0;"><b>Achievement:</b> <b>{row['Achievement']:.1f}%</b></p>
                                    <p style="margin: 5px 0;"><b>Palikas:</b> {palikas_count}</p>
                                </div>
                                """, unsafe_allow_html=True)

                with tab2:
                    st.subheader("📊 Office-Level Analysis Charts")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Beneficiaries by Office**")
                        fig1, ax1 = plt.subplots(figsize=(8, 6))
                        colors = [OFFICE_COORDINATES.get(o, {}).get('color', '#888888') for o in plot_df['Office']]
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
                        ax2.set_xticks(list(x))
                        ax2.set_xticklabels(plot_df['Office'], fontsize=10)
                        ax2.legend()
                        ax2.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig2)

                with tab3:
                    st.subheader("🏘️ Palika-Level Beneficiary Details")
                    selected_office = st.selectbox("Filter by Field Office:", ["All Offices"] + list(plot_df['Office'].unique()))
                    if selected_office == "All Offices":
                        filtered_palika_df = palika_df
                    else:
                        filtered_palika_df = palika_df[palika_df['Office'] == selected_office]

                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Palikas", len(filtered_palika_df))
                    with c2: st.metric("Total Beneficiaries", f"{filtered_palika_df['Beneficiaries'].sum():,}")
                    with c3:
                        avg_ben = int(filtered_palika_df['Beneficiaries'].mean()) if len(filtered_palika_df) > 0 else 0
                        st.metric("Avg per Palika", f"{avg_ben:,}")

                    st.markdown("---")
                    st.markdown("**Top 10 Palikas by Beneficiaries**")
                    top_10 = filtered_palika_df.sort_values('Beneficiaries', ascending=False).head(10).copy()
                    if len(top_10) > 0:
                        top_10['Color'] = top_10['Office'].apply(lambda x: OFFICE_COORDINATES.get(x, {}).get('color', 'gray'))
                        fig3, ax3 = plt.subplots(figsize=(12, 6))
                        bars = ax3.barh(top_10['Palika'], top_10['Beneficiaries'], color=top_10['Color'], edgecolor='black')
                        ax3.set_xlabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax3.invert_yaxis()
                        ax3.grid(axis='x', alpha=0.3)
                        palika_labels = [f"{r['Palika']} ({r['Office']})" for _, r in top_10.iterrows()]
                        ax3.set_yticks(list(range(len(palika_labels))))
                        ax3.set_yticklabels(palika_labels)
                        for b in bars:
                            w = b.get_width()
                            ax3.text(w, b.get_y() + b.get_height()/2., f'{int(w):,}', ha='left', va='center', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig3)
                    else:
                        st.info("선택된 조건에 해당하는 Palika 데이터가 없습니다.")

                    st.markdown("---")
                    st.markdown("**Complete Palika List**")
                    st.dataframe(filtered_palika_df, use_container_width=True, hide_index=True)
                    csv = filtered_palika_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Palika Data as CSV",
                        data=csv,
                        file_name=f"palika_beneficiaries_{selected_office.replace(' ', '_') if selected_office!='All Offices' else 'all'}.csv",
                        mime="text/csv"
                    )

        # -------------------- 3.1.2 --------------------
        elif page == "3.1.2 Water-safe communities 🏘️":
            df_raw = load_data(file_path)
            if show_columns:
                st.sidebar.write("📄 CSV Columns (현재 표준명 적용 후):")
                st.sidebar.write(list(df_raw.columns))
            plot_df = process_office_data_312(df_raw)
            palika_df = process_palika_data_312(df_raw)

            if plot_df.empty:
                st.warning("⚠️ 'Water-safe Communities (Yes/Y)' 및 'WSC Year 2025' 조건을 만족하는 데이터가 없습니다.")

            view_mode = st.radio("Select View:", ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"], horizontal=True)
            st.markdown("---")

            total_ben = plot_df['Beneficiaries'].sum()
            total_target = plot_df['Target'].sum()
            total_ach = (total_ben / total_target * 100) if total_target > 0 else 0.0
            total_palikas = len(palika_df['Palika'].unique())

            if view_mode == "📊 Office Summary Dashboard":
                st.title("💧 WASH Program Dashboard - Water-safe Communities")
                st.markdown("### Total Beneficiaries by Field Office (2025)")
                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Beneficiaries", f"{total_ben:,}")
                with c2: st.metric("Total Target", f"{total_target:,}")
                with c3: st.metric("Overall Achievement", f"{total_ach:.1f}%")
                with c4: st.metric("Field Offices", f"{len(plot_df)}")

                st.markdown("---")

                plt.style.use('default')
                office_colors = [OFFICE_COORDINATES.get(o, {}).get('color', '#888888') for o in plot_df['Office']]

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
                    for b in bars:
                        h = b.get_height()
                        ax1.text(b.get_x() + b.get_width()/2., h, f'{int(h):,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig1)
                with col2:
                    st.subheader("🥧 Distribution")
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    ax2.pie(
                        plot_df['Beneficiaries'],
                        labels=plot_df['Office'],
                        colors=office_colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        textprops={'fontsize': 10, 'fontweight': 'bold'}
                    )
                    ax2.set_title('Beneficiaries Distribution', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig2)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🎯 Target vs Achievement")
                    fig3, ax3 = plt.subplots(figsize=(8, 6))
                    x = range(len(plot_df))
                    width = 0.35
                    bars1 = ax3.bar([i - width/2 for i in x], plot_df['Target'], width, label='Target', color='lightcoral', edgecolor='black', linewidth=1)
                    bars2 = ax3.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width, label='Achieved', color='lightgreen', edgecolor='black', linewidth=1)
                    ax3.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                    ax3.set_title('Target vs Achievement', fontsize=14, fontweight='bold')
                    ax3.set_xticks(list(x))
                    ax3.set_xticklabels(plot_df['Office'], fontsize=10)
                    ax3.legend(fontsize=10)
                    ax3.grid(axis='y', alpha=0.3)
                    for bars in [bars1, bars2]:
                        for b in bars:
                            h = b.get_height()
                            ax3.text(b.get_x() + b.get_width()/2., h, f'{int(h):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig3)
                with col2:
                    st.subheader("📋 Summary Table")
                    summary_df = plot_df.copy()
                    summary_df['Beneficiaries'] = summary_df['Beneficiaries'].apply(lambda x: f"{x:,}")
                    summary_df['Target']        = summary_df['Target'].apply(lambda x: f"{x:,}")
                    summary_df['Achievement']   = summary_df['Achievement'].apply(lambda x: f"{x:.1f}%")

                    total_row = pd.DataFrame([{
                        'Office': 'TOTAL',
                        'Beneficiaries': f"{total_ben:,}",
                        'Target': f"{total_target:,}",
                        'Achievement': f"{total_ach:.1f}%"
                    }])
                    summary_df = pd.concat([summary_df, total_row], ignore_index=True)

                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

                    st.markdown("**Achievement Status:**")
                    st.markdown("🟢 ≥100%  \n🟡 75-99%  \n🔴 <75%")

                    st.markdown("---")
                    st.subheader("📊 Detailed Data Table (Office Level)")
                    st.dataframe(plot_df, use_container_width=True, hide_index=True)

                    csv = plot_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Office Data as CSV",
                        data=csv,
                        file_name="wash_water_safe_communities_office_2025.csv",
                        mime="text/csv"
                    )

            elif view_mode == "🗺️ Nepal Map & Palika Analysis":
                st.title("💧 WASH Program Dashboard - Water-safe Communities")
                st.markdown("### Field Offices Map and Palika-Level Analysis (2025)")
                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Beneficiaries", f"{total_ben:,}")
                with c2: st.metric("Total Target", f"{total_target:,}")
                with c3: st.metric("Overall Achievement", f"{total_ach:.1f}%")
                with c4: st.metric("Total Palikas", f"{total_palikas:,}")

                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["🗺️ Nepal Map (Office Level)", "📊 Office Summary Charts", "🏘️ Palika Details"])

                with tab1:
                    st.subheader("🗺️ Field Offices Distribution in Nepal")
                    st.markdown("**마커를 클릭하면 상세 정보를 볼 수 있습니다.** 마커 크기는 수혜자 수를 반영합니다.")
                    nepal_map = create_nepal_map(plot_df, palika_df)
                    st_folium(nepal_map, width=1200, height=600)

                    st.markdown("---")
                    st.subheader("Field Office Summary Quick View")
                    cols = st.columns(len(plot_df) if len(plot_df) > 0 else 1)
                    for idx, row in plot_df.iterrows():
                        if idx < len(cols):
                            with cols[idx]:
                                office_name = row['Office']
                                color = OFFICE_COORDINATES.get(office_name, {}).get('color', '#888888')
                                palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique())
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                                    <h3 style="color: {color}; margin: 0;">{office_name}</h3>
                                    <p style="margin: 5px 0;"><b>Beneficiaries:</b> {row['Beneficiaries']:,}</p>
                                    <p style="margin: 5px 0;"><b>Target:</b> {row['Target']:,}</p>
                                    <p style="margin: 5px 0;"><b>Achievement:</b> <b>{row['Achievement']:.1f}%</b></p>
                                    <p style="margin: 5px 0;"><b>Palikas:</b> {palikas_count}</p>
                                </div>
                                """, unsafe_allow_html=True)

                with tab2:
                    st.subheader("📊 Office-Level Analysis Charts")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Beneficiaries by Office**")
                        fig1, ax1 = plt.subplots(figsize=(8, 6))
                        colors = [OFFICE_COORDINATES.get(o, {}).get('color', '#888888') for o in plot_df['Office']]
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
                        ax2.set_xticks(list(x))
                        ax2.set_xticklabels(plot_df['Office'], fontsize=10)
                        ax2.legend()
                        ax2.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig2)

                with tab3:
                    st.subheader("🏘️ Palika-Level Beneficiary Details")
                    selected_office = st.selectbox("Filter by Field Office:", ["All Offices"] + list(plot_df['Office'].unique()))
                    if selected_office == "All Offices":
                        filtered_palika_df = palika_df
                    else:
                        filtered_palika_df = palika_df[palika_df['Office'] == selected_office]

                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Palikas", len(filtered_palika_df))
                    with c2: st.metric("Total Beneficiaries", f"{filtered_palika_df['Beneficiaries'].sum():,}")
                    with c3:
                        avg_ben = int(filtered_palika_df['Beneficiaries'].mean()) if len(filtered_palika_df) > 0 else 0
                        st.metric("Avg per Palika", f"{avg_ben:,}")

                    st.markdown("---")
                    st.markdown("**Top 10 Palikas by Beneficiaries**")
                    top_10 = filtered_palika_df.sort_values('Beneficiaries', ascending=False).head(10).copy()
                    if len(top_10) > 0:
                        top_10['Color'] = top_10['Office'].apply(lambda x: OFFICE_COORDINATES.get(x, {}).get('color', 'gray'))
                        fig3, ax3 = plt.subplots(figsize=(12, 6))
                        bars = ax3.barh(top_10['Palika'], top_10['Beneficiaries'], color=top_10['Color'], edgecolor='black')
                        ax3.set_xlabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax3.invert_yaxis()
                        ax3.grid(axis='x', alpha=0.3)
                        palika_labels = [f"{r['Palika']} ({r['Office']})" for _, r in top_10.iterrows()]
                        ax3.set_yticks(list(range(len(palika_labels))))
                        ax3.set_yticklabels(palika_labels)
                        for b in bars:
                            w = b.get_width()
                            ax3.text(w, b.get_y() + b.get_height()/2., f'{int(w):,}', ha='left', va='center', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig3)
                    else:
                        st.info("선택된 조건에 해당하는 Palika 데이터가 없습니다.")

                    st.markdown("---")
                    st.markdown("**Complete Palika List**")
                    st.dataframe(filtered_palika_df, use_container_width=True, hide_index=True)
                    csv = filtered_palika_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Palika Data as CSV",
                        data=csv,
                        file_name=f"palika_water_safe_communities_{selected_office.replace(' ', '_') if selected_office!='All Offices' else 'all'}.csv",
                        mime="text/csv"
                    )

        # -------------------- 3.1.3 (NEW) --------------------
        elif page == "3.1.3 Basic sanitation gained ":
            df_raw = load_data(file_path)
            if show_columns:
                st.sidebar.write("📄 CSV Columns (현재 표준명 적용 후):")
                st.sidebar.write(list(df_raw.columns))

            plot_df = process_office_data_313(df_raw)
            palika_df = process_palika_data_313(df_raw)

            if plot_df.empty:
                st.warning("⚠️ 'Completed Projects' 및 'Sanitation Year 2025' 조건을 만족하는 데이터가 없습니다. (3.1.3)")

            view_mode = st.radio("Select View:", ["📊 Office Summary Dashboard", "🗺️ Nepal Map & Palika Analysis"], horizontal=True)
            st.markdown("---")

            total_ben = plot_df['Beneficiaries'].sum()
            total_target = plot_df['Target'].sum()
            total_ach = (total_ben / total_target * 100) if total_target > 0 else 0.0
            total_palikas = len(palika_df['Palika'].unique())

            if view_mode == "📊 Office Summary Dashboard":
                st.title("💧 WASH Program Dashboard - Basic Sanitation Gained")
                st.markdown("### Total Beneficiaries by Field Office (2025)")
                st.caption(f"Assumption: Beneficiaries = Additional toilets built × {SAN_BENEFICIARY_PER_TOILET}")
                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Beneficiaries", f"{total_ben:,}")
                with c2: st.metric("Total Target", f"{total_target:,}")
                with c3: st.metric("Overall Achievement", f"{total_ach:.1f}%")
                with c4: st.metric("Field Offices", f"{len(plot_df)}")

                st.markdown("---")

                plt.style.use('default')
                office_colors = [OFFICE_COORDINATES.get(o, {}).get('color', '#888888') for o in plot_df['Office']]

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
                    for b in bars:
                        h = b.get_height()
                        ax1.text(b.get_x() + b.get_width()/2., h, f'{int(h):,}', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig1)
                with col2:
                    st.subheader("🥧 Distribution")
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    ax2.pie(
                        plot_df['Beneficiaries'],
                        labels=plot_df['Office'],
                        colors=office_colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        textprops={'fontsize': 10, 'fontweight': 'bold'}
                    )
                    ax2.set_title('Beneficiaries Distribution', fontsize=14, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig2)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🎯 Target vs Achievement")
                    fig3, ax3 = plt.subplots(figsize=(8, 6))
                    x = range(len(plot_df))
                    width = 0.35
                    bars1 = ax3.bar([i - width/2 for i in x], plot_df['Target'], width, label='Target', color='lightcoral', edgecolor='black', linewidth=1)
                    bars2 = ax3.bar([i + width/2 for i in x], plot_df['Beneficiaries'], width, label='Achieved', color='lightgreen', edgecolor='black', linewidth=1)
                    ax3.set_xlabel('Field Office', fontsize=12, fontweight='bold')
                    ax3.set_ylabel('Number of Beneficiaries', fontsize=12, fontweight='bold')
                    ax3.set_title('Target vs Achievement', fontsize=14, fontweight='bold')
                    ax3.set_xticks(list(x))
                    ax3.set_xticklabels(plot_df['Office'], fontsize=10)
                    ax3.legend(fontsize=10)
                    ax3.grid(axis='y', alpha=0.3)
                    for bars in [bars1, bars2]:
                        for b in bars:
                            h = b.get_height()
                            ax3.text(b.get_x() + b.get_width()/2., h, f'{int(h):,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                    plt.tight_layout()
                    st.pyplot(fig3)
                with col2:
                    st.subheader("📋 Summary Table")
                    summary_df = plot_df.copy()
                    summary_df['Beneficiaries'] = summary_df['Beneficiaries'].apply(lambda x: f"{x:,}")
                    summary_df['Target']        = summary_df['Target'].apply(lambda x: f"{x:,}")
                    summary_df['Achievement']   = summary_df['Achievement'].apply(lambda x: f"{x:.1f}%")

                    total_row = pd.DataFrame([{
                        'Office': 'TOTAL',
                        'Beneficiaries': f"{total_ben:,}",
                        'Target': f"{total_target:,}",
                        'Achievement': f"{total_ach:.1f}%"
                    }])
                    summary_df = pd.concat([summary_df, total_row], ignore_index=True)

                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

                    st.markdown("**Achievement Status:**")
                    st.markdown("🟢 ≥100%  \n🟡 75-99%  \n🔴 <75%")

                    st.markdown("---")
                    st.subheader("📊 Detailed Data Table (Office Level)")
                    st.dataframe(plot_df, use_container_width=True, hide_index=True)

                    csv = plot_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Office Data as CSV",
                        data=csv,
                        file_name="wash_basic_sanitation_gained_office_2025.csv",
                        mime="text/csv"
                    )

            elif view_mode == "🗺️ Nepal Map & Palika Analysis":
                st.title("💧 WASH Program Dashboard - Basic Sanitation Gained")
                st.markdown("### Field Offices Map and Palika-Level Analysis (2025)")
                st.caption(f"Assumption: Beneficiaries = Additional toilets built × {SAN_BENEFICIARY_PER_TOILET}")
                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Total Beneficiaries", f"{total_ben:,}")
                with c2: st.metric("Total Target", f"{total_target:,}")
                with c3: st.metric("Overall Achievement", f"{total_ach:.1f}%")
                with c4: st.metric("Total Palikas", f"{total_palikas:,}")

                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["🗺️ Nepal Map (Office Level)", "📊 Office Summary Charts", "🏘️ Palika Details"])

                with tab1:
                    st.subheader("🗺️ Field Offices Distribution in Nepal")
                    st.markdown("**마커를 클릭하면 상세 정보를 볼 수 있습니다.** 마커 크기는 수혜자 수를 반영합니다.")
                    nepal_map = create_nepal_map(plot_df, palika_df)
                    st_folium(nepal_map, width=1200, height=600)

                    st.markdown("---")
                    st.subheader("Field Office Summary Quick View")
                    cols = st.columns(len(plot_df) if len(plot_df) > 0 else 1)
                    for idx, row in plot_df.iterrows():
                        if idx < len(cols):
                            with cols[idx]:
                                office_name = row['Office']
                                color = OFFICE_COORDINATES.get(office_name, {}).get('color', '#888888')
                                palikas_count = len(palika_df[palika_df['Office'] == office_name]['Palika'].unique())
                                st.markdown(f"""
                                <div style="border-left: 4px solid {color}; padding: 10px; background-color: #f0f2f6; border-radius: 5px;">
                                    <h3 style="color: {color}; margin: 0;">{office_name}</h3>
                                    <p style="margin: 5px 0;"><b>Beneficiaries:</b> {row['Beneficiaries']:,}</p>
                                    <p style="margin: 5px 0;"><b>Target:</b> {row['Target']:,}</p>
                                    <p style="margin: 5px 0;"><b>Achievement:</b> <b>{row['Achievement']:.1f}%</b></p>
                                    <p style="margin: 5px 0;"><b>Palikas:</b> {palikas_count}</p>
                                </div>
                                """, unsafe_allow_html=True)

                with tab2:
                    st.subheader("📊 Office-Level Analysis Charts")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Beneficiaries by Office**")
                        fig1, ax1 = plt.subplots(figsize=(8, 6))
                        colors = [OFFICE_COORDINATES.get(o, {}).get('color', '#888888') for o in plot_df['Office']]
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
                        ax2.set_xticks(list(x))
                        ax2.set_xticklabels(plot_df['Office'], fontsize=10)
                        ax2.legend()
                        ax2.grid(axis='y', alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig2)

                with tab3:
                    st.subheader("🏘️ Palika-Level Beneficiary Details")
                    selected_office = st.selectbox("Filter by Field Office:", ["All Offices"] + list(plot_df['Office'].unique()))
                    if selected_office == "All Offices":
                        filtered_palika_df = palika_df
                    else:
                        filtered_palika_df = palika_df[palika_df['Office'] == selected_office]

                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Palikas", len(filtered_palika_df))
                    with c2: st.metric("Total Beneficiaries", f"{filtered_palika_df['Beneficiaries'].sum():,}")
                    with c3:
                        avg_ben = int(filtered_palika_df['Beneficiaries'].mean()) if len(filtered_palika_df) > 0 else 0
                        st.metric("Avg per Palika", f"{avg_ben:,}")

                    st.markdown("---")
                    st.markdown("**Top 10 Palikas by Beneficiaries**")
                    top_10 = filtered_palika_df.sort_values('Beneficiaries', ascending=False).head(10).copy()
                    if len(top_10) > 0:
                        top_10['Color'] = top_10['Office'].apply(lambda x: OFFICE_COORDINATES.get(x, {}).get('color', 'gray'))
                        fig3, ax3 = plt.subplots(figsize=(12, 6))
                        bars = ax3.barh(top_10['Palika'], top_10['Beneficiaries'], color=top_10['Color'], edgecolor='black')
                        ax3.set_xlabel('Total Beneficiaries', fontsize=12, fontweight='bold')
                        ax3.invert_yaxis()
                        ax3.grid(axis='x', alpha=0.3)
                        palika_labels = [f"{r['Palika']} ({r['Office']})" for _, r in top_10.iterrows()]
                        ax3.set_yticks(list(range(len(palika_labels))))
                        ax3.set_yticklabels(palika_labels)
                        for b in bars:
                            w = b.get_width()
                            ax3.text(w, b.get_y() + b.get_height()/2., f'{int(w):,}', ha='left', va='center', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig3)
                    else:
                        st.info("선택된 조건에 해당하는 Palika 데이터가 없습니다.")

                    st.markdown("---")
                    st.markdown("**Complete Palika List**")
                    st.dataframe(filtered_palika_df, use_container_width=True, hide_index=True)
                    csv = filtered_palika_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Palika Data as CSV",
                        data=csv,
                        file_name=f"palika_basic_sanitation_gained_{selected_office.replace(' ', '_') if selected_office!='All Offices' else 'all'}.csv",
                        mime="text/csv"
                    )

        else:
            # Other indicators under Siddhi Shrestha - show "Ongoing"
            display_coming_soon(page)


elif main_menu == "3.2 Dandi Ram":
    # Select Indicator: LGPAS / Palikas
    page = st.sidebar.radio("Select Indicator:", ["LGPAS", "Palikas"])
    # 현재는 플레이스홀더로 안내만 표시합니다. 이후 실제 지표 로직 연결 가능합니다.
    display_coming_soon(f"3.2 Dandi Ram - {page}")

elif main_menu == "Janakpur":
    page = st.sidebar.radio("Select Indicator:", ["Flood Map 2024", "Cholera Outbreak 2025", "Groundwater Monitoring"])
    display_coming_soon(f"Janakpur - {page}")

elif main_menu == "Dhangadi":
    page = st.sidebar.radio("Select Indicator:", ["Flood Map 2024", "Cholera Outbreak 2025", "Groundwater Monitoring"])
    display_coming_soon(f"Dhangadi - {page}")

elif main_menu == "Bhairahawa":
    page = st.sidebar.radio("Select Indicator:", ["Flood Map 2024", "Cholera Outbreak 2025", "Groundwater Monitoring"])
    display_coming_soon(f"Bhairahawa - {page}")

elif main_menu == "Surkhet":
    page = st.sidebar.radio("Select Indicator:", ["Flood Map 2024", "Cholera Outbreak 2025", "Groundwater Monitoring"])
    display_coming_soon(f"Surkhet - {page}")

elif main_menu == "End Year Progress against Annual target":


    # Footer / Filters info
    if main_menu == "3.1 Siddhi Shrestha":
        if page == "3.1.1 Safe water access 🚰":
            st.markdown("**Filters Applied:** Completed Projects · Safe Water (Yes/Y) · Year 2025 (Based on WASH.csv)")
        elif page == "3.1.2 Water-safe communities 🏘️":
            st.markdown("**Filters Applied:** Community Declared Water Safe (Yes/Y) · WSC Year 2025 (Based on WASH.csv)")
        elif page == "3.1.3 Basic sanitation gained ":
            st.markdown("**Filters Applied:** Completed Projects · Sanitation Year 2025 (Based on WASH.csv)")
            st.caption(f"Assumption: Beneficiaries = Additional toilets built × {SAN_BENEFICIARY_PER_TOILET}")
        else:
            st.markdown(f"**Data Source:** {file_path}")
    else:
        st.markdown(f"**Data Source:** {file_path}")
    st.caption(f"Data Source: {file_path}")

except FileNotFoundError:
    st.error(f"❌ Error: '{file_path}' 파일을 찾을 수 없습니다.")
    st.info("💡 **해결 방법:**")
    st.write("1. `WASH.csv` 파일이 올바른 위치에 있는지 확인하세요 (예: 현재 디렉토리 또는 data 폴더)")
    st.write("2. 왼쪽 사이드바에서 파일 위치를 변경해보세요")
    st.write("3. 파일 경로를 직접 입력해보세요")
except KeyError as ke:
    st.error(f"❌ Error: 필요한 컬럼을 찾을 수 없습니다.\n{str(ke)}")
    st.info("💡 **해결 방법:** CSV 헤더(컬럼명)를 확인하고, 데이터 컬럼명이 본 코드의 기대 표준명과 크게 다를 경우 상단의 'CSV 컬럼 확인(디버그)' 옵션을 켜서 실제 컬럼명을 확인한 뒤 매핑 사전에 변형명을 추가해 주세요.")
except Exception as e:
    st.error(f"❌ Error loading data or rendering dashboard: {str(e)}")
    # import traceback
    # st.code(traceback.format_exc())
