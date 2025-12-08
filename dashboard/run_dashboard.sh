#!/bin/bash

# Скрипт для запуску Streamlit Dashboard

echo "🚀 Запуск Trading Dashboard..."

# Перевірка чи встановлені залежності
if ! command -v streamlit &> /dev/null; then
    echo "📦 Встановлення залежностей..."
    pip install -r dashboard_requirements.txt
fi

# Запуск dashboard
echo "📊 Запуск Streamlit на http://localhost:8501"
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

