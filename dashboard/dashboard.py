import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

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

# Отримання списку символів з топ обсягів
top_all = fetch_api("/top_n_highest_volumes", params={"top_n": 50})
if top_all and top_all.get("top_symbols"):
    symbols_list = [item["symbol"] for item in top_all["top_symbols"]]
else:
    # Fallback список символів
    symbols_list = ["XBTUSD", "ETHUSD", "ADAUSD", "SOLUSD", "DOGEUSD", "XRPUSD", "LINKUSD"]

# Значення за замовчуванням - перший символ зі списку
default_symbol = symbols_list[0] if symbols_list else "XBTUSD"

# Опція логарифмічної шкали
if "use_log_scale" not in st.session_state:
    st.session_state.use_log_scale = False

# Використовуємо query params для збереження стану табу
query_params = st.query_params
active_tab = query_params.get("tab", ["0"])[0] if "tab" in query_params else None

# JavaScript для збереження позиції скролу та активного табу
preserve_state_js = """
<script>
(function() {
    // Зберігаємо позицію скролу
    let scrollPosition = sessionStorage.getItem('scrollPosition');
    if (scrollPosition) {
        setTimeout(function() {
            window.scrollTo(0, parseInt(scrollPosition));
        }, 100);
    }
    
    // Зберігаємо позицію скролу під час скролу
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            sessionStorage.setItem('scrollPosition', window.pageYOffset || document.documentElement.scrollTop);
        }, 100);
    });
    
    // Функція для відновлення активного табу
    function restoreActiveTab() {
        const savedTab = sessionStorage.getItem('activeTab');
        const urlTab = new URL(window.location).searchParams.get('tab');
        const tabToRestore = urlTab !== null ? parseInt(urlTab) : (savedTab !== null ? parseInt(savedTab) : null);
        
        if (tabToRestore !== null) {
            // Шукаємо таб кнопки різними способами
            let tabButtons = document.querySelectorAll('[data-baseweb="tab"]');
            if (tabButtons.length === 0) {
                tabButtons = document.querySelectorAll('button[data-testid*="tab"]');
            }
            if (tabButtons.length === 0) {
                tabButtons = document.querySelectorAll('button[role="tab"]');
            }
            
            if (tabButtons.length > tabToRestore && tabButtons[tabToRestore]) {
                // Перевіряємо, чи таб вже активний
                const isActive = tabButtons[tabToRestore].getAttribute('aria-selected') === 'true' ||
                                tabButtons[tabToRestore].classList.contains('st-emotion-cache-1in6wow');
                
                if (!isActive) {
                    tabButtons[tabToRestore].click();
                }
            }
        }
    }
    
    // Зберігаємо активний таб при кліку
    function setupTabListeners() {
        let tabButtons = document.querySelectorAll('[data-baseweb="tab"]');
        if (tabButtons.length === 0) {
            tabButtons = document.querySelectorAll('button[data-testid*="tab"]');
        }
        if (tabButtons.length === 0) {
            tabButtons = document.querySelectorAll('button[role="tab"]');
        }
        
        tabButtons.forEach((tab, index) => {
            // Видаляємо старі слухачі
            const newTab = tab.cloneNode(true);
            tab.parentNode.replaceChild(newTab, tab);
            
            newTab.addEventListener('click', function() {
                sessionStorage.setItem('activeTab', index.toString());
                const url = new URL(window.location);
                url.searchParams.set('tab', index.toString());
                window.history.replaceState({}, '', url);
            });
        });
    }
    
    // Відновлюємо таб кілька разів для надійності
    setTimeout(restoreActiveTab, 100);
    setTimeout(restoreActiveTab, 300);
    setTimeout(restoreActiveTab, 500);
    setTimeout(setupTabListeners, 200);
    
    // Спостерігаємо за змінами DOM для Streamlit rerun
    const observer = new MutationObserver(function(mutations) {
        let hasTabs = document.querySelectorAll('[data-baseweb="tab"]').length > 0 ||
                     document.querySelectorAll('button[data-testid*="tab"]').length > 0 ||
                     document.querySelectorAll('button[role="tab"]').length > 0;
        
        if (hasTabs) {
            setTimeout(setupTabListeners, 100);
            setTimeout(restoreActiveTab, 200);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
</script>
"""
st.markdown(preserve_state_js, unsafe_allow_html=True)

use_log_scale = st.sidebar.checkbox(
    "📊 Використовувати логарифмічну шкалу", 
    value=st.session_state.use_log_scale, 
    help="Корисно для даних з великою різницею між значеннями",
    key="log_scale_checkbox"
)
st.session_state.use_log_scale = use_log_scale

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
        st.subheader("Кількість транзакцій (загальна за 6 годин)")
        transactions_data = fetch_api("/transactions_count_last_6_hours")
        
        if transactions_data and transactions_data.get("count"):
            # Новий формат: загальна сума для кожного символу
            all_data = []
            for symbol, data in transactions_data["count"].items():
                all_data.append({
                    "symbol": symbol,
                    "total_transaction_count": data.get("total_transaction_count", 0)
                })
            
            if all_data:
                df_transactions = pd.DataFrame(all_data)
                
                # Завжди показуємо всі монети
                df_filtered = df_transactions
                
                if not df_filtered.empty:
                    # Підготовка даних для графіка
                    plot_data = df_filtered.copy()
                    y_column = "total_transaction_count"
                    y_label = "Кількість транзакцій"
                    
                    if use_log_scale:
                        # Додаємо 1 перед логарифмуванням, щоб уникнути log(0)
                        plot_data["log_value"] = np.log1p(plot_data[y_column])
                        y_column = "log_value"
                        y_label = "Кількість транзакцій (log scale)"
                    
                    fig = px.bar(
                        plot_data,
                        x="symbol",
                        y=y_column,
                        title="Загальна кількість транзакцій за 6 годин" + (" (логарифмічна шкала)" if use_log_scale else ""),
                        labels={"symbol": "Символ", y_column: y_label},
                        color=y_column,
                        color_continuous_scale="viridis"
                    )
                    fig.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Таблиця з даними
                    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
                else:
                    st.info("Немає даних про транзакції")
            else:
                st.warning("Немає даних про транзакції")
        else:
            st.warning("Не вдалося отримати дані про транзакції")
    
    with col2:
        st.subheader("Обсяг торгівлі (загальний за 6 годин)")
        volume_data = fetch_api("/trade_volume_last_6_hours")
        
        if volume_data and volume_data.get("count"):
            # Новий формат: загальна сума для кожного символу
            all_data = []
            for symbol, data in volume_data["count"].items():
                all_data.append({
                    "symbol": symbol,
                    "total_trade_volume": data.get("total_trade_volume", 0.0)
                })
            
            if all_data:
                df_volume = pd.DataFrame(all_data)
                
                # Завжди показуємо всі монети
                df_filtered = df_volume
                
                if not df_filtered.empty:
                    # Підготовка даних для графіка
                    plot_data = df_filtered.copy()
                    y_column = "total_trade_volume"
                    y_label = "Обсяг торгівлі"
                    
                    if use_log_scale:
                        # Додаємо 1 перед логарифмуванням, щоб уникнути log(0)
                        plot_data["log_value"] = np.log1p(plot_data[y_column])
                        y_column = "log_value"
                        y_label = "Обсяг торгівлі (log scale)"
                    
                    fig = px.bar(
                        plot_data,
                        x="symbol",
                        y=y_column,
                        title="Загальний обсяг торгівлі за 6 годин" + (" (логарифмічна шкала)" if use_log_scale else ""),
                        labels={"symbol": "Символ", y_column: y_label},
                        color=y_column,
                        color_continuous_scale="plasma"
                    )
                    fig.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Таблиця з даними
                    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
                else:
                    st.info("Немає даних про обсяг торгівлі")
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
            
            # Завжди показуємо всі монети
            df_filtered = df_stats
            
            if not df_filtered.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Підготовка даних для графіка транзакцій
                    plot_data1 = df_filtered.copy()
                    y_column1 = "transaction_count"
                    y_label1 = "Кількість"
                    
                    if use_log_scale:
                        plot_data1["log_transaction_count"] = np.log1p(plot_data1[y_column1])
                        y_column1 = "log_transaction_count"
                        y_label1 = "Кількість (log scale)"
                    
                    fig1 = px.line(
                        plot_data1,
                        x="hour_start",
                        y=y_column1,
                        color="symbol",
                        title="Кількість транзакцій" + (" (логарифмічна шкала)" if use_log_scale else ""),
                        labels={"hour_start": "Час", y_column1: y_label1}
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    # Підготовка даних для графіка обсягу
                    plot_data2 = df_filtered.copy()
                    y_column2 = "total_trade_volume"
                    y_label2 = "Обсяг"
                    
                    if use_log_scale:
                        plot_data2["log_volume"] = np.log1p(plot_data2[y_column2])
                        y_column2 = "log_volume"
                        y_label2 = "Обсяг (log scale)"
                    
                    # Сортуємо дані для правильного відображення
                    plot_data2 = plot_data2.sort_values(["symbol", "hour_start"])
                    
                    fig2 = px.line(
                        plot_data2,
                        x="hour_start",
                        y=y_column2,
                        color="symbol",
                        title="Обсяг торгівлі" + (" (логарифмічна шкала)" if use_log_scale else ""),
                        labels={"hour_start": "Час", y_column2: y_label2},
                        markers=True
                    )
                    # Додаємо заповнення під лінією для кращої візуалізації
                    fig2.update_traces(fill='tozeroy', mode='lines+markers')
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Таблиця з даними
                st.subheader("Детальна таблиця")
                st.dataframe(
                    df_filtered.sort_values("hour_start", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Немає даних")
        else:
            st.warning("Немає даних")
    else:
        st.warning("Не вдалося отримати статистику")

# TAB 3: Детальний аналіз
with tab3:
    st.header("Детальний аналіз транзакцій")
    
    # Ініціалізація session state для збереження результатів
    if "detail_analysis_result" not in st.session_state:
        st.session_state.detail_analysis_result = None
    if "detail_symbol" not in st.session_state:
        st.session_state.detail_symbol = default_symbol
    if "detail_minutes" not in st.session_state:
        st.session_state.detail_minutes = 5
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Визначаємо індекс для selectbox
        symbol_options = symbols_list if symbols_list else ["XBTUSD"]
        default_index = 0
        if st.session_state.detail_symbol in symbol_options:
            default_index = symbol_options.index(st.session_state.detail_symbol)
        symbol_input = st.selectbox("Символ", options=symbol_options, index=default_index, key="detail_symbol_select")
    
    with col2:
        n_minutes = st.number_input("Кількість хвилин", min_value=1, max_value=1440, value=st.session_state.detail_minutes, key="detail_minutes_input")
    
    if st.button("Отримати дані", type="primary", key="get_detail_data"):
        if symbol_input:
            transactions_count = fetch_api(
                "/transactions_in_last_n_min",
                params={"symbol": symbol_input, "n_minutes": n_minutes}
            )
            
            # Зберігаємо результат в session state
            st.session_state.detail_analysis_result = transactions_count
            st.session_state.detail_symbol = symbol_input
            st.session_state.detail_minutes = n_minutes
    
    # Відображаємо результат, якщо він є
    if st.session_state.detail_analysis_result:
        transactions_count = st.session_state.detail_analysis_result
        symbol_display = st.session_state.detail_symbol
        minutes_display = st.session_state.detail_minutes
        
        if transactions_count:
            st.success(f"✅ Символ: **{symbol_display}**")
            st.metric(
                "Кількість транзакцій",
                transactions_count.get("number_of_trades", 0)
            )
            
            # Візуалізація
            st.subheader("Інформація")
            st.info(
                f"За останні **{minutes_display} хвилин** для символу **{symbol_display}** "
                f"було виконано **{transactions_count.get('number_of_trades', 0)}** транзакцій."
            )
        else:
            st.error("Не вдалося отримати дані")

# TAB 4: Топ обсяги
with tab4:
    st.header("Топ символів за обсягом торгівлі")
    
    # Ініціалізація session state для збереження значення slider
    if "top_n_value" not in st.session_state:
        st.session_state.top_n_value = 3
    
    top_n = st.slider(
        "Кількість топ символів", 
        min_value=1, 
        max_value=5, 
        value=st.session_state.top_n_value,
        key="top_n_slider"
    )
    
    # Оновлюємо session state
    st.session_state.top_n_value = top_n
    
    top_volumes = fetch_api("/top_n_highest_volumes", params={"top_n": top_n})
    
    if top_volumes and top_volumes.get("top_symbols"):
        df_top = pd.DataFrame(top_volumes["top_symbols"])
        
        # Підготовка даних для графіка
        plot_data = df_top.copy()
        y_column = "total_volume"
        y_label = "Обсяг торгівлі"
        
        if use_log_scale:
            plot_data["log_volume"] = np.log1p(plot_data[y_column])
            y_column = "log_volume"
            y_label = "Обсяг торгівлі (log scale)"
        
        # Графік
        fig = px.bar(
            plot_data,
            x="symbol",
            y=y_column,
            title=f"Топ {top_n} символів за обсягом (остання година)" + (" (логарифмічна шкала)" if use_log_scale else ""),
            labels={"symbol": "Символ", y_column: y_label},
            color=y_column,
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
    
    # Ініціалізація session state для збереження вибраних символів
    if "selected_price_symbols" not in st.session_state:
        st.session_state.selected_price_symbols = [default_symbol] if default_symbol in symbols_list else []
    
    # Мультиселект для вибору символів
    selected_symbols = st.multiselect(
        "Виберіть символи",
        options=symbols_list,
        default=st.session_state.selected_price_symbols,
        key="price_symbols_selector"
    )
    
    # Оновлюємо session state при зміні вибору
    if selected_symbols != st.session_state.selected_price_symbols:
        st.session_state.selected_price_symbols = selected_symbols
    
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
            
            # Підготовка даних для графіка з урахуванням логарифмічної шкали
            plot_data = df_prices.copy()
            sell_col = "Sell Price"
            buy_col = "Buy Price"
            y_label = "Ціна"
            
            if use_log_scale:
                plot_data["log_sell_price"] = np.log1p(plot_data[sell_col])
                plot_data["log_buy_price"] = np.log1p(plot_data[buy_col])
                sell_col = "log_sell_price"
                buy_col = "log_buy_price"
                y_label = "Ціна (log scale)"
            
            # Візуалізація
            col1, col2 = st.columns(2)
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=plot_data["Symbol"],
                    y=plot_data[sell_col],
                    name="Sell Price",
                    marker_color="red"
                ))
                fig.add_trace(go.Bar(
                    x=plot_data["Symbol"],
                    y=plot_data[buy_col],
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

