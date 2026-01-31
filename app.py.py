import streamlit as st
import gspread
import pandas as pd
import random
import string
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

st.set_page_config(page_title="Ванина игра", layout="wide", initial_sidebar_state="expanded")

# CSS - остается тем же
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    .stApp { 
        background: linear-gradient(135deg, #0a0d10 0%, #0b0e11 50%, #0d1015 100%);
        color: #FFFFFF; 
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
    }

    div.stButton > button {
        background: linear-gradient(135deg, #1a1d20 0%, #000000 100%) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 2px solid #2b2b2b !important;
        padding: 12px 20px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        font-size: 14px !important;
    }
    
    div.stButton > button:hover {
        border-color: #f0b90b !important;
        box-shadow: 0 0 20px rgba(240,185,11,0.4) !important;
        transform: translateY(-2px) !important;
    }

    .stock-card { 
        background: linear-gradient(135deg, #1a1d20 0%, #0e1113 100%); 
        border-radius: 16px; 
        padding: 24px; 
        border: 2px solid #2b2f33; 
        margin-bottom: 16px; 
        min-height: 220px;
        transition: all 0.3s ease;
        position: relative;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .stock-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.5), 0 0 30px rgba(240,185,11,0.2);
        border-color: #f0b90b;
    }
    
    .stock-name { 
        color: #FFFFFF; 
        font-size: 24px; 
        font-weight: 800; 
        margin-bottom: 6px;
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
    }
    
    .old-price { 
        color: #666; 
        font-size: 15px; 
        text-decoration: line-through;
    }
    
    .current-price { 
        color: #f0b90b; 
        font-size: 36px; 
        font-weight: 900;
        text-shadow: 0 0 10px rgba(240,185,11,0.4);
    }
    
    .change-pct { 
        font-size: 26px; 
        font-weight: 900;
    }
    
    .pos { color: #0ecb81; } 
    .neg { color: #f6465d; }
    
    @keyframes megaPulse {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(240,185,11,0.4);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 50px rgba(240,185,11,0.6);
            transform: scale(1.02);
        }
    }
    
    .highlight-100 { 
        border: 2px solid #f0b90b;
        animation: megaPulse 2s ease-in-out infinite;
    }

    .portfolio-header { 
        background: linear-gradient(135deg, rgba(240,185,11,0.15) 0%, rgba(26,29,32,0.8) 100%); 
        border-radius: 16px; 
        padding: 32px; 
        margin-bottom: 24px; 
        border: 2px solid #f0b90b;
        box-shadow: 0 8px 24px rgba(240,185,11,0.3);
    }
    
    .stat-label { 
        color: #9aa0a6; 
        font-size: 13px; 
        text-transform: uppercase; 
        font-weight: 700;
    }
    
    .stat-value { 
        color: #FFFFFF; 
        font-size: 32px; 
        font-weight: 900;
    }
    
    .position-item { 
        background: linear-gradient(135deg, #1a1d20 0%, #161719 100%); 
        border-radius: 12px; 
        padding: 24px; 
        margin-bottom: 16px; 
        border: 2px solid #2b2f33;
        transition: all 0.3s ease;
    }
    
    .position-item:hover {
        border-color: #f0b90b;
        transform: translateX(4px);
    }
    
    .news-banner {
        background: linear-gradient(135deg, rgba(240,185,11,0.08) 0%, rgba(26,29,32,0.6) 100%);
        border-left: 4px solid #f0b90b;
        border-right: 4px solid #0ecb81;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    
    .gold-widget {
        background: linear-gradient(135deg, rgba(240,185,11,0.15) 0%, rgba(26,29,32,0.8) 100%);
        border: 2px solid #f0b90b;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(240,185,11,0.25);
    }
    
    .purchase-dialog { 
        background: linear-gradient(180deg, #1a1d20, #0e1113); 
        border: 3px solid #f0b90b; 
        border-radius: 16px; 
        padding: 28px; 
        margin: 16px 0;
        box-shadow: 0 12px 40px rgba(240,185,11,0.4);
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
    }
    
    .icon-badge {
        background: rgba(240,185,11,0.2);
        padding: 8px 16px;
        border-radius: 20px;
        color: #f0b90b;
        font-weight: 700;
        border: 1px solid rgba(240,185,11,0.3);
    }
    
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #f0b90b, transparent);
        margin: 24px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Helper functions (те же)
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

@st.fragment(run_every=30)
def market_display():
    # Заголовок
    st.markdown("<div class='header-container'><h1 class='main-title'>💎 ВАНИНА ИГРА 💎</h1></div>", unsafe_allow_html=True)

    # Новости
    news = [
        "Рынок золота демонстрирует стабильный рост - эксперты прогнозируют дальнейшее укрепление позиций",
        "Новый завод открыл двери - аналитики ожидают значительный прирост к заводским акциям",
        "Крупные инвесторы прогнозируют масштабный рост цен на ближайший квартал",
    ]
    st.markdown(f"<div class='news-banner'><h3 style='color:#ccccff; margin:0;'>📰 {random.choice(news)}</h3></div>", unsafe_allow_html=True)

    # Обновление
    if st.button("🔄 ОБНОВИТЬ"):
        st.cache_data.clear()
        st.rerun()

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
                <h3 style='color:#f0b90b; margin:0 0 12px 0; font-size:20px;'>🪙 КУРС ЗОЛОТА</h3>
                <div style='display:flex; justify-content:space-between;'>
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

    # Обработка акций
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
        st.dataframe(purchases.tail(20), use_container_width=True)
        return

    # Портфель
    if st.session_state.view_mode == "portfolio":
        if not st.session_state.user:
            st.warning("⚠️ Войдите в профиль")
            return
        
        purchases = load_purchases()
        if purchases.empty:
            st.info("Портфель пуст")
            return
        
        st.markdown("<div class='portfolio-header'><h2 style='color:#f0b90b; margin:0;'>💼 ПОРТФЕЛЬ</h2></div>", unsafe_allow_html=True)
        
        # Простая статистика
        header_cols = list(purchases.columns)
        col_price = next((c for c in header_cols if any(k in c.lower() for k in ["price", "цена"])), None)
        if col_price:
            total = purchases[col_price].apply(safe_float).sum()
            st.metric("💰 Инвестировано", f"${total:,.0f}")
        
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
            highlight = "highlight-100" if abs(pct) > 100 else ""
            
            # Создаем контейнер
            card_container = st.container()
            with card_container:
                st.markdown(f"""
                    <div class="stock-card {highlight}">
                        <div>
                            <div class="stock-name">{item['Название']}</div>
                            <div class="stock-type">{item['Тип']}</div>
                        </div>
                        <div style='margin-top:20px;'>
                            <div style='display:flex; justify-content:space-between; align-items:flex-end;'>
                                <div>
                                    <div class="old-price">{item['Базовая цена']:.0f}$</div>
                                    <div class="current-price">{item['final_price']}$</div>
                                </div>
                                <div class="change-pct {color_cls}">{'+'if pct>0 else''}{pct:.2f}%</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Кнопка покупки
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
                <h2 style='color:#f0b90b;'>💰 ПОКУПКА: {d['stock_name']}</h2>
                <div style='text-align:center; font-size:24px; margin:16px 0;'>
                    Цена: <span style='color:#f0b90b; font-weight:900;'>${d['price']:,.0f}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        qty = st.slider("Количество:", 1, 100, 1)
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
                        st.success("✅ Успешно!")
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
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚪 ВЫЙТИ", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    ### ℹ️ О СИСТЕМЕ
    - 🔄 Автообновление 30 сек
    - 📊 Google Sheets интеграция
    - 💎 Влияние золота
    """)

market_display()
