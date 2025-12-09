#!/bin/bash

# Скрипт для перегляду таблиці current_price в Cassandra

CONTAINER_NAME="cassandra"
KEYSPACE="orders"
TABLE="current_price"

echo "Підключення до Cassandra та перегляд таблиці $KEYSPACE.$TABLE..."
echo ""

# Перевіряємо, чи контейнер запущений
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Помилка: Контейнер '$CONTAINER_NAME' не запущений"
    exit 1
fi

# Виконуємо запит до Cassandra
docker exec -it $CONTAINER_NAME cqlsh -e "
USE $KEYSPACE;
SELECT * FROM $TABLE;
"

echo ""
echo "Готово!"

