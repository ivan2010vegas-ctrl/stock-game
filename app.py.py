import streamlit as st
import gspread
import pandas as pd
import random
import string
import textwrap
import plotly.graph_objects as go
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import re
import numpy as np

st.set_page_config(page_title="Ванина игра", layout="wide")

# Инициализация состояний
if 'details_stock' not in st.session_state:
    st.session_state.details_stock = None

# -----------------------
# CSS - СУПЕР ДЕТАЛИЗИРОВАННЫЙ ДИЗАЙН + МОДАЛЬНОЕ ОКНО
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

    /* Карточки акций с кнопкой "Подробнее" */
    .stock-card-wrapper {
        position: relative;
    }
    
    .details-btn {
        position: absolute;
        top: 12px;
        right: 12px;
        background: rgba(240,185,11,0.9);
        color: #000;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        opacity: 0;
        transform: translateY(-10px);
        transition: all 0.3s ease;
        z-index: 100;
        box-shadow: 0 4px 12px rgba(240,185,11,0.4);
    }
    
    .stock-card-wrapper:hover .details-btn {
        opacity: 1;
        transform: translateY(0);
    }
    
    .details-btn:hover {
        background: #f0b90b;
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(240,185,11,0.6);
    }

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
        font-weight: 600;
    }
    
    .old-price { 
        font-size: 16px; 
        color: #9aa0a6; 
        text-decoration: line-through;
        margin-bottom: 4px;
        font-weight: 500;
    }
    
    .current-price { 
        font-size: 32px; 
        font-weight: 900; 
        color: #FFFFFF;
        text-shadow: 0 2px 8px rgba(240,185,11,0.3);
        letter-spacing: -0.5px;
    }
    
    .change-pct { 
        font-size: 24px; 
        font-weight: 900; 
        padding: 8px 16px;
        border-radius: 12px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    
    .change-pct.pos { 
        color: #0ecb81; 
        background: rgba(14,203,129,0.15);
        border: 2px solid rgba(14,203,129,0.3);
    }
    
    .change-pct.neg { 
        color: #f6465d; 
        background: rgba(246,70,93,0.15);
        border: 2px solid rgba(246,70,93,0.3);
    }
    
    .highlight-100 {
        animation: pulse-glow 2s ease-in-out infinite;
    }
    
    @keyframes pulse-glow {
        0%, 100% {
            box-shadow: 
                0 12px 28px rgba(0,0,0,0.5),
                0 0 30px rgba(240,185,11,0.3);
        }
        50% {
            box-shadow: 
                0 12px 28px rgba(0,0,0,0.5),
                0 0 50px rgba(240,185,11,0.6);
        }
    }

    /* МОДАЛЬНОЕ ОКНО ДЕТАЛЕЙ */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.85);
        backdrop-filter: blur(8px);
        z-index: 9998;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .modal-content {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 90%;
        max-width: 1200px;
        max-height: 85vh;
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%);
        border-radius: 20px;
        border: 2px solid #f0b90b;
        box-shadow: 
            0 20px 60px rgba(0,0,0,0.8),
            0 0 40px rgba(240,185,11,0.3),
            inset 0 0 30px rgba(240,185,11,0.05);
        z-index: 9999;
        overflow: auto;
        animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translate(-50%, -40%);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%);
        }
    }
    
    .modal-header {
        padding: 30px 40px;
        border-bottom: 2px solid rgba(240,185,11,0.2);
        background: linear-gradient(90deg, rgba(240,185,11,0.1), transparent);
    }
    
    .modal-title {
        font-size: 36px;
        font-weight: 900;
        color: #fff;
        margin: 0;
        text-shadow: 0 2px 8px rgba(240,185,11,0.3);
    }
    
    .modal-price-info {
        display: flex;
        gap: 30px;
        align-items: baseline;
        margin-top: 12px;
    }
    
    .modal-current-price {
        font-size: 48px;
        font-weight: 900;
        color: #f0b90b;
        text-shadow: 0 4px 12px rgba(240,185,11,0.4);
    }
    
    .modal-change {
        font-size: 28px;
        font-weight: 800;
        padding: 8px 20px;
        border-radius: 12px;
    }
    
    .modal-change.pos {
        color: #0ecb81;
        background: rgba(14,203,129,0.15);
    }
    
    .modal-change.neg {
        color: #f6465d;
        background: rgba(246,70,93,0.15);
    }
    
    .modal-body {
        padding: 30px 40px;
    }
    
    .close-modal-btn {
        position: absolute;
        top: 20px;
        right: 20px;
        background: rgba(246,70,93,0.2);
        border: 2px solid #f6465d;
        color: #f6465d;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        font-size: 24px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    }
    
    .close-modal-btn:hover {
        background: #f6465d;
        color: #fff;
        transform: rotate(90deg) scale(1.1);
        box-shadow: 0 0 20px rgba(246,70,93,0.6);
    }

    /* Диалог покупки */
    .purchase-dialog {
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%);
        border-radius: 16px;
        border: 2px solid #f0b90b;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 
            0 8px 32px rgba(0,0,0,0.5),
            0 0 40px rgba(240,185,11,0.2);
    }
    
    .total-price {
        background: rgba(240,185,11,0.1);
        border: 2px solid rgba(240,185,11,0.3);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        font-size: 28px;
        font-weight: 900;
        color: #f0b90b;
        margin: 20px 0;
        text-shadow: 0 2px 8px rgba(240,185,11,0.3);
    }

    /* Стили для портфолио */
    .portfolio-card {
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%);
        border-radius: 16px;
        border: 2px solid #2b2f33;
        padding: 24px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    
    .portfolio-card:hover {
        border-color: #f0b90b;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4), 0 0 20px rgba(240,185,11,0.2);
        transform: translateY(-4px);
    }
    
    .small-muted {
        color: #9aa0a6;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* Скрываем стандартные элементы Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# -----------------------
# GOOGLE SHEETS
# -----------------------
@st.cache_resource
def get_google_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Ошибка подключения к Google Sheets: {e}")
        return None

def get_stocks_worksheet():
    client = get_google_client()
    if client is None:
        return None
    try:
        sheet = client.open_by_key(st.secrets["spreadsheet_id"])
        return sheet.worksheet("stocks")
    except Exception as e:
        st.error(f"Ошибка открытия листа 'stocks': {e}")
        return None

def get_mods_worksheet():
    client = get_google_client()
    if client is None:
        return None
    try:
        sheet = client.open_by_key(st.secrets["spreadsheet_id"])
        return sheet.worksheet("Mods")
    except Exception as e:
        st.error(f"Ошибка открытия листа 'Mods': {e}")
        return None

def get_buy_worksheet():
    client = get_google_client()
    if client is None:
        return None
    try:
        sheet = client.open_by_key(st.secrets["spreadsheet_id"])
        return sheet.worksheet("buy")
    except Exception as e:
        st.error(f"Ошибка открытия листа 'buy': {e}")
        return None

# -----------------------
# КЕШИ
# -----------------------
@st.cache_data(ttl=30)
def load_stocks():
    ws = get_stocks_worksheet()
    if ws is None:
        return pd.DataFrame()
    try:
        data = ws.get_all_values()
        if len(data) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки акций: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_mods():
    ws = get_mods_worksheet()
    if ws is None:
        return pd.DataFrame()
    try:
        data = ws.get_all_values()
        if len(data) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки модификаторов: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_purchases():
    ws = get_buy_worksheet()
    if ws is None:
        return pd.DataFrame()
    try:
        data = ws.get_all_values()
        if len(data) < 2:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Ошибка загрузки покупок: {e}")
        return pd.DataFrame()

def safe_float(val):
    try:
        return float(val)
    except:
        return 0.0

def safe_int(val):
    try:
        return int(float(val))
    except:
        return 0

# -----------------------
# ГЕНЕРАЦИЯ ИСТОРИЧЕСКИХ ДАННЫХ
# -----------------------
def generate_historical_data(stock_name, current_price, base_price, days=365):
    """Генерирует исторические данные для графика"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Начинаем с базовой цены и приходим к текущей
    prices = []
    price = base_price
    
    # Вычисляем тренд
    total_change = current_price - base_price
    daily_trend = total_change / days
    
    for i in range(days):
        # Добавляем случайную волатильность
        volatility = random.uniform(-price * 0.05, price * 0.05)
        price += daily_trend + volatility
        
        # Ограничиваем минимум
        price = max(price, base_price * 0.3)
        prices.append(price)
    
    # Корректируем последнюю цену к текущей
    prices[-1] = current_price
    
    return dates, prices

def create_stock_chart(stock_name, dates, prices, current_price, pct_change):
    """Создает график в стиле Binance"""
    
    # Определяем цвет линии
    line_color = '#f0b90b'  # Золотой как на Binance
    
    fig = go.Figure()
    
    # Добавляем линию графика
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=stock_name,
        line=dict(color=line_color, width=2),
        fill='tonexty',
        fillcolor=f'rgba(240, 185, 11, 0.1)',
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Цена: $%{y:,.0f}<extra></extra>'
    ))
    
    # Настройка внешнего вида
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0e1113',
        plot_bgcolor='#0e1113',
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            showline=False,
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            showline=False,
            zeroline=False,
            tickformat='$,.0f'
        ),
        hovermode='x unified',
        font=dict(color='#9aa0a6', size=12),
        showlegend=False
    )
    
    return fig

# -----------------------
# ИНИЦИАЛИЗАЦИЯ SESSION STATE
# -----------------------
if 'user' not in st.session_state:
    st.session_state.user = None
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "all"
if 'purchase_dialog' not in st.session_state:
    st.session_state.purchase_dialog = None

# -----------------------
# ГЛАВНЫЙ ИНТЕРФЕЙС
# -----------------------
st.markdown("<div class='header-container'><h1 class='main-title'>⚡ ВАНИНА ИГРА: БИРЖА ⚡</h1></div>", unsafe_allow_html=True)

# Вкладки режимов
tab1, tab2, tab3 = st.tabs(["📊 ВСЕ АКЦИИ", "🔥 ТОП-5", "💼 МОЙ ПОРТФЕЛЬ"])

with tab1:
    st.session_state.view_mode = "all"
with tab2:
    st.session_state.view_mode = "top"
with tab3:
    st.session_state.view_mode = "portfolio"

# -----------------------
# РЕНДЕРИНГ РЫНКА
# -----------------------
def market_display():
    stocks_df = load_stocks()
    mods_df = load_mods()

    if stocks_df.empty:
        st.warning("⚠️ Данные акций не загружены.")
        return

    # Словарь для хранения найденных модификаторов
    found_map = {}

    # Обработка данных
    processed = []
    for _, row in stocks_df.iterrows():
        base_price = safe_float(row.get('Базовая цена', 0))
        final_price = base_price
        stock_name = row.get('Название', '')
        stock_type = row.get('Тип', '')

        mods_applied = []

        if not mods_df.empty:
            for _, mod_row in mods_df.iterrows():
                keyword = str(mod_row.get('Золото', '')).strip().lower()
                pct_value = safe_float(mod_row.get('Процент', 0))

                if keyword and keyword in stock_name.lower():
                    final_price *= (1 + pct_value / 100.0)
                    mods_applied.append((keyword, pct_value))

        found_map[stock_name] = mods_applied

        pct = ((final_price - base_price) / base_price * 100) if base_price > 0 else 0.0

        processed.append({
            'Название': stock_name,
            'Тип': stock_type,
            'Базовая цена': base_price,
            'final_price': round(final_price),
            'pct': pct
        })

    st.session_state['last_found_map'] = found_map

    # Portfolio view
    if st.session_state.view_mode == "portfolio":
        st.markdown("## 💼 МОЙ ПОРТФЕЛЬ")
        
        if not st.session_state.user:
            st.info("🔐 Войдите в профиль, чтобы увидеть портфель")
            return

        purchases = load_purchases()
        if purchases.empty:
            st.info("Портфель пуст. Начните инвестировать!")
            return

        try:
            header_cols = list(purchases.columns)
            col_who = next((c for c in header_cols if any(k in c.lower() for k in ["who", "кто", "user"])), header_cols[1] if len(header_cols) >= 2 else None)
            col_stock = next((c for c in header_cols if any(k in c.lower() for k in ["stock", "акция"])), header_cols[2] if len(header_cols) >= 3 else None)
            col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), header_cols[3] if len(header_cols) >= 4 else None)

            user_purchases = purchases[purchases[col_who] == st.session_state.user]

            if user_purchases.empty:
                st.info("У вас пока нет акций в портфеле")
                return

            # Группируем по акциям
            portfolio_grouped = user_purchases.groupby(col_stock).agg(
                quantity=(col_stock, 'count'),
                avg_price=(col_price, lambda x: sum(safe_float(v) for v in x) / len(x))
            ).reset_index()

            # Обогащаем текущими ценами
            current_prices = {item['Название']: item['final_price'] for item in processed}

            portfolio_data = []
            for _, pos in portfolio_grouped.iterrows():
                stock_name = pos[col_stock]
                quantity = pos['quantity']
                avg_price = pos['avg_price']
                current_price = current_prices.get(stock_name, avg_price)
                
                invested = avg_price * quantity
                current_value = current_price * quantity
                pnl = current_value - invested
                pnl_pct = (pnl / invested * 100) if invested > 0 else 0

                portfolio_data.append({
                    'stock_name': stock_name,
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'invested': invested,
                    'current_value': current_value,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })

            # Общая статистика
            total_invested = sum(p['invested'] for p in portfolio_data)
            total_value = sum(p['current_value'] for p in portfolio_data)
            total_pnl = total_value - total_invested
            total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

            pnl_color = '#0ecb81' if total_pnl >= 0 else '#f6465d'
            pnl_sign = '+' if total_pnl >= 0 else ''

            st.markdown(f"""
                <div style='background:linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
                     padding:30px; border-radius:16px; border:2px solid #f0b90b;
                     box-shadow:0 8px 32px rgba(0,0,0,0.5), 0 0 40px rgba(240,185,11,0.2); margin-bottom:24px;'>
                    <div style='text-align:center;'>
                        <div style='font-size:16px; color:#9aa0a6; margin-bottom:8px; text-transform:uppercase; letter-spacing:2px;'>
                            💰 ОБЩАЯ СТОИМОСТЬ ПОРТФЕЛЯ
                        </div>
                        <div style='font-size:56px; font-weight:900; color:#f0b90b; margin:12px 0;
                             text-shadow:0 4px 12px rgba(240,185,11,0.4);'>
                            ${total_value:,.0f}
                        </div>
                        <div style='font-size:24px; font-weight:800; color:{pnl_color}; margin-top:8px;'>
                            {pnl_sign}${abs(total_pnl):,.0f} ({pnl_sign}{total_pnl_pct:.2f}%)
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Позиции
            for pos in portfolio_data:
                pnl_color = '#0ecb81' if pos['pnl'] >= 0 else '#f6465d'
                pnl_sign = '+' if pos['pnl'] >= 0 else ''

                st.markdown(f"""
                <div class='portfolio-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;'>
                        <div>
                            <div style='font-size:28px; font-weight:900; color:#fff;'>{pos['stock_name']}</div>
                            <div class='small-muted'>Количество: {pos['quantity']} шт.</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:32px; font-weight:900; color:{pnl_color};'>{pnl_sign}{pos['pnl_pct']:.2f}%</div>
                        </div>
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

        except Exception as e:
            st.error(f"Ошибка загрузки портфеля: {e}")
        return

    # Top view
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
                position_badge = f"<div style='position:absolute; top:12px; left:12px; font-size:28px; z-index:10;'>{position_icon}</div>"

            # ID для уникальной идентификации
            stock_id = f"{item['Название']}_{idx}"

            # HTML карточки с кнопкой "Подробнее"
            stock_html = f"""
<div class="stock-card-wrapper">
    <div class="stock-card {highlight}" style="position:relative;">
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
    </div>
</div>"""

            st.markdown(stock_html, unsafe_allow_html=True)

            # Кнопки
            btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1.6, 1.2])
            
            with btn_col1:
                if st.button("📊 ПОДРОБНЕЕ", key=f"details_{stock_id}", use_container_width=True):
                    st.session_state.details_stock = item
                    st.rerun()
            
            with btn_col2:
                if st.button("🛒 КУПИТЬ", key=f"buy_{stock_id}", use_container_width=True):
                    if not st.session_state.user:
                        st.error("⚠️ Войдите в профиль!")
                    else:
                        st.session_state.purchase_dialog = {
                            'stock_name': item['Название'],
                            'price': item['final_price'],
                            'idx': idx
                        }
                        st.rerun()

    # МОДАЛЬНОЕ ОКНО ДЕТАЛЕЙ
    if st.session_state.details_stock:
        stock = st.session_state.details_stock
        
        # Генерируем исторические данные
        dates, prices = generate_historical_data(
            stock['Название'],
            stock['final_price'],
            stock['Базовая цена'],
            days=365
        )
        
        # Создаем график
        fig = create_stock_chart(
            stock['Название'],
            dates,
            prices,
            stock['final_price'],
            stock['pct']
        )
        
        pct = stock['pct']
        sign = '+' if pct > 0 else ''
        pct_text = f"{sign}{pct:.2f}%"
        color_cls = "pos" if pct >= 0 else "neg"
        
        # Модальное окно
        st.markdown("---")
        st.markdown(f"""
        <div style='background:linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
             padding:30px; border-radius:20px; border:2px solid #f0b90b;
             box-shadow:0 20px 60px rgba(0,0,0,0.8), 0 0 40px rgba(240,185,11,0.3); margin:20px 0;'>
            
            <div style='border-bottom:2px solid rgba(240,185,11,0.2); padding-bottom:20px; margin-bottom:30px;
                 background:linear-gradient(90deg, rgba(240,185,11,0.1), transparent);'>
                <div style='font-size:36px; font-weight:900; color:#fff; margin:0;
                     text-shadow:0 2px 8px rgba(240,185,11,0.3);'>
                    {stock['Название']}
                </div>
                <div style='color:#9aa0a6; font-size:14px; text-transform:uppercase; 
                     letter-spacing:1.5px; margin-top:8px;'>
                    {stock['Тип']}
                </div>
                <div style='display:flex; gap:30px; align-items:baseline; margin-top:12px;'>
                    <div style='font-size:48px; font-weight:900; color:#f0b90b;
                         text-shadow:0 4px 12px rgba(240,185,11,0.4);'>
                        ${stock['final_price']:,.0f}
                    </div>
                    <div class='modal-change {color_cls}' style='font-size:28px; font-weight:800;
                         padding:8px 20px; border-radius:12px;'>
                        {pct_text}
                    </div>
                </div>
                <div style='color:#9aa0a6; font-size:14px; margin-top:12px;'>
                    Базовая цена: ${stock['Базовая цена']:,.0f}
                </div>
            </div>
            
            <div style='margin-bottom:20px;'>
                <div style='color:#9aa0a6; font-size:14px; text-transform:uppercase; 
                     letter-spacing:1.5px; margin-bottom:12px;'>
                    📈 ГРАФИК ЗА ВСЁ ВРЕМЯ
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # График
        st.plotly_chart(fig, use_container_width=True)
        
        # Кнопка закрытия
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✕ Закрыть", key="close_modal_btn", use_container_width=True, type="primary"):
                st.session_state.details_stock = None
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
    - 📊 **НОВОЕ:** Детальные графики акций
    
    ⏱️ Данные обновляются каждые 30 секунд
    """)

market_display()
