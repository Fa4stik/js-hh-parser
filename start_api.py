#!/usr/bin/env python3
"""
Скрипт для запуска API извлечения навыков из вакансий
"""

import os
import sys
from pathlib import Path
import subprocess


def check_requirements():
    """Проверяет наличие зависимостей"""
    try:
        import fastapi
        import uvicorn
        import transformers
        import torch
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствуют зависимости: {e}")
        print("📦 Установите зависимости: pip install -r requirements.txt")
        return False


def main():
    """Основная функция запуска"""
    print("🚀 Запуск API для извлечения навыков из вакансий\n")
    
    # Проверяем зависимости
    if not check_requirements():
        return
    
    # Переходим в директорию с API
    api_dir = Path(__file__).parent / "src" / "ai"
    
    if not api_dir.exists():
        print(f"❌ Директория API не найдена: {api_dir}")
        return
    
    # Запускаем API
    print(f"📂 Переходим в: {api_dir}")
    print("🌐 Запускаем сервер на http://localhost:8000")
    print("📖 Документация доступна на http://localhost:8000/docs")
    print("⚠️  Первый запрос может занять время (загрузка модели)")
    print("\n" + "="*60 + "\n")
    
    try:
        # Запускаем uvicorn из нужной директории
        os.chdir(api_dir)
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "qwen:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")


if __name__ == "__main__":
    main() 