import pandas as pd
import requests
import re
import csv
import os
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
import time

from meta import API_URL


class VacancyProcessor:
    def __init__(self, excel_file_path: str, output_dir: str = "process_vacs"):
        self.excel_file_path = excel_file_path
        self.output_dir = output_dir
        self.api_url = API_URL
        
        # Создаем директорию для выходных файлов
        os.makedirs(output_dir, exist_ok=True)
    
    def clean_html(self, text: str) -> str:
        """Удаляет HTML теги из текста"""
        if pd.isna(text) or text is None:
            return ""
        
        # Используем BeautifulSoup для более качественной очистки HTML
        soup = BeautifulSoup(str(text), 'html.parser')
        cleaned_text = soup.get_text(separator=' ', strip=True)
        
        # Дополнительная очистка от лишних пробелов
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def send_api_request(self, description: str) -> Dict[str, List[str]]:
        """Отправляет POST запрос к API для анализа навыков"""
        try:
            payload = {"body": description}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return {
                "soft": result.get("soft", []),
                "hard": result.get("hard", [])
            }
        except requests.RequestException as e:
            print(f"Ошибка API запроса: {e}")
            return {"soft": [], "hard": []}
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return {"soft": [], "hard": []}
    
    def read_vacancies_batch(self, batch_size: int = 100, start_row: int = 0) -> List[Tuple[int, str]]:
        """Читает батч вакансий из Excel файла"""
        try:
            # Читаем файл, всегда начиная с нужной строки данных (не заголовка)
            # start_row=0 означает первую строку данных (после заголовка)
            df = pd.read_excel(
                self.excel_file_path,
                skiprows=range(1, start_row + 1) if start_row > 0 else None,
                nrows=batch_size,
                usecols=['id', 'description'],
                engine='openpyxl'
            )
            
            vacancies = []
            for _, row in df.iterrows():
                vacancy_id = int(row['id']) if pd.notna(row['id']) else None
                description = self.clean_html(row['description'])
                
                if vacancy_id is not None and description:
                    vacancies.append((vacancy_id, description))
            
            return vacancies
        except Exception as e:
            print(f"Ошибка чтения Excel файла: {e}")
            return []
    
    def process_batch(self, vacancies: List[Tuple[int, str]], offset: int) -> bool:
        """Обрабатывает батч вакансий и сохраняет результат в CSV"""
        results = []
        
        print(f"Обработка батча до {offset}...")
        
        for i, (vacancy_id, description) in enumerate(vacancies):
            print(f"Обработка вакансии ID={vacancy_id} ({i+1}/{len(vacancies)})")
            
            # Отправляем запрос к API
            skills = self.send_api_request(description)
            
            # Форматируем навыки как строки, разделенные запятыми
            hard_skills_str = ",".join(skills["hard"]) if skills["hard"] else ""
            soft_skills_str = ",".join(skills["soft"]) if skills["soft"] else ""
            
            results.append({
                "id": vacancy_id,
                "hard_skills": hard_skills_str,
                "soft_skills": soft_skills_str
            })
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
        
        # Сохраняем результаты в CSV
        output_file = os.path.join(self.output_dir, f"{offset}.csv")
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'hard_skills', 'soft_skills']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            print(f"Батч сохранен в {output_file}")
            return True
        except Exception as e:
            print(f"Ошибка сохранения файла {output_file}: {e}")
            return False
    
    def get_total_rows(self) -> int:
        """Получает общее количество строк в Excel файле"""
        try:
            # Читаем только колонку id для подсчета строк (экономия памяти)
            df = pd.read_excel(self.excel_file_path, usecols=['id'], engine='openpyxl')
            return len(df)
        except Exception as e:
            print(f"Ошибка получения количества строк: {e}")
            return 0
    
    def get_processed_count(self) -> int:
        """Возвращает количество обработанных вакансий"""
        try:
            csv_files = [f for f in os.listdir(self.output_dir) if f.endswith('.csv')]
            return len(csv_files) * 100
        except Exception:
            return 0
    
    def merge_all_csv_files(self, output_filename: str = "merged_results.csv") -> str:
        """Объединяет все CSV файлы в один"""
        try:
            csv_files = sorted([f for f in os.listdir(self.output_dir) if f.endswith('.csv')])
            
            if not csv_files:
                return "Нет CSV файлов для объединения"
            
            all_data = []
            for csv_file in csv_files:
                file_path = os.path.join(self.output_dir, csv_file)
                df = pd.read_csv(file_path)
                all_data.append(df)
            
            merged_df = pd.concat(all_data, ignore_index=True)
            output_path = os.path.join(self.output_dir, output_filename)
            merged_df.to_csv(output_path, index=False, encoding='utf-8')
            
            return f"Объединено {len(csv_files)} файлов в {output_path}"
        except Exception as e:
            return f"Ошибка объединения файлов: {e}"
    
    def merge_with_original(self, original_file: str = None) -> str:
        """Объединяет обработанные данные с оригинальным файлом (только обработанные строки)"""
        try:
            if original_file is None:
                original_file = self.excel_file_path
            
            # Читаем все обработанные файлы
            csv_files = [f for f in os.listdir(self.output_dir) if f.endswith('.csv') and not f.startswith('merged')]
            
            if not csv_files:
                return "Нет обработанных файлов для объединения"
            
            all_processed = []
            for csv_file in csv_files:
                file_path = os.path.join(self.output_dir, csv_file)
                df = pd.read_csv(file_path)
                all_processed.append(df)
            
            processed_df = pd.concat(all_processed, ignore_index=True)
            
            # Получаем уникальные ID обработанных вакансий
            processed_ids = set(processed_df['id'].tolist())
            
            # Читаем оригинальный файл только для обработанных ID
            original_df = pd.read_excel(original_file, engine='openpyxl')
            
            # Фильтруем оригинальный файл - только обработанные вакансии
            filtered_original = original_df[original_df['id'].isin(processed_ids)].copy()
            
            # Объединяем по ID
            merged_df = filtered_original.merge(processed_df, on='id', how='inner')
            
            # Сохраняем результат
            output_path = os.path.join(self.output_dir, "merged_with_original.xlsx")
            merged_df.to_excel(output_path, index=False, engine='openpyxl')
            
            return f"Объединено {len(merged_df)} обработанных вакансий: {output_path}"
        except Exception as e:
            return f"Ошибка объединения с оригинальным файлом: {e}" 