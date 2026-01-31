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

st.set_page_config(page_title="Ванина игра", layout="wide")

# -----------------------
# CSS - Полный красивый дизайн + Анимации
# -----------------------
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    .stApp { background-color: #0b0e11; color: #FFFFFF; }

    /* Анимации */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(246, 70, 93, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(246, 70, 93, 0); }
        100% { box-shadow: 0 0 0 0 rgba(246, 70, 93, 0); }
    }

    div.stButton > button {
        background: linear-gradient(135deg, #1a1d20 0%, #000000 100%) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #2b2b2b !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    div.stButton > button:hover {
        border-color: #f0b90b !important;
        box-shadow: 0 0 20px rgba(240,185,11,0.3) !important;
        transform: translateY(-2px) !important;
    }

    .stock-card { 
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
        border-radius: 16px; 
        padding: 20px; 
        border: 1px solid #2b2f33; 
        margin-bottom: 16px; 
        min-height: 200px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        animation: fadeIn 0.5s ease-out;
    }
    
    .stock-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #f0b90b, #0ecb81);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .stock-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(240,185,11,0.2);
        border-color: #f0b90b;
    }
    
    .stock-card:hover::before {
        opacity: 1;
    }
    
    .stock-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
    .stock-name { color: #FFFFFF; font-size: 22px; font-weight: 700; margin-bottom: 4px; line-height: 1.2; }
    .stock-type { 
        color: #9aa0a6; 
        font-size: 13px; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        background: rgba(154,160,166,0.1);
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 4px;
    }
    .old-price { color: #9aa0a6; font-size: 14px; text-decoration: line-through; }
    .current-price { color: #f0b90b; font-size: 32px; font-weight: 800; line-height: 1; text-shadow: 0 0 10px rgba(240,185,11,0.3); }
    .change-pct { font-size: 24px; font-weight: 800; }
    .pos { color: #0ecb81; } 
    .neg { color: #f6465d; }
    
    .portfolio-header { 
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 20px; 
        border: 2px solid #f0b90b;
        box-shadow: 0 4px 20px rgba(240,185,11,0.2);
        animation: fadeIn 0.5s ease;
    }
    .portfolio-stat { text-align: center; padding: 16px; }
    .stat-label { 
        color: #9aa0a6; 
        font-size: 13px; 
        text-transform: uppercase; 
        letter-spacing: 0.5px; 
        margin-bottom: 8px;
        font-weight: 600;
    }
    .stat-value { 
        color: #FFFFFF; 
        font-size: 28px; 
        font-weight: 800;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .position-item { 
        background: linear-gradient(135deg, #1a1d20 0%, #161719 100%); 
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 12px; 
        border: 1px solid #2b2f33;
        transition: all 0.3s ease;
        animation: fadeIn 0.5s ease;
    }
    .position-item:hover {
        border-color: #f0b90b;
        transform: translateX(4px);
    }
    .position-title { color: #f0b90b; font-size: 20px; font-weight: 700; }
    .small-muted { color: #888; font-size: 13px; }
    
    /* Диалоги */
    .purchase-dialog { 
        background: linear-gradient(180deg, #1a1d20, #0e1113); 
        border: 2px solid #0ecb81; 
        border-radius: 12px; 
        padding: 20px; 
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(14,203,129,0.2);
        animation: fadeIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .sell-dialog { 
        background: linear-gradient(180deg, #2b1a1f, #1a0e11); 
        border: 2px solid #f6465d; 
        border-radius: 12px; 
        padding: 20px; 
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(246, 70, 93, 0.3);
        animation: fadeIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), pulse-red 2s infinite;
    }
    
    .total-price { 
        color: #0ecb81; 
        font-size: 24px; 
        font-weight: 800; 
        text-align: center; 
        padding: 15px; 
        background: rgba(14,203,129,0.1); 
        border-radius: 8px; 
        margin: 10px 0;
        border: 1px solid rgba(14,203,129,0.3);
    }
    
    .total-sell-price { 
        color: #f6465d; 
        font-size: 24px; 
        font-weight: 800; 
        text-align: center; 
        padding: 15px; 
        background: rgba(246, 70, 93, 0.1); 
        border-radius: 8px; 
        margin: 10px 0;
        border: 1px solid rgba(246, 70, 93, 0.3);
    }
    
    .news-banner {
        background: linear-gradient(135deg, #1a1d20 0%, #2b1a1f 100%);
        border-left: 4px solid #f0b90b;
        padding: 16px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        animation: fadeIn 1s ease;
    }
    
    .gold-widget {
        background: linear-gradient(135deg, #2a1f1a 0%, #1a1d20 100%);
        border: 2px solid #f0b90b;
        border-radius: 12px; 
        padding: 16px;
        margin-bottom: 16px;
        transition: transform 0.3s;
    }
    .gold-widget:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# Helpers
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

@st.cache_data(ttl=30)
def load_stocks_table():
    client = get_gspread_client()
    try:
        return pd.DataFrame(
            client.open("«Акции»").worksheet("Лист1").get_all_records()
        )
    except Exception as e:
        st.error(f"❌ Ошибка загрузки акций: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_reference_tables():
    client = get_gspread_client()
    try:
        df_zavod = pd.DataFrame(client.open("«Таблица дификаторы_заводские_проценты»").sheet1.get_all_records())
    except Exception:
        df_zavod = pd.DataFrame(columns=["Значение", "%"])
    try:
        df_region = pd.DataFrame(client.open("Таблица «Модификаторы_региональные_проценты»").sheet1.get_all_records())
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
    # Эта функция для удаления делистинговых акций (цена 0)
    try:
        ws = get_buy_worksheet()
        if ws is None: return False
        all_values = ws.get_all_values()
        if not all_values or len(all_values) < 2: return False
        header = all_values[0]
        name_col_idx = next((idx for idx, h in enumerate(header) if h and any(k in h.lower() for k in ["name", "назв", "акция"])), 2 if len(header) > 2 else None)
        if name_col_idx is not None:
            to_delete = [i for i, row in enumerate(all_values[1:], start=2) if len(row) > name_col_idx and str(row[name_col_idx]).strip() == str(stock_name).strip()]
            for r in sorted(to_delete, reverse=True):
                try: ws.delete_row(r)
                except Exception: pass
            load_purchases.clear()
            return bool(to_delete)
    except Exception: return False
    return False

def sell_shares_logic(user, stock_name, quantity_to_sell):
    """
    Удаляет точное количество строк из таблицы покупок, 
    соответствующих пользователю и названию акции.
    """
    try:
        ws = get_buy_worksheet()
        if ws is None:
            return False, "Ошибка подключения к таблице"
        
        # Получаем все данные сырыми, чтобы знать индексы строк
        all_values = ws.get_all_values()
        if not all_values:
            return False, "Таблица пуста"
            
        header = all_values[0]
        # Ищем индексы колонок
        user_col_idx = -1
        name_col_idx = -1
        
        for idx, h in enumerate(header):
            lc = str(h).lower()
            if "who" in lc or "кто" in lc or "user" in lc:
                user_col_idx = idx
            if "name" in lc or "назв" in lc or "акция" in lc:
                name_col_idx = idx
        
        if user_col_idx == -1: user_col_idx = 1 # Дефолт
        if name_col_idx == -1: name_col_idx = 2 # Дефолт
        
        # Собираем индексы строк для удаления (1-based index для gspread)
        rows_to_delete = []
        for i, row in enumerate(all_values):
            if i == 0: continue # Пропуск заголовка
            
            # Безопасное получение значений
            r_user = str(row[user_col_idx]) if len(row) > user_col_idx else ""
            r_name = str(row[name_col_idx]) if len(row) > name_col_idx else ""
            
            if r_user == str(user) and r_name == str(stock_name):
                # i - это индекс в списке (0-based), в gspread строки с 1. 
                # all_values включает хедер, так что row 1 в коде = row 2 в листе?
                # all_values[0] это строка 1. all_values[1] это строка 2.
                rows_to_delete.append(i + 1)
        
        if len(rows_to_delete) < quantity_to_sell:
            return False, f"Ошибка: Найдено только {len(rows_to_delete)} акций, а вы пытаетесь продать {quantity_to_sell}"
            
        # Удаляем с конца, чтобы не сдвигать индексы удаляемых строк в начале
        # Берем последние quantity_to_sell записей (LIFO)
        target_rows = sorted(rows_to_delete, reverse=True)[:quantity_to_sell]
        
        for r_idx in target_rows:
            ws.delete_row(r_idx)
            time.sleep(0.1) # Небольшая пауза для стабильности API
            
        load_purchases.clear()
        return True, f"Продано {quantity_to_sell} шт."
        
    except Exception as e:
        return False, str(e)

# -----------------------
# Strict modifier matching
# -----------------------
def sum_modifiers_and_list(raw_text, ref_df):
    if ref_df is None or ref_df.empty: return 0.0, [], []
    def normalize(s): return re.sub(r'\W+', '', str(s).lower())
    ref_map = {}
    for _, r in ref_df.iterrows():
        typ, val, pct = None, None, 0.0
        for col in r.index:
            if col is None: continue
            lc = str(col).lower()
            if "тип" in lc or lc == "type": typ = r.get(col)
            if "знач" in lc or "value" in lc: val = r.get(col)
            if "%" in str(col).lower() or "percent" in lc or "pct" in lc: pct = safe_float(r.get(col, 0))
        typ_str = str(typ).strip() if typ is not None else ""
        val_str = str(val).strip() if val is not None else ""
        display = f"{typ_str} {val_str}" if typ_str and val_str else (val_str or typ_str)
        keys = set()
        if val_str: keys.add(normalize(val_str))
        if typ_str: keys.add(normalize(typ_str))
        if typ_str and val_str: keys.add(normalize(f"{typ_str} {val_str}"))
        if re.fullmatch(r'-?\d+(\.\d+)?', val_str): keys.add(re.sub(r'\W+', '', val_str))
        for k in keys:
            if k not in ref_map: ref_map[k] = (display, safe_float(pct))

    tokens = split_modifiers(raw_text)
    matched_keys, matched_displays = set(), set()
    found = []
    for tok in tokens:
        if not tok: continue
        tok_norm = normalize(tok)
        if tok_norm in ref_map and tok_norm not in matched_keys:
            disp, p = ref_map[tok_norm]
            disp_norm = normalize(disp)
            if disp_norm not in matched_displays:
                matched_keys.add(tok_norm); matched_displays.add(disp_norm); found.append((disp, p))
            else: matched_keys.add(tok_norm)
            continue
        if re.fullmatch(r'\d{1,6}', tok.strip()):
            num = re.sub(r'\W+', '', tok.strip())
            if num in ref_map and num not in matched_keys:
                disp, p = ref_map[num]
                disp_norm = normalize(disp)
                if disp_norm not in matched_displays:
                    matched_keys.add(num); matched_displays.add(disp_norm); found.append((disp, p))
                else: matched_keys.add(num)
                continue
            for key, (disp, pct) in ref_map.items():
                if key in matched_keys: continue
                if re.search(r'\b' + re.escape(num) + r'\b', disp):
                    disp_norm = normalize(disp)
                    if disp_norm not in matched_displays:
                        matched_keys.add(key); matched_displays.add(disp_norm); found.append((disp, pct))
                    else: matched_keys.add(key)
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
st.session_state.setdefault('sell_dialog', None) # NEW: Состояние для диалога продажи

# -----------------------
# Main fragment
# -----------------------
@st.fragment(run_every=30)
def market_display():
    st.markdown("<h1 style='color:#f0b90b; margin-bottom:6px; text-shadow: 0 0 20px rgba(240,185,11,0.5);'>💎 Ванина игра</h1>", unsafe_allow_html=True)

    # -----------------------
    # Новости
    # -----------------------
    news_list = [
        "Рост рынка золота удивляет экспертов.", "Открылся новый завод, возможно это принесет прибавку к заводским акциям.",
        "Акции компаний резко упали.", "Инвесторы прогнозируют рост цен.", "Экономика рынка стабилизируется.",
        "Новые законы могут повлиять на рынок.", "Поступили данные о прибыли компаний.", "Региональные акции пользуются спросом.",
        "Инновационный проект привлёк инвестиции.", "Аналитики повышают прогноз по золоту.", "Волатильность на рынке выше нормы.",
        "Слияние компаний одобрено.", "Цены на ресурсы растут.", "Эксперты советуют держать региональные акции."
    ]
    random_news = random.choice(news_list)
    st.markdown(f"<div class='news-banner'><h3 style='color:#ccccff; margin:0;'>📰 Актуальные Новости: {random_news}</h3></div>", unsafe_allow_html=True)

    # -----------------------
    # Кнопка обновить
    # -----------------------
    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("🔄 Обновить"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()

    # -----------------------
    # Обновление свечи золота
    # -----------------------
    last_close = st.session_state.gold_history[-1]['close']
    o = last_close
    c = o + random.uniform(-15, 15)
    h = max(o, c) + random.uniform(0, 7)
    l = min(o, c) - random.uniform(0, 7)
    st.session_state.gold_history.append({'open': o, 'high': h, 'low': l, 'close': c})
    if len(st.session_state.gold_history) > 60:
        st.session_state.gold_history.pop(0)

    # -----------------------
    # Загрузка данных
    # -----------------------
    df_raw = load_stocks_table()
    df_ref_zavod, df_ref_region = load_reference_tables()

    if df_raw is None or df_raw.empty:
        st.info("Нет данных таблицы «Акции».")
        return

    df_raw.columns = [str(col).strip() for col in df_raw.columns]
    status_col = find_col_in_df(df_raw, ['статус', 'status'])
    name_col = find_col_in_df(df_raw, ['назв', 'name'])
    type_col = find_col_in_df(df_raw, ['тип', 'type'])
    base_price_col = find_col_in_df(df_raw, ['баз', 'price', 'цена', 'cost'])
    mod_col = find_col_in_df(df_raw, ['модифик', 'modifier'])

    if status_col is None:
        st.error("В таблице «Акции» не найдена колонка со статусом.")
        return

    # -----------------------
    # График золота
    # -----------------------
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
                <h3 style='color:#f0b90b; margin:0 0 8px 0;'>🪙 Курс Золота</h3>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='font-size:32px; font-weight:800; color:#f0b90b;'>{current_gold:.2f}$</div>
                    <div style='font-size:20px; font-weight:700; color:{gold_color};'>{gold_sign}{gold_change:.2f} ({gold_sign}{gold_change_pct:.2f}%)</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        hist_df = pd.DataFrame(st.session_state.gold_history)
        fig = go.Figure(data=[go.Candlestick(
            open=hist_df['open'], high=hist_df['high'], low=hist_df['low'], close=hist_df['close'],
            increasing_line_color='#0ecb81', decreasing_line_color='#f6465d',
            increasing_fillcolor='rgba(14,203,129,0.3)', decreasing_fillcolor='rgba(246,70,93,0.3)'
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=8, b=0), xaxis_rangeslider_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(26,29,32,0.5)',
                          xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_right:
        st.markdown("#### 🎯 Навигация")
        if st.button("📊 Все акции", use_container_width=True):
            st.session_state.view_mode = "all"; st.rerun()
        if st.button("🔥 Топ роста", use_container_width=True):
            st.session_state.view_mode = "top"; st.rerun()
        if st.button("💼 Портфель", use_container_width=True):
            st.session_state.view_mode = "portfolio"; st.rerun()
        st.markdown("<div class='small-muted' style='margin-top:12px; text-align:center;'>⏱️ Автообновление каждые 30 секунд</div>", unsafe_allow_html=True)

    # -----------------------
    # Обработка акций
    # -----------------------
    try:
        status_series = df_raw[status_col].astype(str).str.upper()
        open_mask = status_series.str.contains('ОТКР', regex=False)
        open_stocks = df_raw[open_mask].copy()
    except Exception: return

    gold_imp = (gold_change_pct if gold_change_pct else 0.0)
    processed = []
    removed_stock_names = set()
    st.session_state['last_found_map'] = {}
    st.session_state['last_tokens_map'] = {}
    st.session_state['last_raw_map'] = {}

    for i, row in open_stocks.iterrows():
        name = safe_row_get(row, [name_col] if name_col else [], default=f'#{i}')
        if not name: name = f'#{i}'
        typ = safe_row_get(row, [type_col] if type_col else [], default='')
        base_price = safe_float(safe_row_get(row, [base_price_col] if base_price_col else [], default=0))
        raw_mod = safe_row_get(row, [mod_col] if mod_col else [], default='')
        is_zavod = "завод" in str(typ).lower()

        parts = []
        if df_ref_region is not None and not df_ref_region.empty: parts.append(df_ref_region.copy())
        if df_ref_zavod is not None and not df_ref_zavod.empty: parts.append(df_ref_zavod.copy())

        if parts:
            ref_table = pd.concat(parts, ignore_index=True, sort=False)
            colmap = {c.lower(): c for c in ref_table.columns}
            typ_col_ref = next((col for key, col in colmap.items() if 'тип' in key or 'type' in key), None)
            val_col_ref = next((col for key, col in colmap.items() if 'знач' in key or 'value' in key), None)
            pct_col_ref = next((col for key, col in colmap.items() if '%' in key or 'percent' in key or 'pct' in key), None)
            if typ_col_ref and val_col_ref:
                cols_keep = [typ_col_ref, val_col_ref] + ([pct_col_ref] if pct_col_ref else [])
                ref_table = ref_table[cols_keep].copy()
                ref_table.columns = ['Тип', 'Значение'] + (['%'] if pct_col_ref else [])
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
            try: remove_stock_from_purchases_sheet(name)
            except Exception: pass
            continue
        processed.append({"Название": name, "Тип": typ, "Базовая цена": base_price, "pct": total_pct, "final_price": final_price})

    # -----------------------
    # Portfolio view (Здесь кнопка продажи!)
    # -----------------------
    if st.session_state.view_mode == "portfolio":
        if not st.session_state.user:
            st.warning("⚠️ Войдите в профиль, чтобы просмотреть портфель.")
            return
        purchases = load_purchases()
        if purchases is None or purchases.empty:
            st.info("💼 Портфель пуст. Начните инвестировать!")
            return
        
        # Определение колонок (так же как раньше)
        header_cols = list(purchases.columns)
        col_who = next((c for c in header_cols if any(k in c.lower() for k in ["who", "кто", "user"])), header_cols[1] if len(header_cols) >= 2 else None)
        col_name = next((c for c in header_cols if any(k in c.lower() for k in ["name", "назв", "акция"])), header_cols[2] if len(header_cols) >= 3 else None)
        col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), header_cols[3] if len(header_cols) >= 4 else None)

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
        
        # Шапка портфеля
        total_invested = grouped['total_spent'].sum()
        total_current = grouped['current_value'].sum()
        total_pnl = total_current - total_invested
        
        st.markdown(f"<div class='portfolio-header'><h2 style='color:#f0b90b; margin:0;'>💼 Портфель — {st.session_state.user}</h2></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='portfolio-stat'><div class='stat-label'>💰 Инвестировано</div><div class='stat-value'>${total_invested:,.0f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='portfolio-stat'><div class='stat-label'>📈 Сейчас стоит</div><div class='stat-value'>${total_current:,.0f}</div></div>", unsafe_allow_html=True)
        pnl_color = "#0ecb81" if total_pnl >= 0 else "#f6465d"
        pnl_sign = "+" if total_pnl >= 0 else ""
        c3.markdown(f"<div class='portfolio-stat'><div class='stat-label'>💎 Прибыль/Убыток</div><div class='stat-value' style='color:{pnl_color}'>{pnl_sign}${total_pnl:,.0f}</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='portfolio-stat'><div class='stat-label'>📊 Позиций</div><div class='stat-value'>{len(grouped)}</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        for i, pos in grouped.sort_values(by='current_value', ascending=False).iterrows():
            pnl_sign = "+" if pos['pnl'] >= 0 else ""
            pnl_color = "#0ecb81" if pos['pnl'] >= 0 else "#f6465d"
            
            with st.container():
                st.markdown(f"""
                <div class='position-item'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:12px;'>
                        <div class='position-title'>{pos['name']}</div>
                        <div style='background:rgba(240,185,11,0.2); padding:6px 14px; border-radius:20px; color:#f0b90b; font-weight:700;'>×{int(pos['quantity'])}</div>
                    </div>
                    <div style='display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-top:12px;'>
                        <div><div class='small-muted'>Цена покупки</div><div style='font-size:18px; font-weight:700;'>${pos['avg_price']:,.0f}</div></div>
                        <div><div class='small-muted'>Сейчас</div><div style='font-size:18px; font-weight:700; color:#f0b90b;'>${pos['current_price']:,.0f}</div></div>
                        <div><div class='small-muted'>Стоимость</div><div style='font-size:18px; font-weight:700;'>${pos['current_value']:,.0f}</div></div>
                        <div><div class='small-muted'>P/L</div><div style='font-size:20px; font-weight:800; color:{pnl_color};'>{pnl_sign}${abs(pos['pnl']):,.0f}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # Кнопка продажи
                if st.button(f"🔴 ПРОДАТЬ {pos['name']}", key=f"sell_btn_{i}", use_container_width=True):
                    st.session_state.sell_dialog = {
                        'stock_name': pos['name'],
                        'max_qty': int(pos['quantity']),
                        'price': pos['current_price']
                    }
                    st.rerun()
        return

    # -----------------------
    # Top view
    # -----------------------
    if st.session_state.view_mode == "top":
        processed = sorted(processed, key=lambda x: x['pct'], reverse=True)[:9]

    # -----------------------
    # Display stocks (Grid)
    # -----------------------
    cols = st.columns(3)
    for idx, item in enumerate(processed):
        with cols[idx % 3]:
            pct = item['pct']
            sign = '+' if pct > 0 else ''
            color_cls = "pos" if pct >= 0 else "neg"
            st.markdown(f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div><div class="stock-name">{item['Название']}</div><div class="stock-type">{item['Тип']}</div></div>
                    </div>
                    <div style='margin-top:auto;'>
                        <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
                            <div><div class="old-price">{item['Базовая цена']:.0f}$</div><div class="current-price">{item['final_price']}$</div></div>
                            <div class="change-pct {color_cls}">{sign}{pct:.2f}%</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            _, btn_col2, _ = st.columns([1, 2, 1])
            with btn_col2:
                if st.button("🛒 КУПИТЬ", key=f"buy_{item['Название']}_{idx}", use_container_width=True):
                    if not st.session_state.user: st.error("⚠️ Войдите в профиль!")
                    else:
                        st.session_state.purchase_dialog = {'stock_name': item['Название'], 'price': item['final_price'], 'idx': idx}
                        st.rerun()

    # -----------------------
    # Purchase dialog
    # -----------------------
    if st.session_state.purchase_dialog:
        dialog_data = st.session_state.purchase_dialog
        st.markdown("<div class='purchase-dialog'>", unsafe_allow_html=True)
        st.markdown(f"## 💰 Покупка: **{dialog_data['stock_name']}**")
        st.markdown(f"### Цена за акцию: **${dialog_data['price']:,.0f}**")
        quantity = st.slider("Количество акций:", 1, 100, 1, key="buy_slider")
        total_price = quantity * dialog_data['price']
        st.markdown(f"<div class='total-price'>💎 ИТОГО: ${total_price:,.0f}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ ПОДТВЕРДИТЕ ПОКУПКУ", use_container_width=True):
                ws = get_buy_worksheet()
                if ws:
                    try:
                        rows = []
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for _ in range(quantity):
                            rows.append([now, st.session_state.user, dialog_data['stock_name'], dialog_data['price'], "TX-"+ "".join(random.choices(string.digits, k=6))])
                        ws.append_rows(rows)
                        load_purchases.clear()
                        st.toast(f"✅ Успешно! Куплено {quantity} акций!", icon="🛍️")
                        st.session_state.purchase_dialog = None
                        st.rerun()
                    except Exception as e: st.error(f"❌ Ошибка: {e}")
                else: st.error("❌ Ошибка таблицы")
        with col2:
            if st.button("❌ ОТМЕНА", key="buy_cancel", use_container_width=True):
                st.session_state.purchase_dialog = None; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------
    # Sell dialog (NEW)
    # -----------------------
    if st.session_state.sell_dialog:
        d_data = st.session_state.sell_dialog
        st.markdown("<div class='sell-dialog'>", unsafe_allow_html=True)
        st.markdown(f"## 📉 Продажа: **{d_data['stock_name']}**")
        st.markdown(f"### Текущая цена: **${d_data['price']:,.0f}**")
        
        # Слайдер выбора количества
        qty_to_sell = st.slider("Сколько продать?", 1, d_data['max_qty'], 1, key="sell_slider")
        
        total_rec = qty_to_sell * d_data['price']
        st.markdown(f"<div class='total-sell-price'>🔥 ВЫ ПОЛУЧИТЕ: ${total_rec:,.0f}</div>", unsafe_allow_html=True)
        
        sc1, sc2 = st.columns(2)
        with sc1:
            if st.button("✅ ПРОДАТЬ АКЦИИ", type="primary", use_container_width=True):
                success, msg = sell_shares_logic(st.session_state.user, d_data['stock_name'], qty_to_sell)
                if success:
                    st.toast(msg, icon="💸")
                    st.session_state.sell_dialog = None
                    st.rerun()
                else:
                    st.error(msg)
        with sc2:
            if st.button("❌ ОТМЕНА", key="sell_cancel", use_container_width=True):
                st.session_state.sell_dialog = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Sidebar
# -----------------------
with st.sidebar:
    st.markdown("# 👤 Профиль")
    if not st.session_state.user:
        st.markdown("### Войдите в систему")
        u = st.selectbox("Выберите пользователя:", ["артем", "богдан", "руслан", "разработчик"])
        if st.button("🔐 Войти", use_container_width=True):
            st.session_state.user = u
            st.rerun()
    else:
        st.markdown(f"### Привет, **{st.session_state.user}**! 👋")
        st.markdown("---")
        purchases = load_purchases()
        if not purchases.empty:
            try:
                # Простая статистика в сайдбаре
                header_cols = list(purchases.columns)
                col_who = next((c for c in header_cols if any(k in c.lower() for k in ["who", "кто", "user"])), header_cols[1])
                col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), header_cols[3])
                user_p = purchases[purchases[col_who] == st.session_state.user]
                total_inv = user_p[col_price].apply(safe_float).sum()
                st.markdown(f"**💰 В активах:** ${total_inv:,.0f}")
                st.markdown(f"**📊 Сделок:** {len(user_p)}")
            except: pass
        st.markdown("---")
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.user = None; st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ О Проекте")
    st.markdown("**Ванина игра** v2.0\n\nТеперь с возможностью продажи и анимированным интерфейсом!")

market_display()
