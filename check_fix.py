#!/usr/bin/env python3
"""
Скрипт для проверки исправления ошибки Qwen3
"""

def check_transformers_version():
    """Проверяет версию transformers"""
    try:
        import transformers
        version = transformers.__version__
        
        # Проверяем версию
        major, minor = version.split('.')[:2]
        major, minor = int(major), int(minor)
        
        if major > 4 or (major == 4 and minor >= 51):
            print(f"✅ transformers {version} - OK (>= 4.51.0)")
            return True
        else:
            print(f"❌ transformers {version} - УСТАРЕЛА (нужна >= 4.51.0)")
            return False
            
    except ImportError:
        print("❌ transformers не установлен")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке transformers: {e}")
        return False


def check_qwen3_tokenizer():
    """Проверяет загрузку токенайзера Qwen3"""
    try:
        from transformers import AutoTokenizer
        
        print("📦 Проверяем загрузку токенайзера Qwen3-8B...")
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")
        
        # Проверяем apply_chat_template
        if hasattr(tokenizer, 'apply_chat_template'):
            print("✅ apply_chat_template доступен")
            
            # Тестируем его
            messages = [{"role": "user", "content": "Тест"}]
            text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True,
                enable_thinking=False
            )
            print("✅ apply_chat_template работает")
            return True
        else:
            print("❌ apply_chat_template недоступен")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if "Qwen2Tokenizer" in error_msg:
            print("❌ Ошибка: Tokenizer class Qwen2Tokenizer does not exist")
            print("🔧 Решение: Обновите transformers до >= 4.51.0")
            print("📋 Команда: pip install transformers>=4.51.0 --upgrade")
            return False
        else:
            print(f"❌ Ошибка при загрузке токенайзера: {e}")
            return False


def main():
    """Основная функция проверки"""
    print("🔍 Проверка исправления ошибки Qwen3...\n")
    
    # Проверяем версию transformers
    if not check_transformers_version():
        print("\n❌ Исправление не завершено!")
        print("🔧 Выполните: pip install transformers>=4.51.0 --upgrade")
        return False
    
    print()
    
    # Проверяем токенайзер
    if not check_qwen3_tokenizer():
        print("\n❌ Исправление не завершено!")
        return False
    
    print("\n🎉 Исправление успешно завершено!")
    print("✅ Qwen3-8B готов к работе")
    print("🚀 Можете запускать API: python start_api.py")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 