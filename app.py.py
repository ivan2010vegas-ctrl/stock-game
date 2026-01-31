import streamlit as st
import gspread
import pandas as pd
import random
import string
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re
import time

st.set_page_config(page_title="Ванина игра", layout="wide", initial_sidebar_state="expanded")

# -----------------------
# CSS - МАКСИМАЛЬНО УЛУЧШЕННЫЙ ДИЗАЙН
# -----------------------
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    .stApp { 
        background: linear-gradient(135deg, #0a0d10 0%, #0b0e11 50%, #0d1015 100%);
        color: #FFFFFF; 
    }

    /* АНИМАЦИИ */
    @keyframes borderGlow {
        0%, 100% { 
            box-shadow: 0 0 20px rgba(240,185,11,0.3), 0 0 40px rgba(14,203,129,0.2);
        }
        50% { 
            box-shadow: 0 0 40px rgba(240,185,11,0.5), 0 0 60px rgba(14,203,129,0.3);
        }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.8; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    /* АНИМАЦИЯ КОСТЕЙ */
    @keyframes diceRoll {
        0% { transform: rotateX(0deg) rotateY(0deg); }
        25% { transform: rotateX(180deg) rotateY(180deg); }
        50% { transform: rotateX(360deg) rotateY(360deg); }
        75% { transform: rotateX(540deg) rotateY(180deg); }
        100% { transform: rotateX(720deg) rotateY(360deg); }
    }
    
    @keyframes diceJump {
        0%, 100% { transform: translateY(0) scale(1); }
        50% { transform: translateY(-30px) scale(1.2); }
    }
    
    /* АНИМАЦИЯ ПОБЕДЫ */
    @keyframes winGlow {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(14,203,129,0.5), 0 0 60px rgba(14,203,129,0.3);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 60px rgba(14,203,129,0.8), 0 0 100px rgba(14,203,129,0.5);
            transform: scale(1.05);
        }
    }
    
    @keyframes confetti {
        0% { transform: translateY(0) rotate(0deg); opacity: 1; }
        100% { transform: translateY(1000px) rotate(720deg); opacity: 0; }
    }
    
    @keyframes loseShake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }

    /* ЗАГОЛОВОК */
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
        box-shadow: 0 4px 20px rgba(240,185,11,0.3);
    }

    .main-title {
        color: #f0b90b;
        margin: 0;
        text-shadow: 0 0 20px rgba(240,185,11,0.5), 2px 2px 4px rgba(0,0,0,0.5);
        font-size: 48px;
        font-weight: 900;
        letter-spacing: 2px;
        text-align: center;
        animation: float 3s ease-in-out infinite;
    }

    /* КНОПКИ */
    div.stButton > button {
        background: linear-gradient(135deg, #1a1d20 0%, #000000 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 2px solid #2b2b2b !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        font-size: 15px !important;
        letter-spacing: 0.5px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    div.stButton > button:hover {
        border-color: #f0b90b !important;
        box-shadow: 0 0 25px rgba(240,185,11,0.5), inset 0 0 20px rgba(240,185,11,0.1) !important;
        transform: translateY(-3px) scale(1.03) !important;
    }
    
    div.stButton > button:active {
        animation: pulse 0.3s ease !important;
    }

    /* КАРТОЧКИ АКЦИЙ */
    .stock-card { 
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
        border-radius: 16px; 
        padding: 24px; 
        border: 2px solid #2b2f33; 
        margin-bottom: 16px; 
        min-height: 220px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        animation: slideInLeft 0.5s ease;
    }
    
    .stock-card:hover {
        transform: translateY(-8px) scale(1.03);
        box-shadow: 0 16px 32px rgba(0,0,0,0.6), 0 0 40px rgba(240,185,11,0.3);
        border-color: #f0b90b;
    }
    
    .stock-name { 
        color: #FFFFFF; 
        font-size: 24px; 
        font-weight: 800;
        animation: fadeIn 0.6s ease;
    }
    
    .stock-type { 
        color: #9aa0a6; 
        font-size: 12px; 
        text-transform: uppercase; 
        background: rgba(154,160,166,0.15);
        padding: 6px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 6px;
        animation: slideInRight 0.7s ease;
    }
    
    .current-price { 
        color: #f0b90b; 
        font-size: 36px; 
        font-weight: 900;
        text-shadow: 0 0 15px rgba(240,185,11,0.5);
        animation: pulse 2s ease infinite;
    }
    
    .change-pct { 
        font-size: 26px; 
        font-weight: 900;
    }
    
    .pos { 
        color: #0ecb81;
        animation: winGlow 2s ease infinite;
    } 
    
    .neg { 
        color: #f6465d;
        animation: shake 0.5s ease;
    }

    /* ИГРА В КОСТИ */
    .dice-container {
        background: linear-gradient(135deg, rgba(240,185,11,0.15) 0%, rgba(26,29,32,0.9) 100%);
        border: 3px solid #f0b90b;
        border-radius: 20px;
        padding: 40px;
        margin: 20px 0;
        box-shadow: 0 12px 40px rgba(240,185,11,0.4);
        animation: slideInLeft 0.6s ease;
    }
    
    .dice {
        width: 100px;
        height: 100px;
        background: linear-gradient(135deg, #fff, #e0e0e0);
        border-radius: 15px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        font-weight: 900;
        color: #000;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        margin: 10px;
        border: 3px solid #f0b90b;
    }
    
    .dice.rolling {
        animation: diceRoll 1s ease-in-out, diceJump 1s ease-in-out;
    }
    
    .dice-result-win {
        background: linear-gradient(135deg, rgba(14,203,129,0.2), rgba(14,203,129,0.05));
        border: 3px solid #0ecb81;
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        animation: winGlow 1s ease;
    }
    
    .dice-result-lose {
        background: linear-gradient(135deg, rgba(246,70,93,0.2), rgba(246,70,93,0.05));
        border: 3px solid #f6465d;
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        animation: loseShake 0.5s ease;
    }
    
    .bet-option {
        background: linear-gradient(135deg, #1a1d20, #0e1113);
        border: 2px solid #2b2f33;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .bet-option:hover {
        border-color: #f0b90b;
        transform: translateX(5px);
        box-shadow: 0 4px 16px rgba(240,185,11,0.3);
    }
    
    .bet-option.selected {
        border-color: #0ecb81;
        background: linear-gradient(135deg, rgba(14,203,129,0.2), rgba(14,203,129,0.05));
    }
    
    .balance-display {
        background: linear-gradient(135deg, rgba(240,185,11,0.2), rgba(240,185,11,0.05));
        border: 2px solid #f0b90b;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        margin: 20px 0;
        animation: float 3s ease-in-out infinite;
    }
    
    .balance-amount {
        font-size: 42px;
        font-weight: 900;
        color: #f0b90b;
        text-shadow: 0 0 20px rgba(240,185,11,0.6);
    }

    /* ЗОЛОТО */
    .gold-widget {
        background: linear-gradient(135deg, rgba(240,185,11,0.15) 0%, rgba(26,29,32,0.8) 100%);
        border: 2px solid #f0b90b;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(240,185,11,0.25);
        animation: slideInRight 0.5s ease;
    }

    /* ПОРТФЕЛЬ */
    .portfolio-header { 
        background: linear-gradient(135deg, rgba(240,185,11,0.15) 0%, rgba(26,29,32,0.8) 100%); 
        border-radius: 16px; 
        padding: 32px; 
        margin-bottom: 24px; 
        border: 2px solid #f0b90b;
        box-shadow: 0 8px 24px rgba(240,185,11,0.3);
        animation: fadeIn 0.6s ease;
    }
    
    .stat-value { 
        color: #FFFFFF; 
        font-size: 32px; 
        font-weight: 900;
        animation: pulse 2s ease infinite;
    }
    
    .position-item { 
        background: linear-gradient(135deg, #1a1d20 0%, #161719 100%); 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 16px; 
        border: 2px solid #2b2f33;
        transition: all 0.3s ease;
        animation: slideInLeft 0.5s ease;
    }
    
    .position-item:hover {
        border-color: #f0b90b;
        transform: translateX(8px);
    }

    /* ДИАЛОГ ПОКУПКИ */
    .purchase-dialog { 
        background: linear-gradient(180deg, #1a1d20, #0e1113); 
        border: 3px solid #f0b90b; 
        border-radius: 16px; 
        padding: 28px; 
        margin: 16px 0;
        box-shadow: 0 12px 40px rgba(240,185,11,0.4);
        animation: slideInLeft 0.5s ease;
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
        animation: winGlow 2s ease infinite;
    }

    /* НОВОСТИ */
    .news-banner {
        background: linear-gradient(135deg, rgba(240,185,11,0.08) 0%, rgba(26,29,32,0.6) 100%);
        border-left: 4px solid #f0b90b;
        border-right: 4px solid #0ecb81;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        animation: slideInLeft 0.6s ease;
    }

    /* ИКОНКИ И ЗНАЧКИ */
    .icon-badge {
        background: rgba(240,185,11,0.2);
        padding: 8px 16px;
        border-radius: 20px;
        color: #f0b90b;
        font-weight: 700;
        border: 1px solid rgba(240,185,11,0.3);
        animation: pulse 2s ease infinite;
    }
    
    /* КОНФЕТТИ */
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #f0b90b;
        animation: confetti 3s ease-out forwards;
        z-index: 9999;
    }
    
    .confetti:nth-child(2n) { background: #0ecb81; }
    .confetti:nth-child(3n) { background: #f6465d; }
    </style>
""", unsafe_allow_html=True)

# Helper functions
def safe_float(value):
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace('%', '').replace(',', '.').strip()
        return float(value)
    except:
        return 0.0

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
    return default

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

def sum_modifiers_and_list(raw_text, ref_df):
    if ref_df is None or ref_df.empty:
        return 0.0, [], []

    def normalize(s):
        return re.sub(r'\W+', '', str(s).lower())

    ref_map = {}
    for _, r in ref_df.iterrows():
        typ = val = None
        pct = 0.0
        for col in r.index:
            if col is None:
                continue
            lc = str(col).lower()
            if "тип" in lc or lc == "type":
                typ = r.get(col)
            if "знач" in lc or "value" in lc:
                val = r.get(col)
            if "%" in str(col).lower() or "percent" in lc:
                pct = safe_float(r.get(col, 0))

        typ_str = str(typ).strip() if typ else ""
        val_str = str(val).strip() if val else ""
        display = f"{typ_str} {val_str}" if typ_str and val_str else (val_str or typ_str)

        keys = set()
        if val_str:
            keys.add(normalize(val_str))
        if typ_str:
            keys.add(normalize(typ_str))
        if typ_str and val_str:
            keys.add(normalize(f"{typ_str} {val_str}"))

        for k in keys:
            if k not in ref_map:
                ref_map[k] = (display, safe_float(pct))

    tokens = split_modifiers(raw_text)
    found = []
    matched_keys = set()

    for tok in tokens:
        if not tok:
            continue
        tok_norm = normalize(tok)
        if tok_norm in ref_map and tok_norm not in matched_keys:
            matched_keys.add(tok_norm)
            found.append(ref_map[tok_norm])

    total_pct = sum([safe_float(p) for (_, p) in found])
    return total_pct, found, tokens

# Google Sheets
@st.cache_resource
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=5)
def load_stocks_table():
    try:
        return pd.DataFrame(get_gspread_client().open("«Акции»").worksheet("Лист1").get_all_records())
    except Exception as e:
        st.error(f"❌ Ошибка: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_reference_tables():
    client = get_gspread_client()
    try:
        df_zavod = pd.DataFrame(client.open("«Таблица дификаторы_заводские_проценты»").sheet1.get_all_records())
    except:
        df_zavod = pd.DataFrame(columns=["Значение", "%"])
    try:
        df_region = pd.DataFrame(client.open("Таблица «Модификаторы_региональные_проценты»").sheet1.get_all_records())
    except:
        df_region = pd.DataFrame(columns=["Значение", "%"])
    return df_zavod, df_region

@st.cache_resource
def get_buy_worksheet():
    try:
        return get_gspread_client().open("Таблица «Покупки»").worksheet("Лист6")
    except:
        return None

@st.cache_data(ttl=10)
def load_purchases():
    try:
        return pd.DataFrame(get_gspread_client().open("Таблица «Покупки»").worksheet("Лист6").get_all_records())
    except:
        return pd.DataFrame(columns=["time", "who", "name", "price", "tx_id"])

# Игра в кости - данные
DICE_ODDS = {
    2: {"prob": 97.22, "coef": 1.02},
    3: {"prob": 91.67, "coef": 1.07},
    4: {"prob": 83.33, "coef": 1.18},
    5: {"prob": 72.22, "coef": 1.35},
    6: {"prob": 58.33, "coef": 1.65},
    7: {"prob": 41.67, "coef": 2.20},
    8: {"prob": 27.78, "coef": 3.10},
    9: {"prob": 16.67, "coef": 5.00},
    10: {"prob": 8.33, "coef": 9.50},
    11: {"prob": 2.78, "coef": 28.00}
}

# Initial state
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
st.session_state.setdefault('purchase_dialog', None)
st.session_state.setdefault('user_balance', 10000)  # Начальный баланс
st.session_state.setdefault('dice_rolling', False)
st.session_state.setdefault('dice_result', None)

# Функция игры в кости
def play_dice_game(bet_amount, target):
    """Играет в кости и возвращает результат"""
    # Бросаем две кости
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    # Проверяем выигрыш
    won = total > target
    
    if won:
        winnings = int(bet_amount * DICE_ODDS[target]["coef"])
        return True, total, dice1, dice2, winnings
    else:
        return False, total, dice1, dice2, 0

# Звуковые эффекты (простые beep через HTML5 audio)
def play_sound(sound_type):
    """Проигрывает звук победы или проигрыша"""
    if sound_type == "win":
        # Звук победы - высокая нота
        st.markdown("""
            <audio autoplay>
                <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTUIGGe57OehUBELTKXh8bllHAU2j9bx0n0pBCJ1xe/glEILElyx6OyrWBUIQ5zd8sFuJAUuhM/z24s4CBdnvOzno1IRCkal4PG5ZBwENo/V8dJ9KgQidb/x4JRBDBJcr+jrq1gVCEOc3fK/bSQFLoTO89uLOAgXZ7vs56NSEA=="/>
            </audio>
        """, unsafe_allow_html=True)
    else:
        # Звук проигрыша - низкая нота
        st.markdown("""
            <audio autoplay>
                <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACAgoSHY1dcb5CmopReNTRdnM7XpV0ZBTuY2O2+bSIEKn/M8daCOQcZZ7rq5JdLDQtQp+LvsmAaBTiP1PDIeCgEJXbF7tyPQAoTXrPn6aZUEglGnN/xt2oeBS2Cze/WiDYHGGe67OagTg8KTKXh8LhjGgU1jtXx0HwoAyFzw+7gkkALE1yu5+mrVxQIQ5zc8b1qIgQrfs7w1og2BhhmuOnmn04OCkyl4e+4YxoFNY7V8NB8KAMhc8Pu4JJACw=="/>
            </audio>
        """, unsafe_allow_html=True)

@st.fragment(run_every=30)
def market_display():
    # Заголовок
    st.markdown("<div class='header-container'><h1 class='main-title'>💎 ВАНИНА ИГРА 💎</h1></div>", unsafe_allow_html=True)

    # Новости
    news = [
        "Рынок золота демонстрирует стабильный рост - эксперты прогнозируют дальнейшее укрепление позиций",
        "Новый завод открыл двери - аналитики ожидают значительный прирост к заводским акциям",
        "Крупные инвесторы прогнозируют масштабный рост цен на ближайший квартал",
        "Региональные акции показывают рекордный рост за последний месяц",
        "Аналитики повышают прогнозы по золоту - ожидается прорыв ключевого уровня",
    ]
    st.markdown(f"<div class='news-banner'><h3 style='color:#ccccff; margin:0;'>📰 <strong>НОВОСТИ:</strong> {random.choice(news)}</h3></div>", unsafe_allow_html=True)

    # Обновление
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("🔄 ОБНОВИТЬ", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col3:
        # Отображаем баланс
        st.markdown(f"""
            <div style='background:rgba(240,185,11,0.15); border:2px solid #f0b90b; border-radius:12px; padding:12px; text-align:center;'>
                <div style='font-size:12px; color:#9aa0a6;'>💰 БАЛАНС</div>
                <div style='font-size:20px; font-weight:900; color:#f0b90b;'>${st.session_state.user_balance:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    # Золото
    last_close = st.session_state.gold_history[-1]['close']
    c = last_close + random.uniform(-15, 15)
    st.session_state.gold_history.append({'open': last_close, 'high': max(last_close, c)+7, 'low': min(last_close, c)-7, 'close': c})
    if len(st.session_state.gold_history) > 60:
        st.session_state.gold_history.pop(0)

    # Загрузка
    df_raw = load_stocks_table()
    df_ref_zavod, df_ref_region = load_reference_tables()

    if df_raw.empty:
        st.info("⚠️ Нет данных")
        return

    df_raw.columns = [str(col).strip() for col in df_raw.columns]
    status_col = find_col_in_df(df_raw, ['статус', 'status'])
    name_col = find_col_in_df(df_raw, ['назв', 'name'])
    type_col = find_col_in_df(df_raw, ['тип', 'type'])
    base_price_col = find_col_in_df(df_raw, ['баз', 'price', 'цена'])
    mod_col = find_col_in_df(df_raw, ['модифик', 'modifier'])

    if not status_col:
        st.error("❌ Нет колонки статус")
        return

    # График + Навигация
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        current_gold = st.session_state.gold_history[-1]['close']
        prev_gold = st.session_state.gold_history[-2]['close']
        gold_change = current_gold - prev_gold
        gold_color = "#0ecb81" if gold_change >= 0 else "#f6465d"
        
        st.markdown(f"""
            <div class='gold-widget'>
                <h3 style='color:#f0b90b; margin:0 0 12px 0; font-size:20px; font-weight:800;'>🪙 КУРС ЗОЛОТА</h3>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='font-size:40px; font-weight:900; color:#f0b90b;'>{current_gold:.2f}$</div>
                    <div style='font-size:22px; font-weight:800; color:{gold_color};'>{'+'if gold_change>=0 else''}{gold_change:.2f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        hist_df = pd.DataFrame(st.session_state.gold_history)
        fig = go.Figure(data=[go.Candlestick(
            open=hist_df['open'], high=hist_df['high'], low=hist_df['low'], close=hist_df['close'],
            increasing_line_color='#0ecb81', decreasing_line_color='#f6465d'
        )])
        fig.update_layout(height=320, margin=dict(l=0,r=0,t=0,b=0), xaxis_rangeslider_visible=False,
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(26,29,32,0.6)',
                         xaxis=dict(showgrid=False, showticklabels=False),
                         yaxis=dict(showgrid=True, gridcolor='rgba(240,185,11,0.15)'))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_right:
        st.markdown("#### 🎯 НАВИГАЦИЯ")
        if st.button("📊 ВСЕ АКЦИИ", use_container_width=True):
            st.session_state.view_mode = "all"
            st.rerun()
        if st.button("🔥 ТОП-5", use_container_width=True):
            st.session_state.view_mode = "top"
            st.rerun()
        if st.button("💼 ПОРТФЕЛЬ", use_container_width=True):
            st.session_state.view_mode = "portfolio"
            st.rerun()
        if st.button("📜 ИСТОРИЯ", use_container_width=True):
            st.session_state.view_mode = "history"
            st.rerun()
        if st.button("🎲 Игра «Кости»", use_container_width=True):
            st.session_state.view_mode = "dice"
            st.rerun()

    # ИГРА В КОСТИ
    if st.session_state.view_mode == "dice":
        st.markdown("""
            <div class='dice-container'>
                <h1 style='text-align:center; color:#f0b90b; margin-bottom:10px;'>🎲 СИМУЛЯТОР РИСКА «КОСТИ» 🎲</h1>
                <p style='text-align:center; color:#9aa0a6; font-size:14px; margin-bottom:30px;'>
                    📊 Финансовый тренажер управления рисками • Только виртуальная валюта
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Баланс
        st.markdown(f"""
            <div class='balance-display'>
                <div style='font-size:16px; color:#9aa0a6; margin-bottom:8px;'>💰 ВАШ БАЛАНС</div>
                <div class='balance-amount'>${st.session_state.user_balance:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Игра
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 💵 Размер ставки")
            bet_amount = st.slider("Сумма:", 10, min(st.session_state.user_balance, 5000), 100, 10)
            
            st.markdown("### 🎯 Условие победы")
            st.markdown("<div style='font-size:13px; color:#9aa0a6; margin-bottom:10px;'>Выберите: сумма костей больше чем...</div>", unsafe_allow_html=True)
            
            target = st.selectbox(
                "Число:",
                options=list(DICE_ODDS.keys()),
                format_func=lambda x: f"> {x}  |  Вероятность: {DICE_ODDS[x]['prob']}%  |  Коэффициент: ×{DICE_ODDS[x]['coef']}"
            )
            
            st.markdown(f"""
                <div style='background:rgba(240,185,11,0.1); border:2px solid #f0b90b; border-radius:12px; padding:16px; margin-top:16px;'>
                    <div style='color:#f0b90b; font-weight:700; margin-bottom:8px;'>📊 УСЛОВИЯ:</div>
                    <div style='color:#fff;'>• Вероятность победы: <span style='color:#0ecb81; font-weight:700;'>{DICE_ODDS[target]['prob']}%</span></div>
                    <div style='color:#fff;'>• Коэффициент выплаты: <span style='color:#f0b90b; font-weight:700;'>×{DICE_ODDS[target]['coef']}</span></div>
                    <div style='color:#fff;'>• Возможный выигрыш: <span style='color:#0ecb81; font-weight:700;'>${int(bet_amount * DICE_ODDS[target]['coef']):,}</span></div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 🎲 Результат броска")
            
            # Отображение результата
            if st.session_state.dice_result:
                won, total, dice1, dice2, winnings = st.session_state.dice_result
                
                # Анимация костей
                st.markdown(f"""
                    <div style='text-align:center; margin:30px 0;'>
                        <div class='dice'>{dice1}</div>
                        <div class='dice'>{dice2}</div>
                        <div style='font-size:32px; font-weight:900; color:#f0b90b; margin-top:20px;'>
                            СУММА: {total}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if won:
                    st.markdown(f"""
                        <div class='dice-result-win'>
                            <h2 style='text-align:center; color:#0ecb81; margin:0;'>🎉 ПОБЕДА! 🎉</h2>
                            <div style='text-align:center; font-size:36px; font-weight:900; color:#0ecb81; margin:20px 0;'>
                                +${winnings:,}
                            </div>
                            <div style='text-align:center; color:#fff; font-size:16px;'>
                                Сумма {total} > {target} ✓
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    play_sound("win")
                else:
                    st.markdown(f"""
                        <div class='dice-result-lose'>
                            <h2 style='text-align:center; color:#f6465d; margin:0;'>😢 ПРОИГРЫШ</h2>
                            <div style='text-align:center; font-size:36px; font-weight:900; color:#f6465d; margin:20px 0;'>
                                -${bet_amount:,}
                            </div>
                            <div style='text-align:center; color:#fff; font-size:16px;'>
                                Сумма {total} ≤ {target} ✗
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    play_sound("lose")
            else:
                st.markdown("""
                    <div style='text-align:center; padding:60px 20px; background:rgba(26,29,32,0.5); border-radius:12px; border:2px dashed #2b2f33;'>
                        <div style='font-size:60px; margin-bottom:16px;'>🎲</div>
                        <div style='color:#9aa0a6; font-size:16px;'>Нажмите "БРОСИТЬ КОСТИ"<br/>чтобы начать игру</div>
                    </div>
                """, unsafe_allow_html=True)
        
        # Кнопки управления
        st.markdown("<hr style='margin:30px 0;'>", unsafe_allow_html=True)
        
        col_a, col_b, col_c = st.columns([1, 1, 1])
        
        with col_a:
            if st.button("🎲 БРОСИТЬ КОСТИ", use_container_width=True, type="primary"):
                if st.session_state.user_balance >= bet_amount:
                    # Играем
                    result = play_dice_game(bet_amount, target)
                    won, total, dice1, dice2, winnings = result
                    
                    # Обновляем баланс
                    if won:
                        st.session_state.user_balance += winnings - bet_amount
                    else:
                        st.session_state.user_balance -= bet_amount
                    
                    st.session_state.dice_result = result
                    st.rerun()
                else:
                    st.error("❌ Недостаточно средств!")
        
        with col_b:
            if st.button("🔄 НОВАЯ ИГРА", use_container_width=True):
                st.session_state.dice_result = None
                st.rerun()
        
        with col_c:
            if st.button("💰 ПОПОЛНИТЬ (+$1000)", use_container_width=True):
                st.session_state.user_balance += 1000
                st.success("✅ Баланс пополнен!")
                st.rerun()
        
        # Таблица вероятностей
        st.markdown("<hr style='margin:30px 0;'>", unsafe_allow_html=True)
        st.markdown("### 📊 Таблица вероятностей и коэффициентов")
        
        odds_data = []
        for num, data in DICE_ODDS.items():
            odds_data.append({
                "Условие": f"> {num}",
                "Вероятность": f"{data['prob']}%",
                "Коэффициент": f"×{data['coef']}"
            })
        
        st.dataframe(pd.DataFrame(odds_data), use_container_width=True, hide_index=True)
        
        return

    # Обработка акций (остальной код без изменений)
    try:
        open_stocks = df_raw[df_raw[status_col].astype(str).str.upper().str.contains('ОТКР', regex=False)].copy()
    except:
        st.error("❌ Ошибка фильтрации")
        return

    gold_imp = (gold_change / prev_gold * 100) if prev_gold else 0

    processed = []
    for i, row in open_stocks.iterrows():
        name = safe_row_get(row, [name_col], f'#{i}')
        typ = safe_row_get(row, [type_col], '')
        base_price = safe_float(safe_row_get(row, [base_price_col], 0))
        raw_mod = safe_row_get(row, [mod_col], '')
        is_zavod = "завод" in str(typ).lower()

        parts = []
        if not df_ref_region.empty:
            parts.append(df_ref_region)
        if not df_ref_zavod.empty:
            parts.append(df_ref_zavod)
        ref_table = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

        mod_sum, _, _ = sum_modifiers_and_list(raw_mod, ref_table)
        total_pct = round(mod_sum + (0.0 if is_zavod else gold_imp), 2)
        final_price = max(0, int(round(base_price * (1.0 + total_pct / 100.0))))

        if final_price > 0:
            processed.append({
                "Название": name,
                "Тип": typ,
                "Базовая цена": base_price,
                "pct": total_pct,
                "final_price": final_price
            })

    # История
    if st.session_state.view_mode == "history":
        st.markdown("## 📜 ИСТОРИЯ СДЕЛОК")
        if not st.session_state.user:
            st.warning("⚠️ Войдите в профиль")
            return
        purchases = load_purchases()
        if purchases.empty:
            st.info("История пуста")
            return
        st.dataframe(purchases.tail(50), use_container_width=True)
        return

    # Портфель
    if st.session_state.view_mode == "portfolio":
        if not st.session_state.user:
            st.warning("⚠️ Войдите в профиль")
            return
        
        purchases = load_purchases()
        if purchases.empty:
            st.info("💼 Портфель пуст")
            return
        
        st.markdown("<div class='portfolio-header'><h2 style='color:#f0b90b; margin:0;'>💼 ПОРТФЕЛЬ</h2></div>", unsafe_allow_html=True)
        st.dataframe(purchases, use_container_width=True)
        return

    # Топ-5
    if st.session_state.view_mode == "top":
        processed = sorted(processed, key=lambda x: x['pct'], reverse=True)[:5]
        st.markdown("## 🔥 ТОП-5 ПО РОСТУ")

    # Отображение акций
    cols = st.columns(3)
    for idx, item in enumerate(processed):
        with cols[idx % 3]:
            pct = item['pct']
            color_cls = "pos" if pct >= 0 else "neg"
            
            st.markdown(f"""
                <div class="stock-card">
                    <div>
                        <div class="stock-name">{item['Название']}</div>
                        <div class="stock-type">{item['Тип']}</div>
                    </div>
                    <div style='margin-top:20px;'>
                        <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
                            <div>
                                <div style='color:#666; font-size:14px; text-decoration:line-through;'>{item['Базовая цена']:.0f}$</div>
                                <div class="current-price">{item['final_price']}$</div>
                            </div>
                            <div class="change-pct {color_cls}">{'+'if pct>0 else''}{pct:.2f}%</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🛒 КУПИТЬ", key=f"buy_{idx}", use_container_width=True):
                if not st.session_state.user:
                    st.error("⚠️ Войдите!")
                else:
                    st.session_state.purchase_dialog = {'stock_name': item['Название'], 'price': item['final_price']}
                    st.rerun()

    # Диалог покупки
    if st.session_state.purchase_dialog:
        d = st.session_state.purchase_dialog
        st.markdown(f"""
            <div class='purchase-dialog'>
                <h2 style='color:#f0b90b; text-align:center;'>💰 ПОКУПКА: {d['stock_name']}</h2>
                <div style='text-align:center; font-size:28px; margin:20px 0; color:#fff;'>
                    Цена: <span style='color:#f0b90b; font-weight:900;'>${d['price']:,.0f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        qty = st.slider("Количество акций:", 1, 100, 1)
        total = qty * d['price']
        st.markdown(f"<div class='total-price'>💎 ИТОГО: ${total:,.0f}</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ КУПИТЬ", use_container_width=True):
                ws = get_buy_worksheet()
                if ws:
                    try:
                        for _ in range(qty):
                            ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                         st.session_state.user, d['stock_name'], d['price'],
                                         "TX-"+str(random.randint(100000, 999999))])
                        # Списываем с баланса
                        st.session_state.user_balance -= total
                        st.success("✅ Покупка завершена!")
                        st.session_state.purchase_dialog = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
        with c2:
            if st.button("❌ ОТМЕНА", use_container_width=True):
                st.session_state.purchase_dialog = None
                st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("# 👤 ПРОФИЛЬ")
    if not st.session_state.user:
        u = st.selectbox("Пользователь:", ["артем", "богдан", "руслан", "разработчик"])
        if st.button("🚀 ВОЙТИ", use_container_width=True):
            st.session_state.user = u
            st.rerun()
    else:
        st.markdown(f"### {st.session_state.user.upper()} 👋")
        st.markdown(f"""
            <div style='background:rgba(240,185,11,0.15); padding:16px; border-radius:12px; border:2px solid #f0b90b; margin:16px 0;'>
                <div style='font-size:14px; color:#9aa0a6; margin-bottom:8px;'>💰 БАЛАНС</div>
                <div style='font-size:28px; font-weight:900; color:#f0b90b;'>${st.session_state.user_balance:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 ВЫЙТИ", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    ### ℹ️ О СИСТЕМЕ
    
    **ВАНИНА ИГРА** - комплексный финансовый тренажер
    
    📊 **Возможности:**
    - Торговля акциями
    - Симулятор риска (кости)
    - Реалтайм обновления
    - Виртуальный баланс
    
    ⚠️ **Внимание:**  
    Используется только виртуальная валюта для образовательных целей
    """)

market_display()
