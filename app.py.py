import streamlit as st
import gspread
import pandas as pd
import random
import string
import textwrap
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
            0 12px 24px rgba(0,0,0,0.4),
            0 0 40px rgba(240,185,11,0.15);
        border-color: #f0b90b;
    }
    
    .stock-card:hover::after {
        opacity: 1;
    }

    .highlight-100 {
        border: 3px solid #f0b90b !important;
        box-shadow: 
            0 0 30px rgba(240,185,11,0.4),
            0 0 60px rgba(240,185,11,0.2),
            inset 0 0 40px rgba(240,185,11,0.1) !important;
        animation: pulseGlow 2s ease-in-out infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { 
            box-shadow: 
                0 0 30px rgba(240,185,11,0.4),
                0 0 60px rgba(240,185,11,0.2),
                inset 0 0 40px rgba(240,185,11,0.1);
        }
        50% { 
            box-shadow: 
                0 0 40px rgba(240,185,11,0.6),
                0 0 80px rgba(240,185,11,0.3),
                inset 0 0 50px rgba(240,185,11,0.15);
        }
    }

    .stock-header {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 12px;
    }
    
    .stock-name {
        font-size: 22px;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 0.5px;
        line-height: 1.3;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .stock-type {
        font-size: 12px;
        color: #9aa0a6;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 6px;
        padding: 4px 10px;
        background: rgba(240,185,11,0.1);
        border-radius: 6px;
        display: inline-block;
        border: 1px solid rgba(240,185,11,0.2);
    }

    .old-price {
        font-size: 14px;
        color: #6c757d;
        text-decoration: line-through;
        font-weight: 500;
        margin-bottom: 4px;
    }
    
    .current-price {
        font-size: 32px;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 
            0 0 10px rgba(255,255,255,0.3),
            0 2px 4px rgba(0,0,0,0.4);
        letter-spacing: -0.5px;
    }
    
    .change-pct {
        font-size: 28px;
        font-weight: 900;
        padding: 8px 16px;
        border-radius: 12px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .change-pct.pos {
        color: #0ecb81;
        background: rgba(14,203,129,0.15);
        border: 2px solid rgba(14,203,129,0.3);
        box-shadow: 
            0 0 20px rgba(14,203,129,0.2),
            inset 0 0 20px rgba(14,203,129,0.1);
    }
    
    .change-pct.neg {
        color: #f6465d;
        background: rgba(246,70,93,0.15);
        border: 2px solid rgba(246,70,93,0.3);
        box-shadow: 
            0 0 20px rgba(246,70,93,0.2),
            inset 0 0 20px rgba(246,70,93,0.1);
    }

    /* Purchase Dialog */
    .purchase-dialog {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%);
        padding: 40px;
        border-radius: 20px;
        border: 3px solid #f0b90b;
        box-shadow: 
            0 0 60px rgba(240,185,11,0.4),
            0 20px 60px rgba(0,0,0,0.6),
            inset 0 0 40px rgba(240,185,11,0.1);
        z-index: 1000;
        min-width: 500px;
        animation: dialogAppear 0.3s ease-out;
    }
    
    @keyframes dialogAppear {
        from {
            opacity: 0;
            transform: translate(-50%, -45%) scale(0.9);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
    }
    
    .total-price {
        background: linear-gradient(135deg, rgba(240,185,11,0.2), rgba(14,203,129,0.2));
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        color: #f0b90b;
        border: 2px solid rgba(240,185,11,0.3);
        margin: 20px 0;
        box-shadow: 
            0 0 30px rgba(240,185,11,0.2),
            inset 0 0 30px rgba(240,185,11,0.1);
    }

    /* Портфель */
    .portfolio-card {
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%);
        border: 2px solid #2b2f33;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .portfolio-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #f0b90b, #0ecb81);
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .portfolio-card:hover {
        transform: translateY(-4px);
        border-color: #f0b90b;
        box-shadow: 
            0 8px 20px rgba(0,0,0,0.3),
            0 0 30px rgba(240,185,11,0.15);
    }
    
    .portfolio-card:hover::before {
        opacity: 1;
    }
    
    .position-title {
        font-size: 24px;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .icon-badge {
        font-size: 18px;
        font-weight: 800;
        color: #f0b90b;
        background: rgba(240,185,11,0.15);
        padding: 6px 14px;
        border-radius: 8px;
        border: 2px solid rgba(240,185,11,0.3);
    }
    
    .small-muted {
        font-size: 12px;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* Прочие элементы */
    .gold-price-box {
        background: linear-gradient(135deg, rgba(240,185,11,0.15), rgba(240,185,11,0.05));
        border: 2px solid rgba(240,185,11,0.3);
        border-radius: 12px;
        padding: 16px 24px;
        text-align: center;
        box-shadow: 
            0 4px 12px rgba(240,185,11,0.2),
            inset 0 0 20px rgba(240,185,11,0.05);
    }
    
    .gold-price-label {
        font-size: 14px;
        color: #9aa0a6;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }
    
    .gold-price-value {
        font-size: 36px;
        font-weight: 900;
        color: #f0b90b;
        text-shadow: 
            0 0 10px rgba(240,185,11,0.5),
            0 2px 4px rgba(0,0,0,0.3);
    }

    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(240,185,11,0.3) 50%, 
            transparent 100%);
        margin: 24px 0;
    }

    /* Стили для таблиц */
    .dataframe {
        background: #1a1d20;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .dataframe th {
        background: #0e1113 !important;
        color: #f0b90b !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 12px !important;
        border: none !important;
    }
    
    .dataframe td {
        background: #1a1d20 !important;
        color: #ffffff !important;
        padding: 10px !important;
        border: 1px solid #2b2f33 !important;
    }
    
    /* Слайдер */
    .stSlider > div > div > div {
        background: #f0b90b !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: #1a1d20 !important;
        border: 2px solid #2b2b2b !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# ИНИЦИАЛИЗАЦИЯ SESSION STATE
# -----------------------
if 'user' not in st.session_state:
    st.session_state.user = None
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "all"
if 'purchase_dialog' not in st.session_state:
    st.session_state.purchase_dialog = None
if 'last_found_map' not in st.session_state:
    st.session_state.last_found_map = {}

# -----------------------
# GOOGLE SHEETS ПОДКЛЮЧЕНИЕ
# -----------------------
@st.cache_resource
def get_gspread_client():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Ошибка подключения к Google Sheets: {e}")
        return None

@st.cache_resource
def get_buy_worksheet():
    gc = get_gspread_client()
    if gc is None:
        return None
    try:
        sheet = gc.open_by_key(st.secrets["sheets"]["buy_sheet_id"])
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ Не удалось получить таблицу покупок: {e}")
        return None

@st.cache_resource
def get_stocks_worksheet():
    gc = get_gspread_client()
    if gc is None:
        return None
    try:
        sheet = gc.open_by_key(st.secrets["sheets"]["stocks_sheet_id"])
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ Не удалось получить таблицу акций: {e}")
        return None

@st.cache_resource
def get_modifiers_worksheet():
    gc = get_gspread_client()
    if gc is None:
        return None
    try:
        sheet = gc.open_by_key(st.secrets["sheets"]["modifiers_sheet_id"])
        return sheet.sheet1
    except Exception as e:
        st.error(f"❌ Не удалось получить таблицу модификаторов: {e}")
        return None

# -----------------------
# ЗАГРУЗКА ДАННЫХ
# -----------------------
@st.cache_data(ttl=30, show_spinner=False)
def load_purchases():
    ws = get_buy_worksheet()
    if ws is None:
        return pd.DataFrame()
    try:
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ Ошибка при загрузке покупок: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30, show_spinner=False)
def load_stocks():
    ws = get_stocks_worksheet()
    if ws is None:
        return pd.DataFrame()
    try:
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ Ошибка при загрузке акций: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30, show_spinner=False)
def load_modifiers():
    ws = get_modifiers_worksheet()
    if ws is None:
        return pd.DataFrame()
    try:
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ Ошибка при загрузке модификаторов: {e}")
        return pd.DataFrame()

# -----------------------
# ПОЛУЧЕНИЕ ЦЕНЫ ЗОЛОТА
# -----------------------
@st.cache_data(ttl=600, show_spinner=False)
def get_gold_price():
    try:
        import yfinance as yf
        gold = yf.Ticker("GC=F")
        hist = gold.history(period="1d")
        if hist.empty:
            return 2000.0
        return float(hist['Close'].iloc[-1])
    except:
        return 2000.0

# -----------------------
# УТИЛИТЫ
# -----------------------
def safe_float(val, default=0.0):
    try:
        if isinstance(val, str):
            val = val.replace(',', '').replace(' ', '').strip()
        return float(val)
    except:
        return default

def normalize_stock_name(name):
    return re.sub(r'\s+', ' ', str(name).strip().lower())

def apply_modifiers(stocks_df, modifiers_df):
    if stocks_df.empty or modifiers_df.empty:
        return stocks_df
    
    result = stocks_df.copy()
    result['final_price'] = result['Базовая цена'].apply(safe_float)
    
    found_map = {}
    
    # Колонки таблицы модификаторов
    mod_cols = list(modifiers_df.columns)
    col_stock = next((c for c in mod_cols if any(k in c.lower() for k in ["акция", "stock", "название"])), mod_cols[0] if len(mod_cols) >= 1 else None)
    col_mod_name = next((c for c in mod_cols if any(k in c.lower() for k in ["модификатор", "modifier", "название мод"])), mod_cols[1] if len(mod_cols) >= 2 else None)
    col_pct = next((c for c in mod_cols if any(k in c.lower() for k in ["процент", "percent", "%"])), mod_cols[2] if len(mod_cols) >= 3 else None)
    
    if col_stock is None or col_mod_name is None or col_pct is None:
        return result
    
    for idx, row in result.iterrows():
        stock_name = normalize_stock_name(row['Название'])
        found_map[stock_name] = []
        
        matching = modifiers_df[modifiers_df[col_stock].apply(lambda x: normalize_stock_name(x)) == stock_name]
        
        for _, mod in matching.iterrows():
            mod_name = str(mod[col_mod_name]).strip()
            pct_val = safe_float(mod[col_pct])
            
            if pct_val != 0:
                found_map[stock_name].append((mod_name, pct_val))
                result.at[idx, 'final_price'] = result.at[idx, 'final_price'] * (1 + pct_val / 100.0)
    
    st.session_state['last_found_map'] = found_map
    return result

# -----------------------
# ХЕДЕР С ЗОЛОТОМ
# -----------------------
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
st.markdown("<h1 class='main-title'>🏆 ВАНИНА ИГРА 🏆</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

gold_price = get_gold_price()
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.markdown(f"""
        <div class='gold-price-box'>
            <div class='gold-price-label'>💰 КУРС ЗОЛОТА</div>
            <div class='gold-price-value'>${gold_price:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("### 📊 ВИД")
    view_options = {
        "all": "🌐 ВСЕ АКЦИИ",
        "top": "🔥 ТОП-5",
        "portfolio": "💼 ПОРТФЕЛЬ"
    }
    selected = st.radio(
        "view_mode_label",
        options=list(view_options.keys()),
        format_func=lambda x: view_options[x],
        label_visibility="collapsed",
        key="view_mode_radio"
    )
    if selected != st.session_state.view_mode:
        st.session_state.view_mode = selected

# График золота
with col2:
    try:
        import yfinance as yf
        gold = yf.Ticker("GC=F")
        hist = gold.history(period="1mo", interval="1d")
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                line=dict(color='#f0b90b', width=3),
                fill='tozeroy',
                fillcolor='rgba(240,185,11,0.1)',
                name='Gold Price'
            ))
            fig.update_layout(
                title="📈 График Золота (1 Месяц)",
                xaxis_title="",
                yaxis_title="Цена ($)",
                template="plotly_dark",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(26,29,32,0.5)',
                font=dict(color='#ffffff', size=12),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.info("График золота недоступен")

st.markdown("<hr>", unsafe_allow_html=True)

# -----------------------
# ОСНОВНАЯ ЛОГИКА ОТОБРАЖЕНИЯ
# -----------------------
def market_display():
    stocks = load_stocks()
    modifiers = load_modifiers()
    
    if stocks.empty:
        st.warning("⚠️ Нет данных об акциях")
        return
    
    stocks = apply_modifiers(stocks, modifiers)
    
    processed = []
    for _, row in stocks.iterrows():
        base = safe_float(row['Базовая цена'])
        final = safe_float(row.get('final_price', base))
        pct = ((final - base) / base * 100) if base != 0 else 0.0
        
        processed.append({
            'Название': row['Название'],
            'Тип': row.get('Тип', 'N/A'),
            'Базовая цена': base,
            'final_price': int(round(final)),
            'pct': pct
        })
    
    # Portfolio view
    if st.session_state.view_mode == "portfolio":
        st.markdown("## 💼 МОЙ ПОРТФЕЛЬ")
        
        if not st.session_state.user:
            st.info("🔐 Войдите, чтобы увидеть портфель")
            return
        
        purchases = load_purchases()
        if purchases.empty:
            st.info("📊 У вас пока нет покупок")
            return
        
        # Определяем колонки
        header_cols = list(purchases.columns)
        col_who = next((c for c in header_cols if any(k in c.lower() for k in ["who", "кто", "user"])), header_cols[1] if len(header_cols) >= 2 else None)
        col_stock = next((c for c in header_cols if any(k in c.lower() for k in ["stock", "акция", "название"])), header_cols[2] if len(header_cols) >= 3 else None)
        col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), header_cols[3] if len(header_cols) >= 4 else None)
        
        if not col_who or not col_stock or not col_price:
            st.error("❌ Не удалось определить колонки таблицы покупок")
            return
        
        user_purchases = purchases[purchases[col_who] == st.session_state.user]
        
        if user_purchases.empty:
            st.info("📊 У вас пока нет покупок")
            return
        
        # Группируем по акциям
        grouped = user_purchases.groupby(col_stock).agg({
            col_price: ['sum', 'count', 'mean']
        }).reset_index()
        grouped.columns = ['stock_name', 'total_invested', 'quantity', 'avg_price']
        
        # Текущие цены
        stock_prices = {normalize_stock_name(s['Название']): s['final_price'] for s in processed}
        
        positions = []
        for _, g in grouped.iterrows():
            norm_name = normalize_stock_name(g['stock_name'])
            current_price = stock_prices.get(norm_name, g['avg_price'])
            current_value = current_price * g['quantity']
            pnl = current_value - g['total_invested']
            
            positions.append({
                'name': g['stock_name'],
                'quantity': g['quantity'],
                'avg_price': g['avg_price'],
                'total_invested': g['total_invested'],
                'current_price': current_price,
                'current_value': current_value,
                'pnl': pnl,
                'pnl_pct': (pnl / g['total_invested'] * 100) if g['total_invested'] != 0 else 0.0
            })
        
        # Суммарная статистика
        total_invested = sum([p['total_invested'] for p in positions])
        total_current = sum([p['current_value'] for p in positions])
        total_pnl = total_current - total_invested
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested != 0 else 0.0
        
        pnl_color = "#0ecb81" if total_pnl >= 0 else "#f6465d"
        pnl_sign = "+" if total_pnl >= 0 else ""
        
        st.markdown(f"""
            <div style='background:linear-gradient(135deg, rgba(240,185,11,0.15), rgba(14,203,129,0.1)); 
                        padding:30px; border-radius:16px; border:2px solid rgba(240,185,11,0.3); 
                        margin-bottom:24px; box-shadow:0 0 40px rgba(240,185,11,0.2);'>
                <div style='display:grid; grid-template-columns:repeat(4,1fr); gap:24px;'>
                    <div>
                        <div class='small-muted'>ИНВЕСТИРОВАНО</div>
                        <div style='font-size:28px; font-weight:900; color:#fff; margin-top:8px;'>${total_invested:,.0f}</div>
                    </div>
                    <div>
                        <div class='small-muted'>ТЕКУЩАЯ СТОИМОСТЬ</div>
                        <div style='font-size:28px; font-weight:900; color:#f0b90b; margin-top:8px;'>${total_current:,.0f}</div>
                    </div>
                    <div>
                        <div class='small-muted'>P/L СУММА</div>
                        <div style='font-size:28px; font-weight:900; color:{pnl_color}; margin-top:8px;'>{pnl_sign}${abs(total_pnl):,.0f}</div>
                    </div>
                    <div>
                        <div class='small-muted'>P/L ПРОЦЕНТ</div>
                        <div style='font-size:28px; font-weight:900; color:{pnl_color}; margin-top:8px;'>{pnl_sign}{total_pnl_pct:.2f}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Позиции
        for pos in positions:
            pnl_color = "#0ecb81" if pos['pnl'] >= 0 else "#f6465d"
            pnl_sign = "+" if pos['pnl'] >= 0 else ""
            
            st.markdown(f"""
                <div class='portfolio-card'>
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
                </div>
            """, unsafe_allow_html=True)

        return

    # Top view - ТОП 5 АКЦИЙ
    if st.session_state.view_mode == "top":
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

            # Кнопки - используем уникальный ключ с timestamp
            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col2:
                # FIX: Добавляем view_mode в ключ для уникальности
                btn_key = f"buy_{item['Название']}_{st.session_state.view_mode}_{idx}"
                if st.button("🛒 КУПИТЬ", key=btn_key, use_container_width=True):
                    if not st.session_state.user:
                        st.error("⚠️ Войдите в профиль!")
                    else:
                        st.session_state.purchase_dialog = {
                            'stock_name': item['Название'],
                            'price': item['final_price'],
                            'idx': idx
                        }
                        st.rerun()

    # Purchase dialog - FIX: Вынесен за пределы цикла
    if st.session_state.purchase_dialog:
        dialog_data = st.session_state.purchase_dialog
        
        # Создаем контейнер для диалога
        with st.container():
            st.markdown("<div class='purchase-dialog'>", unsafe_allow_html=True)
            st.markdown(f"## 💰 ПОКУПКА АКЦИЙ")
            st.markdown(f"### 📊 {dialog_data['stock_name']}")
            st.markdown(f"<div style='text-align:center; font-size:24px; color:#fff; margin:12px 0;'>Цена за 1 акцию: <span style='color:#f0b90b; font-weight:900;'>${dialog_data['price']:,.0f}</span></div>", unsafe_allow_html=True)
            
            quantity = st.slider("Количество акций:", min_value=1, max_value=100, value=1, step=1, key="quantity_slider")
            total_price = quantity * dialog_data['price']
            st.markdown(f"<div class='total-price'>💎 ИТОГО К ОПЛАТЕ: ${total_price:,.0f}</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ ПОДТВЕРДИТЬ ПОКУПКУ", key="confirm_purchase_btn", use_container_width=True):
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
                            # FIX: Сначала очищаем диалог, затем делаем rerun
                            st.session_state.purchase_dialog = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Ошибка при покупке: {e}")
            with col2:
                if st.button("❌ ОТМЕНА", key="cancel_purchase_btn", use_container_width=True):
                    # FIX: Сначала очищаем диалог, затем делаем rerun
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
    **ВАНИНА ИГРА** — профессиональный симулятор торговли акциями с учетом реального курса (золота)
    
    ✨ **Возможности:**
    - 🔄 Реалтайм обновление
    - 📊 Интеграция с Google Sheets
    - 💎 Влияние золота на цены
    - 📈 Детальная аналитика
    - 🎯 История всех сделок
    """)

    st.markdown("ИНСТРУКЦИЯ")
    st.markdown("""
    в верхнем блоке сайта присутствует встроенный (график золота)
    его колебания влияют только на региональные акции. 
    ниже есть все доступные акции (их можно купить).
    справа кнопки навигации. 
    ПРО ВЫСТАВКУ АКЦИЙ И ИХ ПРОДАЖУ: чтобы выставить свою акцию нужно 
    подойти к ведущему и сказать это с продпжей тоже самое.
    
    
    
    ⏱️ Данные обновляются каждые 30 секунд
    """)

market_display()
