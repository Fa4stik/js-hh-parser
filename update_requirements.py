#!/usr/bin/env python3
"""
Скрипт для обновления зависимостей для работы с Qwen3-8B
"""

import subprocess
import sys
import importlib.util


def check_package_version(package_name, min_version):
    """Проверяет версию пакета"""
    try:
        if package_name == "transformers":
            import transformers
            current_version = transformers.__version__
        elif package_name == "torch":
            import torch
            current_version = torch.__version__
        elif package_name == "accelerate":
            import accelerate
            current_version = accelerate.__version__
        else:
            return False, "Unknown package"
        
        # Простая проверка версии
        current_major = int(current_version.split('.')[0])
        current_minor = int(current_version.split('.')[1])
        min_major = int(min_version.split('.')[0])
        min_minor = int(min_version.split('.')[1])
        
        if current_major > min_major or (current_major == min_major and current_minor >= min_minor):
            return True, current_version
        else:
            return False, current_version
            
    except ImportError:
        return False, "Not installed"
    except Exception as e:
        return False, str(e)


def install_requirements():
    """Устанавливает обновленные зависимости"""
    print("🔄 Обновление зависимостей для Qwen3-8B...")
    
    # Проверяем текущие версии
    packages = {
        "transformers": "4.51.0",
        "torch": "2.1.0", 
        "accelerate": "0.24.1"
    }
    
    needs_update = []
    
    for package, min_version in packages.items():
        is_ok, version = check_package_version(package, min_version)
        if is_ok:
            print(f"✅ {package} {version} - OK")
        else:
            print(f"❌ {package} {version} - требует обновления (минимум {min_version})")
            needs_update.append(package)
    
    if not needs_update:
        print("✅ Все зависимости актуальны!")
        return True
    
    print(f"\n📦 Обновляем пакеты: {', '.join(needs_update)}")
    
    try:
        # Обновляем requirements.txt
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ], check=True)
        
        print("✅ Зависимости обновлены успешно!")
        
        # Проверяем еще раз
        print("\n🔍 Проверяем обновленные версии:")
        for package, min_version in packages.items():
            is_ok, version = check_package_version(package, min_version)
            status = "✅" if is_ok else "❌"
            print(f"{status} {package} {version}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при обновлении: {e}")
        return False


def test_qwen3_compatibility():
    """Тестирует совместимость с Qwen3"""
    print("\n🧪 Тестирование совместимости с Qwen3...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        # Пробуем загрузить только токенайзер для проверки
        print("📦 Тестируем загрузку токенайзера...")
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
        
        # Проверяем наличие apply_chat_template
        if hasattr(tokenizer, 'apply_chat_template'):
            print("✅ apply_chat_template доступен")
        else:
            print("❌ apply_chat_template не найден")
            return False
        
        # Тестируем apply_chat_template
        messages = [{"role": "user", "content": "Test"}]
        try:
            text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True,
                enable_thinking=False
            )
            print("✅ apply_chat_template работает корректно")
        except Exception as e:
            print(f"❌ Ошибка в apply_chat_template: {e}")
            return False
        
        print("✅ Qwen3 совместимость подтверждена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка совместимости: {e}")
        return False


def main():
    """Основная функция"""
    print("🚀 Обновление системы для работы с Qwen3-8B\n")
    
    # Обновляем зависимости
    if not install_requirements():
        print("❌ Не удалось обновить зависимости")
        return False
    
    # Тестируем совместимость
    if not test_qwen3_compatibility():
        print("❌ Проблемы с совместимостью Qwen3")
        return False
    
    print("\n🎉 Система готова к работе с Qwen3-8B!")
    print("📋 Теперь вы можете запустить API:")
    print("   python start_api.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 