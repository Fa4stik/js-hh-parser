#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики обработки батчей
"""

import os
from vacancy_processor import VacancyProcessor

def test_batch_reading():
    """Тестирует чтение батчей"""
    processor = VacancyProcessor("merged_vacs.xlsx")
    
    print("=== Тест логики чтения батчей ===")
    
    # Получаем общее количество строк
    total_rows = processor.get_total_rows()
    print(f"Общее количество вакансий: {total_rows}")
    
    if total_rows == 0:
        print("❌ Не удалось прочитать файл")
        return
    
    # Тестируем чтение первого батча
    print("\n--- Тест 1: Первый батч (строки 0-100) ---")
    batch1 = processor.read_vacancies_batch(100, 0)
    print(f"Прочитано вакансий: {len(batch1)}")
    if batch1:
        print(f"Первая вакансия: ID={batch1[0][0]}")
        print(f"Последняя вакансия: ID={batch1[-1][0]}")
    
    # Тестируем чтение второго батча
    print("\n--- Тест 2: Второй батч (строки 100-200) ---")
    batch2 = processor.read_vacancies_batch(100, 100)
    print(f"Прочитано вакансий: {len(batch2)}")
    if batch2:
        print(f"Первая вакансия: ID={batch2[0][0]}")
        print(f"Последняя вакансия: ID={batch2[-1][0]}")
    
    # Проверяем, что ID не пересекаются
    if batch1 and batch2:
        batch1_ids = set(v[0] for v in batch1)
        batch2_ids = set(v[0] for v in batch2)
        intersection = batch1_ids.intersection(batch2_ids)
        
        if intersection:
            print(f"❌ ОШИБКА: Найдены дублирующиеся ID: {intersection}")
        else:
            print("✅ Батчи не пересекаются")
    
    # Тестируем определение offset
    print("\n--- Тест 3: Определение offset ---")
    process_dir = processor.output_dir
    
    # Создаем тестовые файлы
    test_files = ["100.csv", "200.csv", "300.csv"]
    for file in test_files:
        filepath = os.path.join(process_dir, file)
        with open(filepath, 'w') as f:
            f.write("id,hard_skills,soft_skills\n")
    
    print(f"Созданы тестовые файлы: {test_files}")
    
    # Тестируем логику определения offset (как в main.py)
    csv_files = [f for f in os.listdir(process_dir) if f.endswith('.csv')]
    max_offset = 0
    
    if csv_files:
        offsets = []
        for file in csv_files:
            try:
                offset = int(file.replace('.csv', ''))
                offsets.append(offset)
            except ValueError:
                continue
        if offsets:
            max_offset = max(offsets)
    
    print(f"Найдено CSV файлов: {len(csv_files)}")
    print(f"Максимальный offset: {max_offset}")
    print(f"Следующий батч должен начаться с строки: {max_offset}")
    
    # Удаляем тестовые файлы
    for file in test_files:
        filepath = os.path.join(process_dir, file)
        try:
            os.remove(filepath)
        except:
            pass
    
    print("\n✅ Тест завершен")

if __name__ == "__main__":
    test_batch_reading() 