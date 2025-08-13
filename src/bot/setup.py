#!/usr/bin/env python3
"""
Скрипт установки для бота обработки вакансий.
Устанавливает необходимые зависимости и проверяет конфигурацию.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

# Список необходимых пакетов
REQUIRED_PACKAGES = [
    'pandas',
    'requests', 
    'beautifulsoup4',
    'python-telegram-bot',
    'openpyxl',
    'xlrd',
    'telegram'
]

def check_python_version():
    """Проверяет версию Python."""
    print("🐍 Проверка версии Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    
    print(f"✅ Python версия: {sys.version.split()[0]}")
    return True

def check_virtual_env():
    """Проверяет, что мы находимся в виртуальном окружении."""
    print("\n🔍 Проверка виртуального окружения...")
    
    # Проверяем переменные окружения, которые указывают на активное виртуальное окружение
    venv_indicators = ['VIRTUAL_ENV', 'CONDA_DEFAULT_ENV']
    
    for indicator in venv_indicators:
        if os.environ.get(indicator):
            print(f"✅ Виртуальное окружение активно: {os.environ.get(indicator)}")
            return True
    
    # Дополнительная проверка через sys.prefix
    if sys.prefix != sys.base_prefix:
        print("✅ Виртуальное окружение активно")
        return True
    
    print("⚠️  Виртуальное окружение не активно")
    print("Рекомендуется активировать виртуальное окружение: source env/bin/activate")
    
    response = input("Продолжить установку без виртуального окружения? (y/N): ")
    return response.lower() in ['y', 'yes']

def install_package(package):
    """Устанавливает пакет через pip."""
    try:
        print(f"📦 Устанавливаю {package}...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {package} установлен успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package}: {e}")
        print(f"Stderr: {e.stderr}")
        return False

def check_package_installed(package):
    """Проверяет, установлен ли пакет."""
    try:
        __import__(package.replace('-', '_'))
        return True
    except ImportError:
        return False

def install_dependencies():
    """Устанавливает все необходимые зависимости."""
    print("\n📚 Установка зависимостей...")
    
    failed_packages = []
    
    for package in REQUIRED_PACKAGES:
        # Проверяем, не установлен ли уже пакет
        package_import_name = package.replace('-', '_')
        if package == 'python-telegram-bot':
            package_import_name = 'telegram'
        elif package == 'beautifulsoup4':
            package_import_name = 'bs4'
        
        if check_package_installed(package_import_name):
            print(f"✅ {package} уже установлен")
            continue
        
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Не удалось установить: {', '.join(failed_packages)}")
        return False
    
    print("\n✅ Все зависимости установлены успешно")
    return True

def check_telegram_api():
    """Проверяет настройки Telegram API."""
    print("\n🤖 Проверка настроек Telegram API...")
    
    try:
        from meta import BOT_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH
        
        # Проверяем BOT_TOKEN
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ BOT_TOKEN не настроен в meta.py")
            return False
        
        # Простая проверка формата токена
        if not BOT_TOKEN.count(':') == 1:
            print("❌ BOT_TOKEN имеет неверный формат")
            return False
        
        print("✅ BOT_TOKEN настроен")
        
        # Проверяем API_ID и API_HASH
        if not TELEGRAM_API_ID or TELEGRAM_API_ID == "YOUR_API_ID":
            print("⚠️  TELEGRAM_API_ID не настроен (нужен для расширенного функционала)")
        else:
            print("✅ TELEGRAM_API_ID настроен")
        
        if not TELEGRAM_API_HASH or TELEGRAM_API_HASH == "YOUR_API_HASH":
            print("⚠️  TELEGRAM_API_HASH не настроен (нужен для расширенного функционала)")
        else:
            print("✅ TELEGRAM_API_HASH настроен")
        
        # Проверяем доступность Telegram API
        print("🌐 Проверяю доступность Telegram API...")
        test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_username = bot_info['result'].get('username', 'неизвестно')
                print(f"✅ Telegram API доступен. Бот: @{bot_username}")
                return True
            else:
                print("❌ Неверный BOT_TOKEN")
                return False
        else:
            print(f"❌ Ошибка подключения к Telegram API: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ Не удалось импортировать настройки из meta.py")
        return False
    except requests.RequestException as e:
        print(f"❌ Ошибка сети при проверке Telegram API: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def check_files():
    """Проверяет наличие необходимых файлов."""
    print("\n📁 Проверка файлов...")
    
    required_files = [
        'meta.py',
        'merged_vacs.xlsx'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file} найден")
    
    if missing_files:
        print(f"❌ Отсутствующие файлы: {', '.join(missing_files)}")
        return False
    
    # Создаем директорию для обработанных файлов
    process_dir = "process_vacs"
    if not os.path.exists(process_dir):
        os.makedirs(process_dir)
        print(f"✅ Создана директория {process_dir}")
    else:
        print(f"✅ Директория {process_dir} существует")
    
    return True

def main():
    """Основная функция установки."""
    print("🚀 Установка бота для обработки вакансий")
    print("=" * 50)
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    # Проверяем виртуальное окружение
    if not check_virtual_env():
        sys.exit(1)
    
    # Проверяем файлы
    if not check_files():
        print("\n❌ Установка прервана из-за отсутствующих файлов")
        sys.exit(1)
    
    # Устанавливаем зависимости
    if not install_dependencies():
        print("\n❌ Установка прервана из-за ошибок с зависимостями")
        sys.exit(1)
    
    # Проверяем Telegram API
    telegram_ok = check_telegram_api()
    
    print("\n" + "=" * 50)
    
    if telegram_ok:
        print("🎉 Установка завершена успешно!")
        print("\nДля запуска:")
        print("• Обработка вакансий: python process_vacancies.py")
        print("• Telegram бот: python main.py")
    else:
        print("⚠️  Установка завершена с предупреждениями")
        print("Необходимо настроить Telegram API в файле meta.py")
    
    print("\n📖 Дополнительная информация:")
    print("• Файлы обработки сохраняются в папку process_vacs/")
    print("• Логи работы бота выводятся в консоль")
    print("• Для остановки используйте Ctrl+C")

if __name__ == "__main__":
    main()
