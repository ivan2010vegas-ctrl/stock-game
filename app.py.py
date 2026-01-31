import streamlit as st
import gspread
import pandas as pd
import random
import string
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

st.set_page_config(page_title="Ванина игра", layout="wide")

# CSS (сокращено для краткости)
st.markdown("""<style>
[data-testid="stStatusWidget"] { visibility: hidden !important; }
.stApp { background-color: #0b0e11; color: #FFFFFF; }
div.stButton > button { background: #000000 !important; color: #FFFFFF !important; border-radius: 8px !important; border: 1px solid #2b2b2b !important; padding: 8px 12px !important; font-weight: 600 !important; }
.stock-card { background:#1a1d20; border-radius:16px; padding:20px; border:1px solid #2b2f33; margin-bottom:16px; min-height:200px; display:flex; flex-direction:column; justify-content:space-between;}
.stock-name { color:#FFFFFF; font-size:22px; font-weight:700; margin-bottom:4px; line-height:1.2; }
.stock-type { color:#9aa0a6; font-size:13px; }
.old-price { color:#9aa0a6; font-size:14px; }
.current-price { color:#f0b90b; font-size:32px; font-weight:800; line-height:1; }
.change-pct { font-size:24px; font-weight:800; }
.pos { color:#0ecb81; } .neg { color:#f6465d; }
.highlight-100 { box-shadow:0 0 15px 3px rgba(240,185,11,0.15); border:2px solid #f0b90b; }
.portfolio-header { background:linear-gradient(135deg,#1a1d20 0%,#0e1113 100%); border-radius:12px; padding:24px; margin-bottom:20px; border:1px solid #f0b90b; }
.portfolio-stat { text-align:center; padding:16px; }
.stat-label { color:#9aa0a6; font-size:13px; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }
.stat-value { color:#FFFFFF; font-size:28px; font-weight:800; }
.position-item { background:linear-gradient(135deg,#1a1d20 0%,#161719 100%); border-radius:12px; padding:20px; margin-bottom:12px; border:1px solid #2b2f33; }
.position-title { color:#f0b90b; font-size:20px; font-weight:700; }
.small-muted { color:#888; font-size:13px; }
.purchase-dialog { background:linear-gradient(180deg,#1a1d20,#0e1113); border:2px solid #f0b90b; border-radius:12px; padding:20px; margin:10px 0; }
.total-price { color:#0ecb81; font-size:24px; font-weight:800; text-align:center; padding:15px; background:rgba(14,203,129,0.1); border-radius:8px; margin:10px 0; }
</style>""", unsafe_allow_html=True)

# Helpers
def safe_float(value):
    try:
        if isinstance(value, str):
            value = value.replace('$', '').replace('%', '').replace(',', '.').strip()
        return float(value)
    except Exception:
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
    client = get_gspread_client()
    try:
        return pd.DataFrame(client.open("«Акции»").worksheet("Лист1").get_all_records())
    except Exception as e:
        st.error(f"❌ Ошибка загрузки акций: {e}")
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
        ws = get_gspread_client().open("Таблица «Покупки»").worksheet("Лист6")
        return pd.DataFrame(ws.get_all_records())
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
st.session_state.setdefault('view_mode', "top")
st.session_state.setdefault('purchase_dialog', None)

# Main display
@st.fragment(run_every=30)
def market_display():
    st.markdown("<h1 style='color:#f0b90b;'>Ванина игра</h1>", unsafe_allow_html=True)

    # Новости
    news = ["Рост рынка золота удивляет экспертов.", "Открылся новый завод.", "Акции компаний резко упали."]
    st.markdown(f"<h3 style='color:#ccccff;'>📰 {random.choice(news)}</h3>", unsafe_allow_html=True)

    # Обновление
    if st.button("🔄 Обновить"):
        st.cache_data.clear()
        st.rerun()

    # Золото
    last = st.session_state.gold_history[-1]['close']
    c = last + random.uniform(-15, 15)
    st.session_state.gold_history.append({'open': last, 'high': max(last, c)+random.uniform(0, 7), 'low': min(last, c)-random.uniform(0, 7), 'close': c})
    if len(st.session_state.gold_history) > 60:
        st.session_state.gold_history.pop(0)

    # Загрузка данных
    df_raw = load_stocks_table()
    df_ref_zavod, df_ref_region = load_reference_tables()

    if df_raw.empty:
        st.info("Нет данных")
        return

    df_raw.columns = [str(col).strip() for col in df_raw.columns]

    status_col = find_col_in_df(df_raw, ['статус', 'status'])
    name_col = find_col_in_df(df_raw, ['назв', 'name'])
    type_col = find_col_in_df(df_raw, ['тип', 'type'])
    base_price_col = find_col_in_df(df_raw, ['баз', 'price', 'цена'])
    mod_col = find_col_in_df(df_raw, ['модифик', 'modifier'])

    if not status_col:
        st.error("Нет колонки Статус")
        return

    open_stocks = df_raw[df_raw[status_col].astype(str).str.upper().str.contains('ОТКР', regex=False)].copy()

    # Золото
    gold_imp = 0.0
    if len(st.session_state.gold_history) >= 2:
        prev = st.session_state.gold_history[-2]['close']
        curr = st.session_state.gold_history[-1]['close']
        gold_imp = ((curr - prev) / prev) * 100 if prev != 0 else 0.0

    # Обработка
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
            processed.append({"Название": name, "Тип": typ, "Базовая цена": base_price, "pct": total_pct, "final_price": final_price})

    # Отображение
    if st.session_state.view_mode == "top":
        cols = st.columns(3)
        for idx, item in enumerate(sorted(processed, key=lambda x: x['pct'], reverse=True)[:9]):
            with cols[idx % 3]:
                pct = item['pct']
                st.markdown(f"""
                    <div class="stock-card">
                        <div class="stock-name">{item['Название']}</div>
                        <div class="stock-type">{item['Тип']}</div>
                        <div style='margin-top:auto;'>
                            <div style='display:flex; justify-content:space-between;'>
                                <div>
                                    <div class="old-price">{item['Базовая цена']:.0f}$</div>
                                    <div class="current-price">{item['final_price']}$</div>
                                </div>
                                <div class="change-pct {'pos' if pct >= 0 else 'neg'}">{'+'if pct>0 else''}{pct:.2f}%</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button("купить", key=f"buy_{idx}"):
                    if not st.session_state.user:
                        st.error("Войдите!")
                    else:
                        st.session_state.purchase_dialog = {'stock_name': item['Название'], 'price': item['final_price']}
                        st.rerun()

        # Покупка
        if st.session_state.purchase_dialog:
            d = st.session_state.purchase_dialog
            st.markdown(f"## 💰 Покупка: {d['stock_name']}")
            qty = st.slider("Количество:", 1, 100, 1)
            if st.button("✅ Купить"):
                ws = get_buy_worksheet()
                if ws:
                    ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.user, d['stock_name'], d['price'], "TX-"+str(random.randint(100000, 999999))])
                    st.success("✅ Куплено!")
                    st.session_state.purchase_dialog = None
                    st.rerun()

    elif st.session_state.view_mode == "portfolio":
        if not st.session_state.user:
            st.warning("Войдите в профиль")
        else:
            st.info("Портфель в разработке")

# Sidebar
with st.sidebar:
    st.title("👤 Профиль")
    if not st.session_state.user:
        u = st.selectbox("Кто вы?", ["артем", "богдан", "руслан"])
        if st.button("Вход"):
            st.session_state.user = u
            st.rerun()
    else:
        st.write(f"**{st.session_state.user}**!")
        if st.button("Выход"):
            st.session_state.user = None
            st.rerun()
    
    st.markdown("---")
    view = st.radio("Режим:", ["top", "portfolio"], format_func=lambda x: "🔥 Акции" if x == "top" else "💼 Портфель")
    if view != st.session_state.view_mode:
        st.session_state.view_mode = view
        st.rerun()

market_display()
