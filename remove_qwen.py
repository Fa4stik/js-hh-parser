#!/usr/bin/env python3
"""
Скрипт для удаления модели Qwen и связанных зависимостей
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def remove_huggingface_cache():
    """Удаляет кэш Hugging Face"""
    print("��️ Удаление кэша Hugging Face...")
    
    # Стандартные пути кэша
    cache_paths = [
        Path.home() / ".cache" / "huggingface",
        Path.home() / ".cache" / "transformers",
        Path.cwd() / ".cache",
        Path.cwd() / "transformers_cache"
    ]
    
    removed_count = 0
    total_freed = 0
    
    for cache_path in cache_paths:
        if cache_path.exists():
            try:
                # Подсчитываем размер перед удалением
                total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                total_freed += size_mb
                
                shutil.rmtree(cache_path)
                print(f"✅ Удален кэш: {cache_path} ({size_mb:.1f} MB)")
                removed_count += 1
            except Exception as e:
                print(f"❌ Ошибка при удалении {cache_path}: {e}")
    
    if removed_count == 0:
        print("ℹ️ Кэш Hugging Face не найден")
    else:
        print(f"✅ Удалено {removed_count} кэш-директорий")
        print(f"�� Освобождено места: {total_freed:.1f} MB")


def remove_python_packages():
    """Удаляет пакеты Python, связанные с Qwen"""
    print("\n📦 Удаление Python пакетов...")
    
    packages_to_remove = [
        "transformers",
        "torch", 
        "accelerate",
        "safetensors"
    ]
    
    for package in packages_to_remove:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "uninstall", package, "-y"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Удален пакет: {package}")
            else:
                print(f"ℹ️ Пакет {package} не установлен или уже удален")
                
        except Exception as e:
            print(f"❌ Ошибка при удалении {package}: {e}")


def update_requirements():
    """Обновляет requirements.txt, убирая зависимости Qwen"""
    print("\n📝 Обновление requirements.txt...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Файл requirements.txt не найден")
        return
    
    # Читаем текущие зависимости
    with open(requirements_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Фильтруем зависимости, связанные с Qwen
    qwen_related = ["transformers", "torch", "accelerate", "safetensors"]
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if line and not any(pkg in line for pkg in qwen_related):
            filtered_lines.append(line)
    
    # Записываем обновленный файл
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_lines) + '\n')
    
    print("✅ requirements.txt обновлен (удалены зависимости Qwen)")


def disable_qwen_code():
    """Отключает код загрузки модели в qwen.py"""
    print("\n�� Отключение кода загрузки модели...")
    
    qwen_file = Path("src/ai/qwen.py")
    if not qwen_file.exists():
        print("❌ Файл src/ai/qwen.py не найден")
        return
    
    # Читаем файл
    with open(qwen_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Создаем резервную копию
    backup_file = qwen_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📋 Создана резервная копия: {backup_file}")
    
    # Отключаем загрузку модели
    modified_content = content.replace(
        "self._load_model()",
        "# self._load_model()  # Отключено"
    )
    
    # Заменяем метод extract_skills на заглушку
    extract_method_start = "def extract_skills(self, description: str) -> Dict[str, List[str]]:"
    
    if extract_method_start in modified_content:
        # Находим позиции метода
        start_pos = modified_content.find(extract_method_start)
        
        # Ищем конец метода (следующий метод или конец класса)
        end_pos = modified_content.find("def ", start_pos + 1)
        if end_pos == -1:
            end_pos = modified_content.find("# Инициализируем экстрактор навыков", start_pos)
        
        if end_pos != -1:
            # Создаем заглушку
            stub_method = '''    def extract_skills(self, description: str) -> Dict[str, List[str]]:
        """Заглушка - модель отключена"""
        print("⚠️ Модель Qwen отключена. Возвращаем пустые навыки.")
        return {"soft": [], "hard": []}'''
            
            # Заменяем метод
            before_method = modified_content[:start_pos]
            after_method = modified_content[end_pos:]
            modified_content = before_method + stub_method + "\n\n" + after_method
    
    # Записываем измененный файл
    with open(qwen_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ Код загрузки модели отключен")


def remove_docker_cache():
    """Удаляет Docker кэш, если используется"""
    print("\n�� Проверка Docker кэша...")
    
    try:
        # Проверяем, есть ли Docker volumes
        result = subprocess.run([
            "docker", "volume", "ls", "--filter", "name=model_cache"
        ], capture_output=True, text=True)
        
        if "model_cache" in result.stdout:
            print("🗑️ Удаление Docker volume model_cache...")
            subprocess.run(["docker", "volume", "rm", "model_cache"], check=True)
            print("✅ Docker volume удален")
        else:
            print("ℹ️ Docker volume model_cache не найден")
            
    except subprocess.CalledProcessError:
        print("ℹ️ Docker не установлен или недоступен")
    except Exception as e:
        print(f"❌ Ошибка при работе с Docker: {e}")


def main():
    """Основная функция удаления"""
    print("��️ Удаление модели Qwen и связанных компонентов\n")
    
    # Удаляем кэш
    remove_huggingface_cache()
    
    # Удаляем пакеты
    remove_python_packages()
    
    # Обновляем requirements.txt
    update_requirements()
    
    # Отключаем код
    disable_qwen_code()
    
    # Удаляем Docker кэш
    remove_docker_cache()
    
    print("\n�� Удаление завершено!")
    print("📋 Что было сделано:")
    print("   ✅ Удален кэш Hugging Face")
    print("   ✅ Удалены пакеты transformers, torch, accelerate")
    print("   ✅ Обновлен requirements.txt")
    print("   ✅ Отключен код загрузки модели")
    print("   ✅ Удален Docker кэш (если был)")
    print("\n📝 Примечания:")
    print("   - Создана резервная копия src/ai/qwen.py.backup")
    print("   - API теперь возвращает пустые навыки")
    print("   - Для восстановления используйте резервную копию")
    print("\n🚀 Альтернативы:")
    print("   - python src/ai/simple_api.py - простое API без модели")
    print("   - cp src/ai/qwen.py.backup src/ai/qwen.py - восстановление")


if __name__ == "__main__":
    main() 