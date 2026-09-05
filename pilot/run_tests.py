#!/usr/bin/env python
"""
Упрощенный запуск тестов
Запуск: python tests/run_tests.py
"""

import os
import sys

# Добавляем корневую директорию проекта в PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control.settings')

import django
django.setup()

# Теперь можно импортировать и запускать тесты
from test_api import APITestRunner

if __name__ == '__main__':
    runner = APITestRunner()
    runner.run()