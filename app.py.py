import streamlit as st
import gspread
import pandas as pd
import random
import string
import plotly.graph_objects as go
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

st.set_page_config(page_title="Ванина игра", layout="wide")

# -----------------------
# CSS - СУПЕР ДЕТАЛИЗИРОВАННЫЙ ДИЗАЙН
# -----------------------
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    .stApp { 
        background: linear-gradient(135deg, #0a0d10 0%, #0b0e11 50%, #0d1015 100%);
        color: #FFFFFF; 
    }

    /* Анимированный фон для заголовка */
    @keyframes borderGlow {
        0%, 100% { 
            box-shadow: 
                0 0 20px rgba(240,185,11,0.3),
                0 0 40px rgba(14,203,129,0.2),
                inset 0 0 30px rgba(240,185,11,0.1);
        }
        50% { 
            box-shadow: 
                0 0 40px rgba(240,185,11,0.5),
                0 0 60px rgba(14,203,129,0.3),
                inset 0 0 40px rgba(240,185,11,0.2);
        }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .header-container {
        position: relative;
        padding: 30px;
        margin: -20px -20px 30px -20px;
        background: linear-gradient(135deg, 
            rgba(240,185,11,0.1) 0%, 
            rgba(14,203,129,0.1) 25%,
            rgba(240,185,11,0.1) 50%,
            rgba(14,203,129,0.1) 75%,
            rgba(240,185,11,0.1) 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, #f0b90b, #0ecb81, #f0b90b) 1;
        box-shadow: 
            0 4px 20px rgba(240,185,11,0.3),
            inset 0 -2px 10px rgba(240,185,11,0.1);
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            #f0b90b 20%, 
            #0ecb81 50%, 
            #f0b90b 80%, 
            transparent 100%);
        animation: borderGlow 3s ease-in-out infinite;
    }
    
    .header-container::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            #0ecb81 20%, 
            #f0b90b 50%, 
            #0ecb81 80%, 
            transparent 100%);
        animation: borderGlow 3s ease-in-out infinite reverse;
    }

    .main-title {
        color: #f0b90b;
        margin: 0;
        text-shadow: 
            0 0 10px rgba(240,185,11,0.5),
            0 0 20px rgba(240,185,11,0.3),
            0 0 30px rgba(240,185,11,0.2),
            2px 2px 4px rgba(0,0,0,0.5);
        font-size: 48px;
        font-weight: 900;
        letter-spacing: 2px;
        text-align: center;
        position: relative;
        z-index: 1;
    }

    /* Кнопки */
    div.stButton > button {
        background: linear-gradient(135deg, #1a1d20 0%, #000000 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 2px solid #2b2b2b !important;
        padding: 12px 20px !important;
        font-weight: 700 !important;
        transition: all 0.4s ease !important;
        position: relative !important;
        overflow: hidden !important;
        font-size: 14px !important;
        letter-spacing: 0.5px !important;
    }
    
    div.stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(240,185,11,0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    div.stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    div.stButton > button:hover {
        border-color: #f0b90b !important;
        box-shadow: 
            0 0 20px rgba(240,185,11,0.4),
            0 0 40px rgba(240,185,11,0.2),
            inset 0 0 20px rgba(240,185,11,0.1) !important;
        transform: translateY(-3px) scale(1.02) !important;
        background: linear-gradient(135deg, #2a2d30 0%, #1a1d20 100%) !important;
    }
    
    div.stButton > button:active {
        transform: translateY(-1px) scale(0.98) !important;
    }

    /* Карточки акций */
    .stock-card { 
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
        border-radius: 16px; 
        padding: 24px; 
        border: 2px solid #2b2f33; 
        margin-bottom: 16px; 
        min-height: 220px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .stock-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, #f0b90b, transparent);
        transition: left 0.5s;
    }
    
    .stock-card:hover::before {
        left: 100%;
    }
    
    .stock-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 50% 0%, rgba(240,185,11,0.05), transparent 70%);
        opacity: 0;
        transition: opacity 0.4s;
    }
    
    .stock-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 
            0 12px 28px rgba(0,0,0,0.5),
            0 0 30px rgba(240,185,11,0.2),
            inset 0 0 20px rgba(240,185,11,0.05);
        border-color: #f0b90b;
    }
    
    .stock-card:hover::after {
        opacity: 1;
    }
    
    .stock-name { 
        color: #FFFFFF; 
        font-size: 24px; 
        font-weight: 800; 
        margin-bottom: 6px; 
        line-height: 1.2;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .stock-type { 
        color: #9aa0a6; 
        font-size: 12px; 
        text-transform: uppercase; 
        letter-spacing: 1.5px;
        background: rgba(154,160,166,0.15);
        padding: 6px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 6px;
        font-weight: 600;
        border: 1px solid rgba(154,160,166,0.2);
    }
    
    .old-price { 
        color: #666; 
        font-size: 15px; 
        text-decoration: line-through;
        margin-bottom: 4px;
    }
    
    .current-price { 
        color: #f0b90b; 
        font-size: 36px; 
        font-weight: 900; 
        line-height: 1; 
        text-shadow: 
            0 0 10px rgba(240,185,11,0.4),
            0 2px 4px rgba(0,0,0,0.3);
        letter-spacing: -1px;
    }
    
    .change-pct { 
        font-size: 26px; 
        font-weight: 900;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .pos { 
        color: #0ecb81;
        text-shadow: 0 0 10px rgba(14,203,129,0.4);
    } 
    
    .neg { 
        color: #f6465d;
        text-shadow: 0 0 10px rgba(246,70,93,0.4);
    }
    
    .highlight-100 { 
        box-shadow: 
            0 0 30px rgba(240,185,11,0.4),
            0 12px 28px rgba(0,0,0,0.5),
            inset 0 0 30px rgba(240,185,11,0.1); 
        border: 2px solid #f0b90b;
        animation: megaPulse 2s ease-in-out infinite;
    }
    
    @keyframes megaPulse {
        0%, 100% { 
            box-shadow: 
                0 0 30px rgba(240,185,11,0.4),
                0 12px 28px rgba(0,0,0,0.5),
                inset 0 0 30px rgba(240,185,11,0.1);
            transform: scale(1);
        }
        50% { 
            box-shadow: 
                0 0 50px rgba(240,185,11,0.6),
                0 16px 32px rgba(0,0,0,0.6),
                inset 0 0 40px rgba(240,185,11,0.2);
            transform: scale(1.02);
        }
    }

    /* Портфель */
    .portfolio-header { 
        background: linear-gradient(135deg, 
            rgba(240,185,11,0.15) 0%, 
            rgba(26,29,32,0.8) 50%,
            rgba(14,203,129,0.15) 100%); 
        border-radius: 16px; 
        padding: 32px; 
        margin-bottom: 24px; 
        border: 2px solid #f0b90b;
        box-shadow: 
            0 8px 24px rgba(240,185,11,0.3),
            inset 0 0 40px rgba(240,185,11,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .portfolio-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(240,185,11,0.1), transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .portfolio-stat { 
        text-align: center; 
        padding: 20px;
        position: relative;
        z-index: 1;
    }
    
    .stat-label { 
        color: #9aa0a6; 
        font-size: 13px; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        margin-bottom: 10px;
        font-weight: 700;
    }
    
    .stat-value { 
        color: #FFFFFF; 
        font-size: 32px; 
        font-weight: 900;
        text-shadow: 
            0 2px 4px rgba(0,0,0,0.4),
            0 0 10px rgba(255,255,255,0.2);
    }
    
    .position-item { 
        background: linear-gradient(135deg, #1a1d20 0%, #161719 100%); 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 16px; 
        border: 2px solid #2b2f33;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .position-item::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, #f0b90b, #0ecb81);
        transform: scaleY(0);
        transition: transform 0.3s ease;
    }
    
    .position-item:hover {
        border-color: #f0b90b;
        transform: translateX(8px);
        box-shadow: 0 4px 16px rgba(240,185,11,0.2);
    }
    
    .position-item:hover::before {
        transform: scaleY(1);
    }
    
    .position-title { 
        color: #f0b90b; 
        font-size: 22px; 
        font-weight: 800;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .small-muted { 
        color: #888; 
        font-size: 13px;
        letter-spacing: 0.5px;
    }
    
    /* Диалог покупки */
    .purchase-dialog { 
        background: linear-gradient(180deg, #1a1d20, #0e1113); 
        border: 3px solid #f0b90b; 
        border-radius: 16px; 
        padding: 28px; 
        margin: 16px 0;
        box-shadow: 
            0 12px 40px rgba(240,185,11,0.4),
            inset 0 0 30px rgba(240,185,11,0.1);
        animation: dialogSlideIn 0.4s ease;
    }
    
    @keyframes dialogSlideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .total-price { 
        color: #0ecb81; 
        font-size: 28px; 
        font-weight: 900; 
        text-align: center; 
        padding: 20px; 
        background: linear-gradient(135deg, rgba(14,203,129,0.15), rgba(14,203,129,0.05)); 
        border-radius: 12px; 
        margin: 16px 0;
        border: 2px solid rgba(14,203,129,0.4);
        box-shadow: 
            0 4px 16px rgba(14,203,129,0.2),
            inset 0 0 20px rgba(14,203,129,0.1);
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Новостная лента */
    .news-banner {
        background: linear-gradient(135deg, 
            rgba(240,185,11,0.08) 0%, 
            rgba(26,29,32,0.6) 50%,
            rgba(14,203,129,0.08) 100%);
        border-left: 4px solid #f0b90b;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        animation: slideIn 0.6s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border-right: 4px solid #0ecb81;
    }
    
    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateX(-30px); 
        }
        to { 
            opacity: 1; 
            transform: translateX(0); 
        }
    }
    
    /* Виджет золота */
    .gold-widget {
        background: linear-gradient(135deg, 
            rgba(240,185,11,0.15) 0%, 
            rgba(26,29,32,0.8) 100%);
        border: 2px solid #f0b90b;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 
            0 6px 20px rgba(240,185,11,0.25),
            inset 0 0 30px rgba(240,185,11,0.08);
        position: relative;
        overflow: hidden;
    }
    
    .gold-widget::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at center, rgba(240,185,11,0.1), transparent 60%);
        animation: rotate 15s linear infinite reverse;
    }
    
    /* Навигационные кнопки */
    .nav-button-container {
        display: grid;
        gap: 12px;
        margin-bottom: 20px;
    }
    
    /* Значки и иконки */
    .icon-badge {
        display: inline-block;
        background: rgba(240,185,11,0.2);
        padding: 8px 16px;
        border-radius: 20px;
        color: #f0b90b;
        font-weight: 700;
        font-size: 14px;
        border: 1px solid rgba(240,185,11,0.3);
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Стили для слайдера */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #f0b90b, #0ecb81) !important;
    }
    
    /* Улучшение sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1113 0%, #0b0e11 100%);
        border-right: 2px solid rgba(240,185,11,0.2);
    }
    
    /* Разделители */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #f0b90b, transparent);
        margin: 24px 0;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# Helpers (без изменений)
# -----------------------
def safe_float(value):
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace('%', '').replace(',', '.').strip()
        return float(value)
    except Exception:
        return 0.0

def split_modifiers(raw_text):
    if raw_text is None:
        return []
    txt = str(raw_text).strip()
    if txt == "":
        return []
    txt = re.sub(r'[\[\]\(\)"]', ' ', txt)
    tokens = re.split(r'[,\;/\|\n]+', txt)
    tokens = [t.strip() for t in tokens if t.strip() != ""]
    expanded = []
    for t in tokens:
        expanded.append(t)
        m = re.search(r'\b(\d{1,3})\b', t)
        if m:
            expanded.append(m.group(1))
    seen = set()
    ordered = []
    for x in expanded:
        lx = x.lower()
        if lx not in seen:
            ordered.append(x)
            seen.add(lx)
    return ordered

def find_col_in_df(df, keywords, default=None):
    if df is None or df.empty:
        return default
    for col in df.columns:
        if col is None:
            continue
        lc = str(col).lower()
        for kw in keywords:
            if kw in lc:
                return col
    return default

def safe_row_get(row, candidates, default=""):
    if row is None:
        return default
    for c in candidates:
        if not c:
            continue
        if c in row.index:
            return row.get(c, default)
    for col in row.index:
        try:
            lc = str(col).lower()
        except Exception:
            lc = ""
        for c in candidates:
            if not c:
                continue
            if c in lc:
                return row.get(col, default)
    return default

# -----------------------
# Google Sheets helpers
# -----------------------
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )
    return gspread.authorize(creds)

@st.cache_data(ttl=5)
def load_stocks_table():
    client = get_gspread_client()
    try:
        return pd.DataFrame(
            client.open("«Акции»").worksheet("Лист1").get_all_records()
        )
    except Exception as e:
        st.error(f"❌ Ошибка загрузки акций: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_reference_tables():
    client = get_gspread_client()
    
    try:
        df_zavod = pd.DataFrame(
            client.open("«Таблица дификаторы_заводские_проценты»")
            .sheet1.get_all_records()
        )
    except Exception:
        df_zavod = pd.DataFrame(columns=["Значение", "%"])

    try:
        df_region = pd.DataFrame(
            client.open("Таблица «Модификаторы_региональные_проценты»")
            .sheet1.get_all_records()
        )
    except Exception:
        df_region = pd.DataFrame(columns=["Значение", "%"])

    return df_zavod, df_region

@st.cache_resource
def get_buy_worksheet():
    client = get_gspread_client()
    try:
        return client.open("Таблица «Покупки»").worksheet("Лист6")
    except Exception:
        return None

@st.cache_data(ttl=10)
def load_purchases():
    client = get_gspread_client()
    try:
        ws = client.open("Таблица «Покупки»").worksheet("Лист6")
        return pd.DataFrame(ws.get_all_records())
    except Exception:
        return pd.DataFrame(columns=["time", "who", "name", "price", "tx_id"])

def remove_stock_from_purchases_sheet(stock_name):
    try:
        ws = get_buy_worksheet()
        if ws is None:
            return False
        all_values = ws.get_all_values()
        if not all_values or len(all_values) < 2:
            return False

        header = all_values[0]
        name_col_idx = next((idx for idx, h in enumerate(header)
                             if h and any(k in h.lower() for k in ["name", "назв", "акция"])),
                            2 if len(header) > 2 else None)

        if name_col_idx is not None:
            to_delete = [i for i, row in enumerate(all_values[1:], start=2)
                         if len(row) > name_col_idx and str(row[name_col_idx]).strip() == str(stock_name).strip()]

            for r in sorted(to_delete, reverse=True):
                try:
                    ws.delete_row(r)
                except Exception:
                    pass
            try:
                load_purchases.clear()
            except Exception:
                pass
            return bool(to_delete)
    except Exception:
        return False
    return False

def sum_modifiers_and_list(raw_text, ref_df):
    if ref_df is None or ref_df.empty:
        return 0.0, [], []

    def normalize(s):
        return re.sub(r'\W+', '', str(s).lower())

    ref_map = {}

    for _, r in ref_df.iterrows():
        typ = None
        val = None
        pct = 0.0
        for col in r.index:
            if col is None:
                continue
            lc = str(col).lower()
            if "тип" in lc or lc == "type":
                typ = r.get(col)
            if "знач" in lc or "value" in lc:
                val = r.get(col)
            if "%" in str(col).lower() or "percent" in lc or "pct" in lc:
                pct = safe_float(r.get(col, 0))

        typ_str = str(typ).strip() if typ is not None else ""
        val_str = str(val).strip() if val is not None else ""

        if typ_str and val_str:
            display = f"{typ_str} {val_str}"
        elif val_str:
            display = val_str
        else:
            display = typ_str

        keys = set()
        if val_str != "":
            keys.add(normalize(val_str))
        if typ_str != "":
            keys.add(normalize(typ_str))
        if typ_str != "" and val_str != "":
            keys.add(normalize(f"{typ_str} {val_str}"))
        if re.fullmatch(r'-?\d+(\.\d+)?', val_str):
            keys.add(re.sub(r'\W+', '', val_str))

        for k in keys:
            if k not in ref_map:
                ref_map[k] = (display, safe_float(pct))

    tokens = split_modifiers(raw_text)
    matched_keys = set()
    matched_displays = set()
    found = []

    for tok in tokens:
        if not tok:
            continue
        tok_norm = normalize(tok)

        if tok_norm in ref_map and tok_norm not in matched_keys:
            disp, p = ref_map[tok_norm]
            disp_norm = normalize(disp)
            if disp_norm not in matched_displays:
                matched_keys.add(tok_norm)
                matched_displays.add(disp_norm)
                found.append((disp, p))
            else:
                matched_keys.add(tok_norm)
            continue

        if re.fullmatch(r'\d{1,6}', tok.strip()):
            num = re.sub(r'\W+', '', tok.strip())
            if num in ref_map and num not in matched_keys:
                disp, p = ref_map[num]
                disp_norm = normalize(disp)
                if disp_norm not in matched_displays:
                    matched_keys.add(num)
                    matched_displays.add(disp_norm)
                    found.append((disp, p))
                else:
                    matched_keys.add(num)
                continue
            for key, (disp, pct) in ref_map.items():
                if key in matched_keys:
                    continue
                if re.search(r'\b' + re.escape(num) + r'\b', disp):
                    disp_norm = normalize(disp)
                    if disp_norm not in matched_displays:
                        matched_keys.add(key)
                        matched_displays.add(disp_norm)
                        found.append((disp, pct))
                    else:
                        matched_keys.add(key)
                    break

    total_pct = sum([safe_float(p) for (_, p) in found])
    return total_pct, found, tokens

# -----------------------
# Initial state
# -----------------------
if 'gold_history' not in st.session_state:
    st.session_state.gold_history = []
    p = 1200.0
    for _ in range(20):
        o = p
        c = o + random.uniform(-10, 10)
        h = max(o, c) + random.uniform(0, 5)
        l = min(o, c) - random.uniform(0, 5)
        st.session_state.gold_history.append({'open': o, 'high': h, 'low': l, 'close': c})
        p = c

st.session_state.setdefault('user', None)
st.session_state.setdefault('view_mode', "all")
st.session_state.setdefault('last_found_map', {})
st.session_state.setdefault('last_tokens_map', {})
st.session_state.setdefault('last_raw_map', {})
st.session_state.setdefault('purchase_dialog', None)

# -----------------------
# Main fragment
# -----------------------
@st.fragment(run_every=30)
def market_display():
    # Красивый заголовок с декорациями
    st.markdown("""
        <div class='header-container'>
            <h1 class='main-title'>💎 ВАНИНА ИГРА 💎</h1>
        </div>
    """, unsafe_allow_html=True)

    # Новости
    news_list = [
        "Рынок золота демонстрирует стабильный рост - эксперты прогнозируют дальнейшее укрепление позиций",
        "Новый завод открыл двери - аналитики ожидают значительный прирост к заводским акциям",
        "Резкое падение акций технологических компаний вызвало волну беспокойства среди инвесторов",
        "Крупные инвесторы прогнозируют масштабный рост цен на ближайший квартал",
        "Экономика рынка стабилизируется после турбулентного периода - хорошие новости для инвесторов",
        "Новые законодательные инициативы могут кардинально изменить расклад сил на рынке",
        "Квартальные отчеты компаний превзошли ожидания - акционеры празднуют успех",
        "Региональные акции набирают популярность среди опытных трейдеров",
        "Инновационный проект привлек рекордные инвестиции в размере $500 млн",
        "Ведущие аналитики Wall Street повышают прогнозы по золоту на следующий год",
    ]
    random_news = random.choice(news_list)
    st.markdown(
        f"<div class='news-banner'><h3 style='color:#ccccff; margin:0; font-size:16px;'>📰 <strong>НОВОСТИ РЫНКА:</strong> {random_news}</h3></div>",
        unsafe_allow_html=True
    )

    # Кнопка обновить
    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("🔄 ОБНОВИТЬ ДАННЫЕ"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

    # Обновление свечи золота
    last_close = st.session_state.gold_history[-1]['close']
    o = last_close
    c = o + random.uniform(-15, 15)
    h = max(o, c) + random.uniform(0, 7)
    l = min(o, c) - random.uniform(0, 7)
    st.session_state.gold_history.append({'open': o, 'high': h, 'low': l, 'close': c})
    if len(st.session_state.gold_history) > 60:
        st.session_state.gold_history.pop(0)

    # Загрузка данных
    df_raw = load_stocks_table()
    df_ref_zavod, df_ref_region = load_reference_tables()

    if df_raw is None or df_raw.empty:
        st.info("⚠️ Нет данных таблицы «Акции».")
        return

    df_raw.columns = [str(col).strip() for col in df_raw.columns]

    status_col = find_col_in_df(df_raw, ['статус', 'status'])
    name_col = find_col_in_df(df_raw, ['назв', 'name'])
    type_col = find_col_in_df(df_raw, ['тип', 'type'])
    base_price_col = find_col_in_df(df_raw, ['баз', 'price', 'цена', 'cost'])
    mod_col = find_col_in_df(df_raw, ['модифик', 'modifier'])

    if status_col is None:
        st.error("❌ В таблице «Акции» не найдена колонка со статусом.")
        return

    # График золота и навигация
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        current_gold = st.session_state.gold_history[-1]['close']
        prev_gold = st.session_state.gold_history[-2]['close'] if len(st.session_state.gold_history) >= 2 else current_gold
        gold_change = current_gold - prev_gold
        gold_change_pct = (gold_change / prev_gold * 100) if prev_gold != 0 else 0
        
        gold_color = "#0ecb81" if gold_change >= 0 else "#f6465d"
        gold_sign = "+" if gold_change >= 0 else ""
        
        st.markdown(f"""
            <div class='gold-widget'>
                <h3 style='color:#f0b90b; margin:0 0 12px 0; font-size:20px; font-weight:800; position:relative; z-index:1;'>🪙 КУРС ЗОЛОТА</h3>
                <div style='display:flex; justify-content:space-between; align-items:center; position:relative; z-index:1;'>
                    <div style='font-size:40px; font-weight:900; color:#f0b90b; text-shadow: 0 0 15px rgba(240,185,11,0.5);'>{current_gold:.2f}$</div>
                    <div style='font-size:22px; font-weight:800; color:{gold_color}; text-shadow: 0 0 10px {gold_color};'>{gold_sign}{gold_change:.2f} ({gold_sign}{gold_change_pct:.2f}%)</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        hist_df = pd.DataFrame(st.session_state.gold_history)
        fig = go.Figure(data=[go.Candlestick(
            open=hist_df['open'], 
            high=hist_df['high'], 
            low=hist_df['low'], 
            close=hist_df['close'],
            increasing_line_color='#0ecb81', 
            decreasing_line_color='#f6465d',
            increasing_fillcolor='rgba(14,203,129,0.4)',
            decreasing_fillcolor='rgba(246,70,93,0.4)'
        )])
        fig.update_layout(
            height=320, 
            margin=dict(l=0, r=0, t=8, b=0), 
            xaxis_rangeslider_visible=False,
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(26,29,32,0.6)',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(240,185,11,0.15)', gridwidth=1)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_right:
        st.markdown("#### 🎯 НАВИГАЦИЯ")
        st.markdown("<div class='nav-button-container'>", unsafe_allow_html=True)
        
        if st.button("📊 ВСЕ АКЦИИ", use_container_width=True):
            st.session_state.view_mode = "all"
            st.rerun()
        if st.button("🔥 ТОП-5 РОСТА", use_container_width=True):
            st.session_state.view_mode = "top"
            st.rerun()
        if st.button("💼 ПОРТФЕЛЬ", use_container_width=True):
            st.session_state.view_mode = "portfolio"
            st.rerun()
        if st.button("📜 ИСТОРИЯ СДЕЛОК", use_container_width=True):
            st.session_state.view_mode = "history"
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='small-muted' style='margin-top:16px; text-align:center; font-size:12px;'>⏱️ Автообновление<br/>каждые 30 сек</div>", unsafe_allow_html=True)

    # Обработка акций
    try:
        status_series = df_raw[status_col].astype(str).str.upper()
        open_mask = status_series.str.contains('ОТКР', regex=False)
        open_stocks = df_raw[open_mask].copy()
    except Exception:
        st.error("❌ Не удалось отфильтровать открытые акции.")
        return

    gold_imp = (gold_change_pct if gold_change_pct else 0.0)

    processed = []
    removed_stock_names = set()
    st.session_state['last_found_map'] = {}
    st.session_state['last_tokens_map'] = {}
    st.session_state['last_raw_map'] = {}

    for i, row in open_stocks.iterrows():
        name = safe_row_get(row, [name_col] if name_col else [], default=f'#{i}')
        if not name:
            name = f'#{i}'
        typ = safe_row_get(row, [type_col] if type_col else [], default='')
        base_price = safe_float(safe_row_get(row, [base_price_col] if base_price_col else [], default=0))
        raw_mod = safe_row_get(row, [mod_col] if mod_col else [], default='')
        is_zavod = "завод" in str(typ).lower()

        parts = []
        if df_ref_region is not None and not df_ref_region.empty:
            parts.append(df_ref_region.copy())
        if df_ref_zavod is not None and not df_ref_zavod.empty:
            parts.append(df_ref_zavod.copy())

        if parts:
            ref_table = pd.concat(parts, ignore_index=True, sort=False)
            colmap = {c.lower(): c for c in ref_table.columns}
            typ_col = next((col for key, col in colmap.items() if 'тип' in key or 'type' in key), None)
            val_col = next((col for key, col in colmap.items() if 'знач' in key or 'value' in key), None)
            pct_col = next((col for key, col in colmap.items() if '%' in key or 'percent' in key or 'pct' in key), None)
            if typ_col and val_col:
                cols_keep = [typ_col, val_col] + ([pct_col] if pct_col else [])
                ref_table = ref_table[cols_keep].copy()
                ref_table.columns = ['Тип', 'Значение'] + (['%'] if pct_col else [])
                ref_table['Тип'] = ref_table['Тип'].astype(str).str.strip()
                ref_table['Значение'] = ref_table['Значение'].astype(str).str.strip()
                ref_table = ref_table.drop_duplicates(subset=['Тип', 'Значение'], keep='first').reset_index(drop=True)
        else:
            ref_table = pd.DataFrame(columns=["Значение", "%"])

        mod_sum, found_pairs, tokens = sum_modifiers_and_list(raw_mod, ref_table)

        st.session_state['last_found_map'][name] = found_pairs
        st.session_state['last_tokens_map'][name] = tokens
        st.session_state['last_raw_map'][name] = raw_mod

        total_pct = round(mod_sum + (0.0 if is_zavod else gold_imp), 2)
        final_price = max(0, int(round(base_price * (1.0 + total_pct / 100.0))))

        if final_price <= 0:
            removed_stock_names.add(name)
            try:
                remove_stock_from_purchases_sheet(name)
            except Exception:
                pass
            continue

        processed.append({
            "Название": name,
            "Тип": typ,
            "Базовая цена": base_price,
            "модификаторы": raw_mod,
            "pct": total_pct,
            "final_price": final_price
        })

    # История сделок
    if st.session_state.view_mode == "history":
        st.markdown("## 📜 История сделок")
        
        if not st.session_state.user:
            st.warning("⚠️ Войдите в профиль, чтобы просмотреть историю сделок.")
            return

        purchases = load_purchases()
        if purchases is None or purchases.empty:
            st.info("📭 История сделок пуста.")
            return

        header_cols = list(purchases.columns)
        col_time = next((c for c in header_cols if any(k in c.lower() for k in ["time", "время", "дата"])), header_cols[0] if len(header_cols) >= 1 else None)
        col_who = next((c for c in header_cols if any(k in c.lower() for k in ["who", "кто", "user"])), header_cols[1] if len(header_cols) >= 2 else None)
        col_name = next((c for c in header_cols if any(k in c.lower() for k in ["name", "назв", "акция"])), header_cols[2] if len(header_cols) >= 3 else None)
        col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), header_cols[3] if len(header_cols) >= 4 else None)
        col_tx = next((c for c in header_cols if any(k in c.lower() for k in ["tx", "id"])), header_cols[4] if len(header_cols) >= 5 else None)

        try:
            user_purchases = purchases[purchases[col_who] == st.session_state.user].copy()
        except:
            user_purchases = purchases.copy()

        if user_purchases.empty:
            st.info("У вас ещё нет сделок.")
            return

        user_purchases = user_purchases.sort_values(by=col_time, ascending=False)

        for idx, row in user_purchases.head(20).iterrows():
            st.markdown(f"""
                <div class='position-item'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <div style='font-size:18px; font-weight:700; color:#f0b90b;'>{row[col_name]}</div>
                            <div class='small-muted'>💰 ${safe_float(row[col_price]):,.0f} • 🕐 {row[col_time]}</div>
                        </div>
                        <div style='background:rgba(240,185,11,0.2); padding:6px 12px; border-radius:20px; color:#f0b90b; font-size:12px; font-weight:700;'>
                            {row[col_tx]}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        return

    # Portfolio view
    if st.session_state.view_mode == "portfolio":
        if not st.session_state.user:
            st.warning("⚠️ Войдите в профиль, чтобы просмотреть портфель.")
            return

        purchases = load_purchases()
        if purchases is None or purchases.empty:
            st.info("💼 Портфель пуст. Начните инвестировать!")
            return

        header_cols = list(purchases.columns)
        col_time = col_who = col_name = col_price = col_tx = None

        for c in header_cols:
            lc = c.lower()
            if not col_time and any(k in lc for k in ["time", "время", "дата", "timestamp"]):
                col_time = c
            if not col_who and any(k in lc for k in ["who", "кто", "user", "buyer"]):
                col_who = c
            if not col_name and any(k in lc for k in ["name", "назв", "акция"]):
                col_name = c
            if not col_price and any(k in lc for k in ["price", "цена", "cost"]):
                col_price = c
            if not col_tx and any(k in lc for k in ["tx", "id", "идентификатор"]):
                col_tx = c

        col_time = col_time or (header_cols[0] if len(header_cols) >= 1 else None)
        col_who = col_who or (header_cols[1] if len(header_cols) >= 2 else None)
        col_name = col_name or (header_cols[2] if len(header_cols) >= 3 else None)
        col_price = col_price or (header_cols[3] if len(header_cols) >= 4 else None)
        col_tx = col_tx or (header_cols[4] if len(header_cols) >= 5 else None)

        try:
            user_purchases = purchases[purchases[col_who] == st.session_state.user].copy()
        except Exception:
            user_purchases = purchases.copy()

        if user_purchases.empty:
            st.info("У вас ещё нет покупок. Начните инвестировать!")
            return

        user_purchases['_price_'] = user_purchases[col_price].apply(safe_float)
        grouped = user_purchases.groupby(col_name).agg(
            quantity=pd.NamedAgg(column=col_name, aggfunc='count'),
            avg_price=pd.NamedAgg(column='_price_', aggfunc='mean'),
            total_spent=pd.NamedAgg(column='_price_', aggfunc='sum')
        ).reset_index().rename(columns={col_name: 'name'})

        current_price_map = {p['Название']: p['final_price'] for p in processed}
        grouped['current_price'] = grouped['name'].map(current_price_map).fillna(grouped['avg_price'])
        grouped['current_value'] = grouped['quantity'] * grouped['current_price']
        grouped['pnl'] = grouped['current_value'] - grouped['total_spent']
        grouped['pnl_pct'] = (grouped['pnl'] / grouped['total_spent'] * 100).fillna(0)

        total_invested = grouped['total_spent'].sum()
        total_current = grouped['current_value'].sum()
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested != 0 else 0.0

        st.markdown(f"<div class='portfolio-header'><h2 style='color:#f0b90b; margin:0; position:relative; z-index:1;'>💼 ПОРТФЕЛЬ — {st.session_state.user.upper()}</h2></div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>💰 ИНВЕСТИРОВАНО</div><div class='stat-value'>${total_invested:,.0f}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>📈 ТЕКУЩАЯ СТОИМОСТЬ</div><div class='stat-value'>${total_current:,.0f}</div></div>", unsafe_allow_html=True)
        with c3:
            pnl_color = "#0ecb81" if total_pnl >= 0 else "#f6465d"
            pnl_sign = "+" if total_pnl >= 0 else ""
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>💎 ПРИБЫЛЬ/УБЫТОК</div><div class='stat-value' style='color:{pnl_color}'>{pnl_sign}${total_pnl:,.0f}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>📊 ПОЗИЦИЙ</div><div class='stat-value'>{len(grouped)}</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📊 ВАШИ АКЦИИ")

for _, pos in grouped_sorted.iterrows():
            pnl_sign = "+" if pos['pnl'] >= 0 else ""
            pnl_color = "#0ecb81" if pos['pnl'] >= 0 else "#f6465d"
            
            # HTML без внутренних отступов (прижат влево)
            st.markdown(f"""<div class='position-item'>
<div style='display:flex; justify-content:space-between; margin-bottom:16px;'>
<div class='position-title'>{pos['name']}</div>
<div class='icon-badge'>×{int(pos['quantity'])}</div>
</div>
<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:20px; margin-top:12px;'>
<div>
<div class='small-muted'>Цена покупки</div>
<div style='font-size:20px; font-weight:800; color:#fff; margin-top:4px;'>${pos['avg_price']:,.0f}</div>
</div>
<div>
<div class='small-muted'>Текущая цена</div>
<div style='font-size:20px; font-weight:800; color:#f0b90b; margin-top:4px;'>${pos['current_price']:,.0f}</div>
</div>
<div>
<div class='small-muted'>Общая стоимость</div>
<div style='font-size:20px; font-weight:800; color:#fff; margin-top:4px;'>${pos['current_value']:,.0f}</div>
</div>
<div>
<div class='small-muted'>P/L</div>
<div style='font-size:24px; font-weight:900; color:{pnl_color}; margin-top:4px;'>{pnl_sign}${abs(pos['pnl']):,.0f}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        # Этот return теперь стоит правильно
return

# Top view - ТОП 5 АКЦИЙ
    if st.session_state.view_mode == "top":
        # Сортируем по процентам от БОЛЬШЕГО к МЕНЬШЕМУ и берем первые 5
        processed = sorted(processed, key=lambda x: x['pct'], reverse=True)[:5]
        st.markdown("## 🔥 ТОП-5 АКЦИЙ ПО РОСТУ")

    # Отрисовка акций
    cols = st.columns(3)
    for idx, item in enumerate(processed):
        with cols[idx % 3]:
            pct = item['pct']
            sign = '+' if pct > 0 else ''
            pct_text = f"{sign}{pct:.2f}%"
            color_cls = "pos" if pct >= 0 else "neg"
            highlight = "highlight-100" if abs(pct) > 100 else ""

            # Значок позиции
            position_badge = ""
            if st.session_state.view_mode == "top" and idx < 5:
                position_icon = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][idx]
                position_badge = f"<div style='position:absolute; top:12px; right:12px; font-size:28px; z-index:10;'>{position_icon}</div>"

            # ВАЖНО: HTML внутри f-строки ПРИЖАТ ВЛЕВО, чтобы не было рамки "кода"
            stock_html = f"""<div class="stock-card {highlight}" style="position:relative;">
{position_badge}
<div class="stock-header">
<div style='width:100%;'>
<div class="stock-name">{item['Название']}</div>
<div class="stock-type">{item['Тип']}</div>
</div>
</div>
<div style='margin-top:auto; padding-top:16px;'>
<div style='display:flex; justify-content:space-between; align-items:flex-end;'>
<div>
<div class="old-price">{item['Базовая цена']:.0f}$</div>
<div class="current-price">{item['final_price']}$</div>
</div>
<div class="change-pct {color_cls}">{pct_text}</div>
</div>
</div>
</div>"""
            
            st.markdown(stock_html, unsafe_allow_html=True)

            # Кнопка покупки (выровнена по сетке Streamlit)
            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col2:
                if st.button("🛒 КУПИТЬ", key=f"buy_{item['Название']}_{idx}", use_container_width=True):
                    if not st.session_state.user:
                        st.error("⚠️ Войдите в профиль!")
                    else:
                        st.session_state.purchase_dialog = {
                            'stock_name': item['Название'],
                            'price': item['final_price'],
                            'idx': idx
                        }
                        st.rerun()

    # Purchase dialog
    if st.session_state.purchase_dialog:
        dialog_data = st.session_state.purchase_dialog
        st.markdown("<div class='purchase-dialog'>", unsafe_allow_html=True)
        st.markdown(f"## 💰 ПОКУПКА АКЦИЙ")
        st.markdown(f"### 📊 {dialog_data['stock_name']}")
        st.markdown(f"<div style='text-align:center; font-size:24px; color:#fff; margin:12px 0;'>Цена за 1 акцию: <span style='color:#f0b90b; font-weight:900;'>${dialog_data['price']:,.0f}</span></div>", unsafe_allow_html=True)
        
        quantity = st.slider("Количество акций:", min_value=1, max_value=100, value=1, step=1, key="quantity_slider")
        total_price = quantity * dialog_data['price']
        st.markdown(f"<div class='total-price'>💎 ИТОГО К ОПЛАТЕ: ${total_price:,.0f}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ ПОДТВЕРДИТЬ ПОКУПКУ", use_container_width=True):
                ws = get_buy_worksheet()
                if ws is None:
                    st.error("❌ Ошибка подключения к таблице покупок.")
                else:
                    try:
                        for _ in range(quantity):
                            tx_id = "TX-" + "".join(random.choices(string.digits, k=6))
                            ws.append_row([
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                st.session_state.user,
                                dialog_data['stock_name'],
                                dialog_data['price'],
                                tx_id
                            ])
                        load_purchases.clear()
                        st.success(f"✅ УСПЕШНО! Куплено {quantity} акций за ${total_price:,.0f}!")
                        st.session_state.purchase_dialog = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Ошибка при покупке: {e}")
        with col2:
            if st.button("❌ ОТМЕНА", use_container_width=True):
                st.session_state.purchase_dialog = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Debug panel
    if st.session_state.get('last_found_map'):
        with st.expander("🛠️ ПАНЕЛЬ ОТЛАДКИ"):
            for stock_name, mods in st.session_state['last_found_map'].items():
                if mods:
                    formatted = ", ".join([f"{m[0]} ({m[1]}%)" for m in mods])
                    st.write(f"• **{stock_name}**: {formatted}")
                else:
                    st.write(f"• **{stock_name}**: нет модификаторов")

# Sidebar
with st.sidebar:
    st.markdown("# 👤 ПРОФИЛЬ")
    
    if not st.session_state.user:
        st.markdown("### 🔐 Вход в систему")
        u = st.selectbox("Выберите пользователя:", ["артем", "богдан", "руслан", "разработчик"])
        if st.button("🚀 ВОЙТИ", use_container_width=True):
            st.session_state.user = u
            st.success(f"Добро пожаловать, {u.upper()}!")
            st.rerun()
    else:
        st.markdown(f"### Привет, **{st.session_state.user.upper()}**! 👋")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Статистика
        purchases = load_purchases()
        if not purchases.empty:
            try:
                header_cols = list(purchases.columns)
                col_who = next((c for c in header_cols if any(k in c.lower() for k in ["who", "кто", "user"])), header_cols[1] if len(header_cols) >= 2 else None)
                col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), header_cols[3] if len(header_cols) >= 4 else None)
                
                user_purchases = purchases[purchases[col_who] == st.session_state.user]
                if not user_purchases.empty:
                    total_invested = user_purchases[col_price].apply(safe_float).sum()
                    st.markdown(f"""
                        <div style='background:rgba(240,185,11,0.1); padding:16px; border-radius:8px; border:1px solid rgba(240,185,11,0.3); margin-bottom:12px;'>
                            <div style='font-size:12px; color:#9aa0a6; margin-bottom:6px;'>💰 ИНВЕСТИРОВАНО</div>
                            <div style='font-size:24px; font-weight:900; color:#f0b90b;'>${total_invested:,.0f}</div>
                            <div style='font-size:12px; color:#9aa0a6; margin-top:6px;'>📊 Сделок: {len(user_purchases)}</div>
                        </div>
                    """, unsafe_allow_html=True)
            except:
                pass
        
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚪 ВЫЙТИ", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### ℹ️ О СИСТЕМЕ")
    st.markdown("""
    **ВАНИНА ИГРА** — профессиональный симулятор торговли акциями
    
    ✨ **Возможности:**
    - 🔄 Реалтайм обновление
    - 📊 Интеграция с Google Sheets
    - 💎 Влияние золота на цены
    - 📈 Детальная аналитика
    - 🎯 История всех сделок
    
    ⏱️ Данные обновляются каждые 30 секунд
    """)

market_display()





