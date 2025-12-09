import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import time

# Конфігурація сторінки
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === API ТА ФУНКЦІЇ ===

# API базовий URL
API_BASE_URL = st.sidebar.text_input("API URL", value="http://localhost:8000", help="Base URL для FastAPI")

# Функція для виклику API
@st.cache_data(ttl=30)  # Кешування на 30 секунд для звичайних запитів
def fetch_api(endpoint, params=None):
    """Викликає API ендпоінт і повертає JSON відповідь"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=5) # Зменшив таймаут для швидшої реакції
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

# Окрема функція для real-time без кешування
def fetch_api_no_cache(endpoint, params=None):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=2)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

# === СТАН (SESSION STATE) ===

if "use_log_scale" not in st.session_state:
    st.session_state.use_log_scale = False

if "price_history" not in st.session_state:
    st.session_state.price_history = {}  # {symbol: [(timestamp, buy_price, sell_price), ...]}

# === ІНТЕРФЕЙС ===

st.title("📊 Trading Analytics Dashboard")
st.markdown("---")

# Health Status
with st.expander("🏥 Health Status", expanded=False):
    health_data = fetch_api("/health")
    if health_data:
        st.success(f"✅ API Status: {health_data.get('status', 'Unknown')}")
    else:
        st.error("❌ API недоступний")

# Отримання списку символів (оптимізовано)
top_all = fetch_api("/top_n_highest_volumes", params={"top_n": 50})
if top_all and top_all.get("top_symbols"):
    symbols_list = [item["symbol"] for item in top_all["top_symbols"]]
else:
    symbols_list = ["XBTUSD", "ETHUSD", "ADAUSD", "SOLUSD", "DOGEUSD", "XRPUSD", "LINKUSD"]
default_symbol = symbols_list[0] if symbols_list else "XBTUSD"

# Sidebar
st.sidebar.header("⚙️ Налаштування")
use_log_scale = st.sidebar.checkbox(
    "📊 Логарифмічна шкала", 
    value=st.session_state.use_log_scale, 
    key="log_scale_checkbox"
)
st.session_state.use_log_scale = use_log_scale

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 6 Годин",
    "📊 12 Годин",
    "🔍 Аналіз",
    "🏆 Топ обсяги",
    "💵 Ціни",
    "📡 Real-time"
])

# === ЛОГІКА ВКЛАДОК ===

# TAB 1: Статистика за 6 годин
with tab1:
    st.header("Статистика за останні 6 годин")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Кількість транзакцій")
        transactions_data = fetch_api("/transactions_count_last_6_hours")
        if transactions_data and transactions_data.get("count"):
            all_data = [{"symbol": k, "val": v.get("total_transaction_count", 0)} for k, v in transactions_data["count"].items()]
            df = pd.DataFrame(all_data)
            if not df.empty:
                # Створюємо копію для графіка (може бути з логарифмованими значеннями)
                plot_df = df.copy()
                y_col = "val"
                if use_log_scale:
                    plot_df["log_val"] = np.log1p(plot_df["val"])
                    y_col = "log_val"
                
                fig = px.bar(plot_df, x="symbol", y=y_col, title="Транзакції (6г)", color=y_col)
                st.plotly_chart(fig, width='stretch')
                
                # Таблиця з оригінальними даними (не логарифмованими)
                df_display = df.copy()
                df_display.columns = ["Символ", "Кількість транзакцій"]
                df_display = df_display.sort_values("Кількість транзакцій", ascending=False)
                st.dataframe(df_display, width='stretch', hide_index=True)
                
                # Кнопка експорту CSV
                csv_data = df_display.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Експортувати в CSV",
                    data=csv_data,
                    file_name=f"transactions_6h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="export_transactions_6h"
                )
        else:
            st.info("Немає даних")

    with col2:
        st.subheader("Обсяг торгівлі")
        vol_data = fetch_api("/trade_volume_last_6_hours")
        if vol_data and vol_data.get("count"):
            all_data = [{"symbol": k, "val": v.get("total_trade_volume", 0)} for k, v in vol_data["count"].items()]
            df = pd.DataFrame(all_data)
            if not df.empty:
                # Створюємо копію для графіка (може бути з логарифмованими значеннями)
                plot_df = df.copy()
                y_col = "val"
                if use_log_scale:
                    plot_df["log_val"] = np.log1p(plot_df["val"])
                    y_col = "log_val"
                fig = px.bar(plot_df, x="symbol", y=y_col, title="Обсяг (6г)", color=y_col, color_continuous_scale="plasma")
                st.plotly_chart(fig, width='stretch')
                
                # Таблиця з оригінальними даними (не логарифмованими)
                df_display = df.copy()
                df_display.columns = ["Символ", "Обсяг торгівлі"]
                df_display = df_display.sort_values("Обсяг торгівлі", ascending=False)
                
                # Створюємо копію для відображення (з форматуванням)
                df_display_formatted = df_display.copy()
                df_display_formatted["Обсяг торгівлі"] = df_display_formatted["Обсяг торгівлі"].apply(lambda x: f"{x:,.2f}")
                st.dataframe(df_display_formatted, width='stretch', hide_index=True)
                
                # Кнопка експорту CSV (з оригінальними числовими значеннями)
                csv_data = df_display.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Експортувати в CSV",
                    data=csv_data,
                    file_name=f"volume_6h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="export_volume_6h"
                )
        else:
            st.info("Немає даних")

# TAB 2: Статистика за 12 годин
with tab2:
    st.header("Статистика за 12 годин")
    hourly_stats = fetch_api("/hourly_stats_last_12_hours")
    
    if hourly_stats and hourly_stats.get("stats"):
        all_data = []
        for symbol, values in hourly_stats["stats"].items():
            for item in values:
                all_data.append({
                    "symbol": symbol,
                    "hour": pd.to_datetime(item["hour_start"]),
                    "count": item["transaction_count"],
                    "volume": item["total_trade_volume"]
                })
        
        if all_data:
            df = pd.DataFrame(all_data)
            col1, col2 = st.columns(2)
            with col1:
                y_col = "count"
                if use_log_scale:
                    df["log_count"] = np.log1p(df["count"])
                    y_col = "log_count"
                fig = px.line(df, x="hour", y=y_col, color="symbol", title="Кількість транзакцій" + (" (логарифмічна шкала)" if use_log_scale else ""))
                st.plotly_chart(fig, width='stretch')
            with col2:
                y_col = "volume"
                if use_log_scale:
                    df["log_vol"] = np.log1p(df["volume"])
                    y_col = "log_vol"
                fig = px.line(df.sort_values(["symbol", "hour"]), x="hour", y=y_col, color="symbol", title="Обсяг" + (" (логарифмічна шкала)" if use_log_scale else ""))
                fig.update_traces(fill='tozeroy', mode='lines+markers')
                st.plotly_chart(fig, width='stretch')
            
            # Таблиця з детальними даними
            st.subheader("Детальна таблиця статистики")
            # Вибираємо тільки оригінальні колонки (без логарифмованих)
            df_display = df[["symbol", "hour", "count", "volume"]].copy()
            df_display.columns = ["Символ", "Година", "Кількість транзакцій", "Обсяг торгівлі"]
            
            # Створюємо копію для експорту (з оригінальними даними)
            df_export = df_display.copy()
            df_export["Година"] = df_export["Година"].dt.strftime("%Y-%m-%d %H:00")
            
            # Форматуємо для відображення
            df_display["Година"] = df_display["Година"].dt.strftime("%Y-%m-%d %H:00")
            df_display["Обсяг торгівлі"] = df_display["Обсяг торгівлі"].apply(lambda x: f"{x:,.2f}")
            # Сортуємо за часом (найновіші спочатку)
            df_display = df_display.sort_values(["Година", "Символ"], ascending=[False, True])
            df_export = df_export.sort_values(["Година", "Символ"], ascending=[False, True])
            
            st.dataframe(df_display, width='stretch', hide_index=True)
            
            # Кнопка експорту CSV
            csv_data = df_export.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Експортувати в CSV",
                data=csv_data,
                file_name=f"stats_12h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="export_stats_12h"
            )

# TAB 3: Детальний аналіз
with tab3:
    st.header("Детальний аналіз")
    c1, c2 = st.columns(2)
    with c1:
        s_sym = st.selectbox("Символ", symbols_list, key="det_sym")
    with c2:
        n_min = st.number_input("Хвилини", 1, 1440, 5)
    
    if st.button("Аналіз"):
        res = fetch_api("/transactions_in_last_n_min", params={"symbol": s_sym, "n_minutes": n_min})
        if res:
            st.metric("Транзакції", res.get("number_of_trades", 0))
            st.info(f"{res.get('number_of_trades', 0)} угод за {n_min} хв для {s_sym}")

# TAB 4: Топ обсяги
with tab4:
    st.header("Топ символів за обсягом")
    top_n = st.slider("Кількість символів", 1, 5, 3, key="top_n_slider")
    top_v = fetch_api("/top_n_highest_volumes", params={"top_n": top_n})
    if top_v and top_v.get("top_symbols"):
        df = pd.DataFrame(top_v["top_symbols"])
        
        # Підготовка даних для графіка з урахуванням логарифмічної шкали
        plot_df = df.copy()
        y_col = "total_volume"
        y_label = "Обсяг торгівлі"
        
        if use_log_scale:
            plot_df["log_volume"] = np.log1p(plot_df["total_volume"])
            y_col = "log_volume"
            y_label = "Обсяг торгівлі (log scale)"
        
        fig = px.bar(
            plot_df, 
            x="symbol", 
            y=y_col, 
            color=y_col,
            title=f"Топ {top_n} символів за обсягом" + (" (логарифмічна шкала)" if use_log_scale else ""),
            labels={"symbol": "Символ", y_col: y_label}
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.warning("Не вдалося отримати дані про топ обсяги")

# TAB 5: Поточні ціни
with tab5:
    st.header("Поточні ціни символів")
    
    # Ініціалізація session state для збереження вибраних символів
    if "selected_price_symbols" not in st.session_state:
        st.session_state.selected_price_symbols = [default_symbol] if default_symbol in symbols_list else []
    
    sel_syms = st.multiselect(
        "Виберіть символи", 
        symbols_list, 
        default=st.session_state.selected_price_symbols,
        key="price_symbols_multiselect"
    )
    st.session_state.selected_price_symbols = sel_syms
    
    if sel_syms:
        data = []
        for s in sel_syms:
            r = fetch_api("/current_price", params={"symbol": s})
            if r: 
                data.append({
                    "Symbol": s, 
                    "Buy Price": r.get("Buy price", 0), 
                    "Sell Price": r.get("Sell price", 0)
                })
        
        if data:
            df = pd.DataFrame(data)
            
            # Підготовка даних для графіка з урахуванням логарифмічної шкали
            plot_df = df.copy()
            buy_col = "Buy Price"
            sell_col = "Sell Price"
            y_label = "Ціна"
            
            if use_log_scale:
                plot_df["log_buy"] = np.log1p(plot_df["Buy Price"])
                plot_df["log_sell"] = np.log1p(plot_df["Sell Price"])
                buy_col = "log_buy"
                sell_col = "log_sell"
                y_label = "Ціна (log scale)"
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=plot_df["Symbol"], 
                    y=plot_df[sell_col], 
                    name="Sell Price",
                    marker_color="red"
                ))
                fig.add_trace(go.Bar(
                    x=plot_df["Symbol"], 
                    y=plot_df[buy_col], 
                    name="Buy Price",
                    marker_color="green"
                ))
                fig.update_layout(
                    title="Поточні ціни покупки та продажу" + (" (логарифмічна шкала)" if use_log_scale else ""),
                    xaxis_title="Символ",
                    yaxis_title=y_label,
                    barmode="group",
                    height=400
                )
                st.plotly_chart(fig, width='stretch')
            
            with col2:
                st.subheader("Таблиця цін")
                st.dataframe(df, width='stretch', hide_index=True)
                
                # Розрахунок спреду
                df["Spread"] = df["Sell Price"] - df["Buy Price"]
                df["Spread %"] = ((df["Sell Price"] - df["Buy Price"]) / df["Buy Price"] * 100).round(4)
                
                st.subheader("Спред")
                st.dataframe(
                    df[["Symbol", "Spread", "Spread %"]],
                    width='stretch',
                    hide_index=True
                )
        else:
            st.warning("Не вдалося отримати дані про ціни")
    else:
        st.info("Виберіть хоча б один символ для відображення цін")

# TAB 6: REAL-TIME (Виправлено з використанням st.fragment)
with tab6:
    st.header("📡 Real-time відстеження цін")
    
    # Ініціалізація session state
    if "realtime_enabled" not in st.session_state:
        st.session_state.realtime_enabled = False
    if "selected_realtime_symbol" not in st.session_state:
        st.session_state.selected_realtime_symbol = default_symbol if default_symbol in symbols_list else (symbols_list[0] if symbols_list else "XBTUSD")
    
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        is_streaming = st.toggle(
            "🔴 Увімкнути Live Stream", 
            value=st.session_state.realtime_enabled,
            key="realtime_toggle"
        )
        st.session_state.realtime_enabled = is_streaming
    with col_ctrl2:
        # Визначаємо індекс для selectbox
        symbol_index = 0
        if st.session_state.selected_realtime_symbol in symbols_list:
            symbol_index = symbols_list.index(st.session_state.selected_realtime_symbol)
        
        target_symbol = st.selectbox(
            "Символ для моніторингу", 
            symbols_list, 
            index=symbol_index,
            key="realtime_symbol_select"
        )
        st.session_state.selected_realtime_symbol = target_symbol
    with col_ctrl3:
        if st.button("🗑️ Очистити графік", key="clear_realtime_history", width='stretch'):
            if target_symbol in st.session_state.price_history:
                st.session_state.price_history[target_symbol] = []

    # === ФРАГМЕНТ ДЛЯ АВТО-ОНОВЛЕННЯ ===
    # Використовуємо run_every=1 для автоматичного оновлення кожну секунду
    # Фрагмент оновлюється тільки цей блок, а не вся сторінка
    # Всередині перевіряємо streaming_enabled, щоб оновлювати дані тільки коли потрібно
    
    @st.fragment(run_every=1)
    def render_realtime_chart(symbol, streaming_enabled):
        # Отримуємо свіжі дані тільки якщо streaming увімкнено
        if streaming_enabled:
            price_data = fetch_api_no_cache("/current_price", params={"symbol": symbol})
            
            if price_data:
                now = datetime.now()
                # Ініціалізація, якщо немає
                if symbol not in st.session_state.price_history:
                    st.session_state.price_history[symbol] = []
                
                # Додаємо дані
                hist = st.session_state.price_history[symbol]
                # Уникаємо дублікатів (занадто частих запитів)
                if not hist or (now - hist[-1][0]).total_seconds() >= 0.5:
                    hist.append((
                        now, 
                        price_data.get("Buy price", 0), 
                        price_data.get("Sell price", 0)
                    ))
                    
                    # Тримаємо тільки останні 300 точок для продуктивності
                    if len(hist) > 300:
                        st.session_state.price_history[symbol] = hist[-300:]
        
        # Малюємо графік
        if symbol in st.session_state.price_history and st.session_state.price_history[symbol]:
            history = st.session_state.price_history[symbol]
            times = [h[0] for h in history]
            buys = [h[1] for h in history]
            sells = [h[2] for h in history]
            
            fig = go.Figure()
            
            # Лінія Buy Price
            fig.add_trace(go.Scatter(
                x=times, 
                y=buys, 
                mode='lines+markers', 
                name='Buy Price', 
                line=dict(color='green', width=2),
                marker=dict(size=4)
            ))
            
            # Лінія Sell Price
            fig.add_trace(go.Scatter(
                x=times, 
                y=sells, 
                mode='lines+markers', 
                name='Sell Price', 
                line=dict(color='red', width=2),
                marker=dict(size=4)
            ))
            
            # Додаємо спред як заливку
            fig.add_trace(go.Scatter(
                x=times,
                y=sells,
                mode='lines',
                name='Spread',
                fill='tonexty',
                fillcolor='rgba(255, 0, 0, 0.1)',
                line=dict(width=0),
                showlegend=False
            ))
            
            curr_buy = buys[-1] if buys else 0
            curr_sell = sells[-1] if sells else 0
            spread = curr_sell - curr_buy
            spread_pct = ((curr_sell - curr_buy) / curr_buy * 100) if curr_buy > 0 else 0
            
            fig.update_layout(
                title=f"Детальний графік цін для {symbol}",
                xaxis_title="Час",
                yaxis_title="Ціна",
                height=500,
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, width='stretch', key="realtime_chart")
            
            # Показуємо поточні значення
            if len(buys) > 0 and len(sells) > 0:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Поточна Buy Price", f"{curr_buy:,.2f}")
                with col2:
                    st.metric("Поточна Sell Price", f"{curr_sell:,.2f}")
                with col3:
                    st.metric("Спред", f"{spread:,.2f}")
                with col4:
                    st.metric("Спред %", f"{spread_pct:.4f}%")
        else:
            st.info(f"Очікування даних для {symbol}... {'(Увімкніть Live Stream)' if not streaming_enabled else ''}")

    # Виклик функції фрагмента
    render_realtime_chart(target_symbol, is_streaming)

# Footer
st.markdown("---")
st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")