#!/usr/bin/env python3
"""
Отладочный скрипт для проверки чтения вакансий
"""

import pandas as pd
from vacancy_processor import VacancyProcessor

def debug_excel_reading():
    """Отладочная функция для проверки чтения Excel"""
    file_path = "merged_vacs.xlsx"
    processor = VacancyProcessor(file_path)
    
    print("=== Отладка чтения Excel файла ===")
    
    # Сначала посмотрим на структуру файла
    print("\n--- Проверка структуры файла ---")
    try:
        # Читаем первые 5 строк для проверки
        df_sample = pd.read_excel(file_path, nrows=5, engine='openpyxl')
        print(f"Колонки в файле: {list(df_sample.columns)}")
        print(f"Первые 5 строк:")
        for i, row in df_sample.iterrows():
            print(f"  Строка {i}: ID={row.get('id', 'N/A')}")
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return
    
    # Тестируем наш метод
    print("\n--- Тест метода read_vacancies_batch ---")
    
    # Первый батч (строки 0-2 для теста)
    print("Первый батч (start_row=0, batch_size=3):")
    batch1 = processor.read_vacancies_batch(3, 0)
    print(f"Получено вакансий: {len(batch1)}")
    for i, (vacancy_id, description) in enumerate(batch1):
        print(f"  {i}: ID={vacancy_id}, описание={description[:50]}...")
    
    # Второй батч (строки 3-5 для теста)
    print("\nВторой батч (start_row=3, batch_size=3):")
    batch2 = processor.read_vacancies_batch(3, 3)
    print(f"Получено вакансий: {len(batch2)}")
    for i, (vacancy_id, description) in enumerate(batch2):
        print(f"  {i}: ID={vacancy_id}, описание={description[:50]}...")
    
    # Проверяем пересечения
    if batch1 and batch2:
        ids1 = [v[0] for v in batch1]
        ids2 = [v[0] for v in batch2]
        print(f"\nID первого батча: {ids1}")
        print(f"ID второго батча: {ids2}")
        
        intersection = set(ids1).intersection(set(ids2))
        if intersection:
            print(f"❌ ПЕРЕСЕЧЕНИЯ: {intersection}")
        else:
            print("✅ Пересечений нет")
    
    # Тестируем реальные размеры
    print("\n--- Тест реальных размеров ---")
    batch_real = processor.read_vacancies_batch(100, 0)
    print(f"Первый реальный батч (100 вакансий): получено {len(batch_real)}")
    if batch_real:
        print(f"Первая вакансия: ID={batch_real[0][0]}")
        print(f"Последняя вакансия: ID={batch_real[-1][0]}")

if __name__ == "__main__":
    debug_excel_reading() 