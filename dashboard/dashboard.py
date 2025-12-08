import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Конфігурація сторінки
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API базовий URL
API_BASE_URL = st.sidebar.text_input("API URL", value="http://localhost:8000", help="Base URL для FastAPI")

# Функція для виклику API
@st.cache_data(ttl=30)  # Кешування на 30 секунд
def fetch_api(endpoint, params=None):
    """Викликає API ендпоінт і повертає JSON відповідь"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Помилка при виклику API: {e}")
        return None

# Заголовок
st.title("📊 Trading Analytics Dashboard")
st.markdown("---")

# Health Status
with st.expander("🏥 Health Status", expanded=False):
    health_data = fetch_api("/health")
    if health_data:
        st.success(f"✅ API Status: {health_data.get('status', 'Unknown')}")
    else:
        st.error("❌ API недоступний")

# Основні метрики
col1, col2, col3, col4 = st.columns(4)

# Топ символів за обсягом (для швидкого огляду)
top_volumes = fetch_api("/top_n_highest_volumes", params={"top_n": 1})
if top_volumes and top_volumes.get("top_symbols"):
    top_symbol = top_volumes["top_symbols"][0]
    with col1:
        st.metric("🏆 Топ символ", top_symbol.get("symbol", "N/A"))
    with col2:
        st.metric("💰 Обсяг", f"{top_symbol.get('total_volume', 0):,.2f}")

# Транзакції за останні 5 хвилин (якщо є символ)
with col3:
    st.metric("⏱️ Оновлено", datetime.now().strftime("%H:%M:%S"))

# Sidebar для налаштувань
st.sidebar.header("⚙️ Налаштування")

# Автоматичне оновлення
auto_refresh = st.sidebar.checkbox("🔄 Автоматичне оновлення", value=False)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Інтервал оновлення (секунди)", min_value=5, max_value=300, value=30)
    time.sleep(refresh_interval)
    st.rerun()

# Отримання списку символів з топ обсягів
top_all = fetch_api("/top_n_highest_volumes", params={"top_n": 50})
if top_all and top_all.get("top_symbols"):
    symbols_list = [item["symbol"] for item in top_all["top_symbols"]]
else:
    # Fallback список символів
    symbols_list = ["XBTUSD", "ETHUSD", "ADAUSD", "SOLUSD", "DOGEUSD", "XRPUSD", "LINKUSD"]

# Вибір символу для детального аналізу
selected_symbol = st.sidebar.selectbox("Виберіть символ", options=symbols_list if symbols_list else ["XBTUSD"])

# Tabs для різних секцій
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Статистика за 6 годин",
    "📊 Статистика за 12 годин",
    "🔍 Детальний аналіз",
    "🏆 Топ обсяги",
    "💵 Поточні ціни"
])

# TAB 1: Статистика за 6 годин
with tab1:
    st.header("Статистика за останні 6 годин")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Кількість транзакцій")
        transactions_data = fetch_api("/transactions_count_last_6_hours")
        
        if transactions_data and transactions_data.get("count"):
            # Підготовка даних для графіка
            all_data = []
            for symbol, values in transactions_data["count"].items():
                for item in values:
                    all_data.append({
                        "symbol": symbol,
                        "hour_start": pd.to_datetime(item["hour_start"]),
                        "transaction_count": item["transaction_count"]
                    })
            
            if all_data:
                df_transactions = pd.DataFrame(all_data)
                
                # Фільтр за символом
                if selected_symbol:
                    df_filtered = df_transactions[df_transactions["symbol"] == selected_symbol]
                else:
                    df_filtered = df_transactions
                
                if not df_filtered.empty:
                    fig = px.line(
                        df_filtered,
                        x="hour_start",
                        y="transaction_count",
                        color="symbol",
                        title="Кількість транзакцій по годинах",
                        labels={"hour_start": "Час", "transaction_count": "Кількість транзакцій"}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Немає даних для вибраного символу")
            else:
                st.warning("Немає даних про транзакції")
        else:
            st.warning("Не вдалося отримати дані про транзакції")
    
    with col2:
        st.subheader("Обсяг торгівлі")
        volume_data = fetch_api("/trade_volume_last_6_hours")
        
        if volume_data and volume_data.get("count"):
            all_data = []
            for symbol, values in volume_data["count"].items():
                for item in values:
                    all_data.append({
                        "symbol": symbol,
                        "hour_start": pd.to_datetime(item["hour_start"]),
                        "total_trade_volume": item["total_trade_volume"]
                    })
            
            if all_data:
                df_volume = pd.DataFrame(all_data)
                
                if selected_symbol:
                    df_filtered = df_volume[df_volume["symbol"] == selected_symbol]
                else:
                    df_filtered = df_volume
                
                if not df_filtered.empty:
                    fig = px.bar(
                        df_filtered,
                        x="hour_start",
                        y="total_trade_volume",
                        color="symbol",
                        title="Обсяг торгівлі по годинах",
                        labels={"hour_start": "Час", "total_trade_volume": "Обсяг торгівлі"}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Немає даних для вибраного символу")
            else:
                st.warning("Немає даних про обсяг торгівлі")
        else:
            st.warning("Не вдалося отримати дані про обсяг торгівлі")

# TAB 2: Статистика за 12 годин
with tab2:
    st.header("Комплексна статистика за останні 12 годин")
    
    hourly_stats = fetch_api("/hourly_stats_last_12_hours")
    
    if hourly_stats and hourly_stats.get("stats"):
        all_data = []
        for symbol, values in hourly_stats["stats"].items():
            for item in values:
                all_data.append({
                    "symbol": symbol,
                    "hour_start": pd.to_datetime(item["hour_start"]),
                    "transaction_count": item["transaction_count"],
                    "total_trade_volume": item["total_trade_volume"]
                })
        
        if all_data:
            df_stats = pd.DataFrame(all_data)
            
            # Фільтр за символом
            if selected_symbol:
                df_filtered = df_stats[df_stats["symbol"] == selected_symbol]
            else:
                df_filtered = df_stats
            
            if not df_filtered.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig1 = px.line(
                        df_filtered,
                        x="hour_start",
                        y="transaction_count",
                        color="symbol",
                        title="Кількість транзакцій",
                        labels={"hour_start": "Час", "transaction_count": "Кількість"}
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    fig2 = px.area(
                        df_filtered,
                        x="hour_start",
                        y="total_trade_volume",
                        color="symbol",
                        title="Обсяг торгівлі",
                        labels={"hour_start": "Час", "total_trade_volume": "Обсяг"}
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Таблиця з даними
                st.subheader("Детальна таблиця")
                st.dataframe(
                    df_filtered.sort_values("hour_start", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Немає даних для вибраного символу")
        else:
            st.warning("Немає даних")
    else:
        st.warning("Не вдалося отримати статистику")

# TAB 3: Детальний аналіз
with tab3:
    st.header("Детальний аналіз транзакцій")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol_input = st.text_input("Символ", value=selected_symbol)
    
    with col2:
        n_minutes = st.number_input("Кількість хвилин", min_value=1, max_value=1440, value=5)
    
    if st.button("Отримати дані", type="primary"):
        if symbol_input:
            transactions_count = fetch_api(
                "/transactions_in_last_n_min",
                params={"symbol": symbol_input, "n_minutes": n_minutes}
            )
            
            if transactions_count:
                st.success(f"✅ Символ: **{transactions_count.get('symbol')}**")
                st.metric(
                    "Кількість транзакцій",
                    transactions_count.get("number_of_trades", 0)
                )
                
                # Візуалізація
                st.subheader("Інформація")
                st.info(
                    f"За останні **{n_minutes} хвилин** для символу **{symbol_input}** "
                    f"було виконано **{transactions_count.get('number_of_trades', 0)}** транзакцій."
                )
            else:
                st.error("Не вдалося отримати дані")

# TAB 4: Топ обсяги
with tab4:
    st.header("Топ символів за обсягом торгівлі")
    
    top_n = st.slider("Кількість топ символів", min_value=1, max_value=20, value=10)
    
    top_volumes = fetch_api("/top_n_highest_volumes", params={"top_n": top_n})
    
    if top_volumes and top_volumes.get("top_symbols"):
        df_top = pd.DataFrame(top_volumes["top_symbols"])
        
        # Графік
        fig = px.bar(
            df_top,
            x="symbol",
            y="total_volume",
            title=f"Топ {top_n} символів за обсягом (остання година)",
            labels={"symbol": "Символ", "total_volume": "Обсяг торгівлі"},
            color="total_volume",
            color_continuous_scale="viridis"
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Таблиця
        st.subheader("Детальна таблиця")
        df_top_display = df_top.copy()
        df_top_display["total_volume"] = df_top_display["total_volume"].apply(lambda x: f"{x:,.2f}")
        df_top_display.index = range(1, len(df_top_display) + 1)
        st.dataframe(df_top_display, use_container_width=True)
    else:
        st.warning("Не вдалося отримати дані про топ обсяги")

# TAB 5: Поточні ціни
with tab5:
    st.header("Поточні ціни символів")
    
    # Мультиселект для вибору символів
    selected_symbols = st.multiselect(
        "Виберіть символи",
        options=symbols_list,
        default=[selected_symbol] if selected_symbol in symbols_list else []
    )
    
    if selected_symbols:
        prices_data = []
        for symbol in selected_symbols:
            price_data = fetch_api("/current_price", params={"symbol": symbol})
            if price_data:
                prices_data.append(price_data)
        
        if prices_data:
            # Створення DataFrame
            df_prices = pd.DataFrame(prices_data)
            df_prices.columns = ["Symbol", "Sell Price", "Buy Price"]
            
            # Візуалізація
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df_prices["Symbol"],
                    y=df_prices["Sell Price"],
                    name="Sell Price",
                    marker_color="red"
                ))
                fig.add_trace(go.Bar(
                    x=df_prices["Symbol"],
                    y=df_prices["Buy Price"],
                    name="Buy Price",
                    marker_color="green"
                ))
                fig.update_layout(
                    title="Поточні ціни покупки та продажу",
                    xaxis_title="Символ",
                    yaxis_title="Ціна",
                    barmode="group",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Таблиця з цінами
                st.subheader("Таблиця цін")
                st.dataframe(df_prices, use_container_width=True, hide_index=True)
                
                # Розрахунок спреду
                df_prices["Spread"] = df_prices["Sell Price"] - df_prices["Buy Price"]
                df_prices["Spread %"] = ((df_prices["Sell Price"] - df_prices["Buy Price"]) / df_prices["Buy Price"] * 100).round(2)
                
                st.subheader("Спред")
                st.dataframe(
                    df_prices[["Symbol", "Spread", "Spread %"]],
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.warning("Не вдалося отримати дані про ціни")
    else:
        st.info("Виберіть хоча б один символ для відображення цін")

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: gray;'>"
    f"Останнє оновлення: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"API: {API_BASE_URL}"
    f"</div>",
    unsafe_allow_html=True
)

