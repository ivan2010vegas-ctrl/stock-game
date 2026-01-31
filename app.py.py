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
import os

st.set_page_config(page_title="Ванина игра", layout="wide")

# -----------------------
# CSS
# -----------------------
st.markdown("""
    <style>
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    .stApp { background-color: #0b0e11; color: #FFFFFF; }

    div.stButton > button {
        background: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #2b2b2b !important;
        padding: 8px 12px !important;
        font-weight: 600 !important;
    }

    .stock-card { background:#1a1d20; border-radius:16px; padding:20px; border:1px solid #2b2f33; margin-bottom:16px; min-height:200px; display:flex; flex-direction:column; justify-content:space-between;}
    .stock-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; }
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
    """Split modifiers cell into tokens (keeps numbers as separate tokens)."""
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
def load_reference_tables():
    client = get_gspread_client()


@st.cache_data(ttl=5)
def load_reference_tables():
    client = get_gspread_client()
    try:
        df_zavod = pd.DataFrame(
            client.open("Таблица дификаторы_заводские_проценты")
            .sheet1.get_all_records()
        )
    except Exception:
        df_zavod = pd.DataFrame(columns=["Значение", "%"])

    try:
        df_region = pd.DataFrame(
            client.open("Модификаторы_региональные_проценты")
            .sheet1.get_all_records()
        )
    except Exception:
        df_region = pd.DataFrame(columns=["Значение", "%"])

    return df_zavod, df_region


@st.cache_data(ttl=5)
def load_stocks_table():
    client = get_gspread_client()
    try:
        return pd.DataFrame(
            client.open("Акции").worksheet("Лист1").get_all_records()
        )
    except Exception:
        return pd.DataFrame()


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

# -----------------------
# Strict modifier matching
# -----------------------
def sum_modifiers_and_list(raw_text, ref_df):
    """
    Strict matching using 'Тип' and 'Значение' from reference table.
    Returns: total_pct (float), found_pairs [(display_str, pct), ...], tokens (list)
    Avoids duplicate found entries (by display string).
    """
    if ref_df is None or ref_df.empty:
        return 0.0, [], []

    def normalize(s):
        return re.sub(r'\W+', '', str(s).lower())

    # Build normalized ref_map: key -> (display, pct)
    ref_map = {}
    original_rows = []

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
            # keep first occurrence for a key
            if k not in ref_map:
                ref_map[k] = (display, safe_float(pct))

        original_rows.append((typ_str, val_str, safe_float(pct)))

    # Tokens from cell
    tokens = split_modifiers(raw_text)
    matched_keys = set()
    matched_displays = set()   # <-- prevent duplicates by display
    found = []

    for tok in tokens:
        if not tok:
            continue
        tok_norm = normalize(tok)

        # exact normalized match
        if tok_norm in ref_map and tok_norm not in matched_keys:
            disp, p = ref_map[tok_norm]
            disp_norm = normalize(disp)
            if disp_norm not in matched_displays:
                matched_keys.add(tok_norm)
                matched_displays.add(disp_norm)
                found.append((disp, p))
            else:
                # still mark key used to avoid later matching same key
                matched_keys.add(tok_norm)
            continue

        # numeric token handling
        if re.fullmatch(r'\d{1,6}', tok.strip()):
            num = re.sub(r'\W+', '', tok.strip())
            # direct key by number
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
            # search number inside display strings (as whole word)
            for key, (disp, pct) in ref_map.items():
                if key in matched_keys:
                    continue
                # check number in original display (word boundary)
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
    st.markdown("<h1 style='color:#f0b90b; margin-bottom:6px;'>Ванина игра</h1>", unsafe_allow_html=True)

    # -----------------------
    # Новости
    # -----------------------
    news_list = [
    "Новости 1: Рост рынка золота удивляет экспертов.",
    "Новости 2: Открылся новый завод, возможно это принесет подбавку к заводским акциям.",
    "Новости 3: Акции компаний резко упали.",
    "Новости 4: Инвесторы прогнозируют рост цен.",
    "Новости 5: Экономика рынка стабилизируется.",
    "Новости 6: Новые законы могут повлиять на рынок.",
    "Новости 7: Поступили данные о прибыли компаний.",
    "Новости 8: Региональные акции пользуются спросом.",
    "Новости 9: Инновационный проект привлёк инвестиции.",
    "Новости 10: Аналитики повышают прогноз по золоту.",
    "Новости 11: Волатильность на рынке выше нормы.",
    "Новости 12: Слияние компаний одобрено.",
    "Новости 13: Цены на ресурсы растут.",
    "Новости 14: Эксперты советуют держать региональные акции .",
    "Новости 15: Рынок переживает небольшую коррекцию.",
    "Новости 16: Некоторые компании будут объявлять дивиденды.",
    "Новости 17: Инфляция ниже ожидаемой.",
    "Новости 18: Международные рынки демонстрируют рост.",
    "Новости 19: Новая технология снижает издержки.",
    "Новости 20: Акции достигли исторического максимума.",
    "Новости 21: Появились слухи о поглощении заводских компаний.",
    "Новости 22: Экономический форум обсудил новые стратегии.",
    "Новости 23: Инвесторы ждут отчёты за квартал.",
    "Новости 24: Центробанк изменил ключевую ставку.",
    "Новости 25: Прирост производства превысил прогноз.",
    "Новости 26: Влияние внешней политики на рынок.",
    "Новости 27: Региональные акции демонстрируют рост.",
    "Новости 28: Новые инвестиционные возможности открыты.",
    "Новости 29: Цены на золото стабилизировались.",
    "Новости 30: Заводские компания увеличила объём производства.",
    "Новости 31: Финансовые аналитики пересмотрели прогноз.",
    "Новости 32: Появились новые требования к инвестициям.",
    "Новости 33: Некоторые акции подорожали на 15%.",
    "Новости 34: Рынок реагирует на мировые события.",
    "Новости 35: Инвесторы осторожничают с покупками.",
    "Новости 36: Власти объявили новые меры поддержки.",
    "Новости 37: Акции потеряли часть стоимости.",
    "Новости 38: Стабильность валютного курса радует инвесторов.",
    "Новости 39: Объём продаж компаний вырос.",
    "Новости 40: Эксперты предсказывают рост рынка.",
    "Новости 41: Новости мировых ресурсов влияют на акции.",
    "Новости 42: Новые стартапы привлекают внимание инвесторов.",
    "Новости 43: Акции показали рекордный рост.",
    "Новости 44: Рынок золота демонстрирует колебания.",
    "Новости 45: Крупные компании объявили стратегию расширения.",
    "Новости 46: Рост цен на нефть сказывается на акциях.",
    "Новости 47: Аналитики советуют покупать заводские акции.",
    "Новости 48: Новые законы стимулируют экономику.",
    "Новости 49: Акции демонстрируют высокую волатильность.",
    "Новости 50: Рынок закрывается с положительной динамикой."
    ]
    random_news = random.choice(news_list)
    clean_news = re.sub(r'^Новости\s*\d+\s*:\s*', '', random_news)
    st.markdown(
        f"<h3 style='color:#ccccff; margin-bottom:12px;'>📰 Актуальные Новости: {clean_news}</h3>",
        unsafe_allow_html=True
    )

    # -----------------------
    # Кнопка обновить
    # -----------------------
    col_refresh, _ = st.columns([1, 6])
    with col_refresh:
        if st.button("Обновить"):
            for func in [load_stocks_table, load_reference_tables, load_purchases, get_gspread_client]:
                try:
                    func.clear()
                except Exception:
                    pass
            st.rerun()

    # -----------------------
    # Остальной код (графики, акции, портфель)
    # -----------------------


    # -----------------------
    # market_display...




    # update candle
    last_close = st.session_state.gold_history[-1]['close']
    o = last_close
    c = o + random.uniform(-15, 15)
    h = max(o, c) + random.uniform(0, 7)
    l = min(o, c) - random.uniform(0, 7)
    st.session_state.gold_history.append({'open': o, 'high': h, 'low': l, 'close': c})
    if len(st.session_state.gold_history) > 60:
        st.session_state.gold_history.pop(0)

    # load tables
    try:
        df_raw = load_stocks_table()
        df_ref_zavod, df_ref_region = load_reference_tables()
    except FileNotFoundError as fe:
        st.error(f"Ошибка авторизации Google API: {fe}")
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {e}")

    status_col = find_col_in_df(df_raw, ['Статус', 'status'])
    name_col = find_col_in_df(df_raw, ['назв', 'name'])
    type_col = find_col_in_df(df_raw, ['тип', 'type'])
    base_price_col = find_col_in_df(df_raw, ['баз', 'price', 'цена', 'cost'])
    mod_col = find_col_in_df(df_raw, ['модифик', 'modifier'])

    if status_col is None:
        st.error("В таблице «Акции» не найдена колонка со статусом.")

    col_left, col_right = st.columns([3, 1])
    with col_left:
        current_gold = st.session_state.gold_history[-1]['close']
        gold_imp = ((current_gold - 1200.0) / 1200.0) * 100.0
        st.markdown(f"### 🪙 Курс Золота: {current_gold:.2f}$")
        hist_df = pd.DataFrame(st.session_state.gold_history)
        fig = go.Figure(data=[go.Candlestick(
            open=hist_df['open'], high=hist_df['high'], low=hist_df['low'], close=hist_df['close'],
            increasing_line_color='#0ecb81', decreasing_line_color='#f6465d'
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=8, b=0), xaxis_rangeslider_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_right:
        st.markdown("#### Навигация")
        if st.button("Все акции"):
            st.session_state.view_mode = "all"
            st.rerun()
        if st.button("Топ роста"):
            st.session_state.view_mode = "top"
            st.rerun()
        if st.button("Портфель"):
            st.session_state.view_mode = "portfolio"
            st.rerun()
        st.markdown("<div class='small-muted' style='margin-top:8px'>Автообновление каждые 30 секунд</div>", unsafe_allow_html=True)

    processed = []
    removed_stock_names = set()
    st.session_state['last_found_map'] = {}
    st.session_state['last_tokens_map'] = {}
    st.session_state['last_raw_map'] = {}

    if df_raw is None or df_raw.empty:
        st.info("Нет данных таблицы «Акции».")

    try:
        status_series = df_raw[status_col].astype(str).str.upper()
        open_mask = status_series.str.contains('ОТКР', regex=False)
        open_stocks = df_raw[open_mask].copy()
    except Exception:
        st.error("Не удалось отфильтровать открытые акции.")

    for i, row in open_stocks.iterrows():
        name = safe_row_get(row, [name_col] if name_col else [], default=f'#{i}')
        if not name:
            name = f'#{i}'
        typ = safe_row_get(row, [type_col] if type_col else [], default='')
        base_price = safe_float(safe_row_get(row, [base_price_col] if base_price_col else [], default=0))
        raw_mod = safe_row_get(row, [mod_col] if mod_col else [], default='')

        is_zavod = "завод" in str(typ).lower()
        
import streamlit as st

# --- очистка названий колонок, один раз ---
df.columns = [col.strip() for col in df.columns]

# --- ищем колонку "Статус" один раз ---
col_status = [col for col in df.columns if col.lower() == "статус"][0]

# --- для отладки один раз выводим ---
st.write(sheet.get_all_records()[0])
st.write(df.columns)

# --- цикл по строкам ---
for i, row in open_stocks.iterrows():
    name = safe_row_get(row, [name_col] if name_col else [], default=f'#{i}')
    if not name:
        name = f'#{i}'
    typ = safe_row_get(row, [type_col] if type_col else [], default='')
    base_price = safe_float(safe_row_get(row, [base_price_col] if base_price_col else [], default=0))
    raw_mod = safe_row_get(row, [mod_col] if mod_col else [], default='')

    is_zavod = "завод" in str(typ).lower()
    
    # --- статус для этой строки ---
    status_value = row[col_status]

    # Ищем модификаторы во ВСЕХ справочниках (региональный + заводской)
    parts = []
    if df_ref_region is not None and not df_ref_region.empty:
        parts.append(df_ref_region.copy())
    if df_ref_zavod is not None and not df_ref_zavod.empty:
        parts.append(df_ref_zavod.copy())


        if parts:
            ref_table = pd.concat(parts, ignore_index=True, sort=False)
            # Попытаемся привести имена колонок к ожидаемым и убрать дубликаты по (Тип, Значение)
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

    # Portfolio view
    if st.session_state.view_mode == "portfolio":
        if not st.session_state.user:
        st.warning("Войдите в профиль, чтобы просмотреть портфель.")
    else:

        purchases = load_purchases()
        if purchases is None or purchases.empty:
            st.info("Портфель пуст.")
        else:

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
            st.info("У вас ещё нет покупок.")
        else:

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

        st.markdown(f"<div class='portfolio-header'><h2 style='color:#f0b90b; margin:0;'>💼 Портфель — {st.session_state.user}</h2></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>Инвестировано</div><div class='stat-value'>${total_invested:,.0f}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>Сейчас стоит</div><div class='stat-value'>${total_current:,.0f}</div></div>", unsafe_allow_html=True)
        with c3:
            pnl_class = "profit" if total_pnl >= 0 else "loss"
            pnl_sign = "+" if total_pnl >= 0 else ""
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>Прибыль/Убыток</div><div class='stat-value {pnl_class}'>{pnl_sign}${total_pnl:,.0f}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='portfolio-stat'><div class='stat-label'>Позиций</div><div class='stat-value'>{len(grouped)}</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📊 Ваши акции")

        for _, pos in grouped.sort_values(by='current_value', ascending=False).iterrows():
            pnl_sign = "+" if pos['pnl'] >= 0 else ""
            st.markdown(f"""
                <div class='position-item'>
                    <div class='position-header'>
                        <div class='position-title'>{pos['name']}</div>
                        <div class='position-badge'>x{int(pos['quantity'])}</div>
                    </div>
                    <div class='position-stats'>
                        <div class='mini-stat'><div class='mini-stat-label'>Цена покупки</div><div class='mini-stat-value'>${pos['avg_price']:,.0f}</div></div>
                        <div class='mini-stat'><div class='mini-stat-label'>Сейчас</div><div class='mini-stat-value'>${pos['current_price']:,.0f}</div></div>
                        <div class='mini-stat'><div class='mini-stat-label'>Стоимость</div><div class='mini-stat-value'>${pos['current_value']:,.0f}</div></div>
                        <div class='mini-stat'><div class='mini-stat-label'>P/L</div><div class='mini-stat-value' style='color:{'#0ecb81' if pos['pnl']>=0 else '#f6465d'}'>{pnl_sign}${abs(pos['pnl']):,.0f}</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        if st.checkbox("🛠️ Показать отладку"):
            with st.expander("Найденные модификаторы / Токены / Raw"):
                for stock_name in st.session_state.get('last_found_map', {}):
                    mods = st.session_state['last_found_map'].get(stock_name, [])
                    tokens = st.session_state['last_tokens_map'].get(stock_name, [])
                    raw = st.session_state['last_raw_map'].get(stock_name, '')
                    st.write(f"• {stock_name}: raw='{raw}' tokens={tokens} -> found={mods}")
        else:

    if st.session_state.view_mode == "top":
        processed = sorted(processed, key=lambda x: x['pct'], reverse=True)[:9]

    cols = st.columns(3)
    for idx, item in enumerate(processed):
        with cols[idx % 3]:
            pct = item['pct']
            sign = '+' if pct > 0 else ''
            pct_text = f"{sign}{pct:.2f}%"
            color_cls = "pos" if pct >= 0 else "neg"
            highlight = "highlight-100" if abs(pct) > 100 else ""

            st.markdown(f"""
                <div class="stock-card {highlight}">
                    <div class="stock-header">
                        <div class="stock-title-section">
                            <div class="stock-name">{item['Название']}</div>
                            <div class="stock-type">{item['Тип']}</div>
                        </div>
                    </div>
                    <div class="stock-footer">
                        <div class="price-section">
                            <div class="old-price">{item['Базовая цена']:.0f}$</div>
                            <div class="current-price">{item['final_price']}$</div>
                        </div>
                        <div class="change-section">
                            <div class="change-pct {color_cls}">{pct_text}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col2:
                if st.button("купить", key=f"buy_{item['Название']}_{idx}", use_container_width=True):
                    if not st.session_state.user:
                        st.error("Войдите в профиль!")
                    else:
                        st.session_state.purchase_dialog = {
                            'stock_name': item['Название'],
                            'price': item['final_price'],
                            'idx': idx
                        }
                        st.rerun()

    # purchase dialog
    if st.session_state.purchase_dialog:
        dialog_data = st.session_state.purchase_dialog
        st.markdown("<div class='purchase-dialog'>", unsafe_allow_html=True)
        st.markdown(f"## 💰 Покупка: **{dialog_data['stock_name']}**")
        st.markdown(f"### Цена: **${dialog_data['price']:,.0f}**")
        quantity = st.slider("Количество акций:", min_value=1, max_value=100, value=1, step=1, key="quantity_slider")
        total_price = quantity * dialog_data['price']
        st.markdown(f"<div class='total-price'>ИТОГО: ${total_price:,.0f}</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Купить", use_container_width=True):
                ws = get_buy_worksheet()
                if ws is None:
                    st.error("Ошибка подключения.")
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
                        st.success(f"✅ Куплено {quantity} акций за ${total_price:,.0f}!")
                        st.session_state.purchase_dialog = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
        with col2:
            if st.button("❌ Отмена", use_container_width=True):
                st.session_state.purchase_dialog = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # debug panel (collapsed)
    if st.session_state.get('last_found_map'):
        with st.expander("🛠️ Отладка модификаторов"):
            for stock_name, mods in st.session_state['last_found_map'].items():
                if mods:
                    formatted = ", ".join([f"{m[0]} ({m[1]}%)" for m in mods])
                    st.write(f"• {stock_name}: {formatted}")
                else:
                    st.write(f"• {stock_name}: нет")

# Sidebar
with st.sidebar:
    st.title("👤 Профиль")
    if not st.session_state.user:
        u = st.selectbox("Кто вы?", ["артем", "богдан", "руслан", "разработчик"])
        if st.button("Вход"):
            st.session_state.user = u
            st.rerun()
    else:
        st.write(f"Привет, **{st.session_state.user}**!")
        if st.button("Выход"):
            st.session_state.user = None
            st.rerun()


market_display()






