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
    
    def send_api_request(self, description: str, skill_type: str = None) -> Dict[str, List[str]]:
        """Отправляет POST запрос к API для анализа навыков"""
        try:
            payload = {"body": description}
            
            # Добавляем параметр skill если указан
            if skill_type:
                payload["skill"] = skill_type
                
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
    
    def get_empty_skills_from_merged(self, limit: int = None) -> List[Tuple[int, str, int, str, str]]:
        """Получает список вакансий с частично пустыми навыками из merged_results.csv"""
        try:
            merged_file = os.path.join(self.output_dir, "merged_results.csv")
            
            if not os.path.exists(merged_file):
                return []
            
            # Перечитываем файл каждый раз для получения актуальных данных
            df = pd.read_csv(merged_file)
            
            # Находим строки с частично пустыми навыками (хотя бы одна колонка пустая)
            hard_empty = df['hard_skills'].isna() | (df['hard_skills'] == '') | (df['hard_skills'] == 'nan')
            soft_empty = df['soft_skills'].isna() | (df['soft_skills'] == '') | (df['soft_skills'] == 'nan')
            
            # Берем строки где хотя бы один навык пустой
            empty_mask = hard_empty | soft_empty
            
            empty_rows = df[empty_mask]
            
            if limit:
                empty_rows = empty_rows.head(limit)
            
            # Получаем описания вакансий из оригинального файла только для найденных ID
            if empty_rows.empty:
                return []
            
            empty_ids = empty_rows['id'].tolist()
            original_df = pd.read_excel(self.excel_file_path, engine='openpyxl')
            original_filtered = original_df[original_df['id'].isin(empty_ids)]
            
            result = []
            for _, row in empty_rows.iterrows():
                vacancy_id = int(row['id'])
                
                # Находим описание в оригинальном файле
                original_row = original_filtered[original_filtered['id'] == vacancy_id]
                if not original_row.empty:
                    description = self.clean_html(original_row.iloc[0]['description'])
                    # Добавляем индекс строки в merged_results.csv для обновления
                    csv_index = df[df['id'] == vacancy_id].index[0]
                    
                    # Текущие навыки (чтобы не перезаписывать заполненные)
                    current_hard = row['hard_skills'] if pd.notna(row['hard_skills']) and str(row['hard_skills']).strip() and str(row['hard_skills']) != 'nan' else ''
                    current_soft = row['soft_skills'] if pd.notna(row['soft_skills']) and str(row['soft_skills']).strip() and str(row['soft_skills']) != 'nan' else ''
                    
                    result.append((vacancy_id, description, csv_index, current_hard, current_soft))
            
            return result
            
        except Exception as e:
            print(f"Ошибка получения пустых навыков: {e}")
            return []
    
    def update_skills_in_merged(self, csv_index: int, hard_skills: List[str], soft_skills: List[str]) -> bool:
        """Обновляет навыки в merged_results.csv по индексу строки"""
        try:
            merged_file = os.path.join(self.output_dir, "merged_results.csv")
            
            if not os.path.exists(merged_file):
                return False
            
            df = pd.read_csv(merged_file)
            
            # Обновляем навыки
            hard_skills_str = ",".join(hard_skills) if hard_skills else ""
            soft_skills_str = ",".join(soft_skills) if soft_skills else ""
            
            df.at[csv_index, 'hard_skills'] = hard_skills_str
            df.at[csv_index, 'soft_skills'] = soft_skills_str
            
            # Сохраняем файл
            df.to_csv(merged_file, index=False, encoding='utf-8')
            
            return True
            
        except Exception as e:
            print(f"Ошибка обновления навыков: {e}")
            return False
    
    def update_skills_in_merged_with_original(self, vacancy_id: int, current_hard: str, current_soft: str, new_hard_skills: List[str], new_soft_skills: List[str]) -> bool:
        """Обновляет навыки в merged_with_original.xlsx, заполняя только пустые поля"""
        try:
            merged_file = os.path.join(self.output_dir, "merged_with_original.xlsx")
            
            if not os.path.exists(merged_file):
                # Если файл не существует, создаем его сначала
                self.merge_with_original()
                if not os.path.exists(merged_file):
                    return False
            
            # Читаем Excel файл
            df = pd.read_excel(merged_file, engine='openpyxl')
            
            # Находим строку с нужным ID
            mask = df['id'] == vacancy_id
            if not mask.any():
                print(f"Вакансия {vacancy_id} не найдена в merged_with_original.xlsx")
                return False
            
            row_index = df[mask].index[0]
            
            # Определяем, какие навыки нужно обновить
            final_hard = current_hard
            final_soft = current_soft
            
            # Заполняем только пустые поля
            if not current_hard and new_hard_skills:
                final_hard = ",".join(new_hard_skills)
            
            if not current_soft and new_soft_skills:
                final_soft = ",".join(new_soft_skills)
            
            # Обновляем навыки
            df.at[row_index, 'hard_skills'] = final_hard
            df.at[row_index, 'soft_skills'] = final_soft
            
            # Сохраняем файл
            df.to_excel(merged_file, index=False, engine='openpyxl')
            
            return True
            
        except Exception as e:
            print(f"Ошибка обновления навыков в merged_with_original.xlsx: {e}")
            return False
    
    def count_empty_skills_in_merged(self) -> int:
        """Подсчитывает количество вакансий с частично пустыми навыками в merged_results.csv"""
        try:
            merged_file = os.path.join(self.output_dir, "merged_results.csv")
            
            if not os.path.exists(merged_file):
                return 0
            
            df = pd.read_csv(merged_file)
            
            # Считаем строки с частично пустыми навыками (хотя бы одна колонка пустая)
            hard_empty = df['hard_skills'].isna() | (df['hard_skills'] == '') | (df['hard_skills'] == 'nan')
            soft_empty = df['soft_skills'].isna() | (df['soft_skills'] == '') | (df['soft_skills'] == 'nan')
            
            # Берем строки где хотя бы один навык пустой
            empty_mask = hard_empty | soft_empty
            
            return empty_mask.sum()
            
        except Exception as e:
            print(f"Ошибка подсчета пустых навыков: {e}")
            return 0 