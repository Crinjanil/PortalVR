#!/bin/bash

echo "Building the project..."

# Установка зависимостей
pip install -r requirements.txt

# Сбор статических файлов
python manage.py collectstatic --no-input

# Применение миграций базы данных
python manage.py migrate

echo "Build finished."
