#!/usr/bin/env python3
"""
Скрипт для обработки вакансий из Excel файла по батчам.
Отправляет описания вакансий к API для анализа навыков.
"""

import os
import sys
import argparse
from vacancy_processor import VacancyProcessor


def main():
    parser = argparse.ArgumentParser(description='Обработка вакансий по батчам')
    parser.add_argument('--batch-size', type=int, default=100, 
                       help='Размер батча для обработки (по умолчанию: 100)')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Номер строки для начала обработки (по умолчанию: 0)')
    parser.add_argument('--max-batches', type=int, default=None,
                       help='Максимальное количество батчей для обработки')
    parser.add_argument('--excel-file', type=str, default='merged_vacs.xlsx',
                       help='Путь к Excel файлу с вакансиями')
    
    args = parser.parse_args()
    
    # Проверяем существование файла
    if not os.path.exists(args.excel_file):
        print(f"Ошибка: файл {args.excel_file} не найден")
        sys.exit(1)
    
    # Создаем процессор вакансий
    processor = VacancyProcessor(args.excel_file)
    
    # Получаем общее количество вакансий
    total_rows = processor.get_total_rows()
    print(f"Общее количество вакансий в файле: {total_rows}")
    
    if total_rows == 0:
        print("Не удалось получить данные из файла")
        sys.exit(1)
    
    # Вычисляем параметры обработки
    batch_size = args.batch_size
    start_row = args.start_from
    current_row = start_row
    batch_count = 0
    
    print(f"Начинаем обработку с строки {start_row}")
    print(f"Размер батча: {batch_size}")
    
    while current_row < total_rows:
        # Проверяем лимит на количество батчей
        if args.max_batches and batch_count >= args.max_batches:
            print(f"Достигнут лимит батчей: {args.max_batches}")
            break
        
        print(f"\n--- Батч {batch_count + 1} ---")
        print(f"Обработка строк {current_row} - {min(current_row + batch_size, total_rows)}")
        
        # Читаем батч вакансий
        vacancies = processor.read_vacancies_batch(batch_size, current_row)
        
        if not vacancies:
            print("Нет данных для обработки в этом батче")
            break
        
        print(f"Загружено {len(vacancies)} вакансий из батча")
        
        # Обрабатываем батч
        offset = current_row + len(vacancies)
        success = processor.process_batch(vacancies, offset)
        
        if success:
            print(f"Батч успешно обработан и сохранен как {offset}.csv")
            processed_count = processor.get_processed_count()
            print(f"Всего обработано вакансий: {processed_count}")
        else:
            print(f"Ошибка при обработке батча {offset}")
            break
        
        # Переходим к следующему батчу
        current_row += len(vacancies)
        batch_count += 1
        
        # Показываем прогресс
        progress = (current_row / total_rows) * 100
        print(f"Прогресс: {progress:.1f}% ({current_row}/{total_rows})")
    
    print(f"\nОбработка завершена!")
    final_count = processor.get_processed_count()
    print(f"Итого обработано вакансий: {final_count}")


if __name__ == "__main__":
    main() 