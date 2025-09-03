#!/usr/bin/env python3
"""
Telegram бот для управления обработкой вакансий.
Поддерживает команды для мониторинга прогресса и объединения файлов.
Автоматически запускает обработку при старте.
"""

import os
import logging
import asyncio
import threading
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from vacancy_processor import VacancyProcessor
from meta import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальный процессор вакансий
processor = VacancyProcessor("merged_vacs.xlsx")

# Флаг для отслеживания состояния обработки
processing_active = False
processing_thread = None

# Флаг для отслеживания заполнения пустых навыков
filling_empty_active = False
filling_empty_thread = None

# Состояния для диалогов
GET_OFFSET = 0


def process_vacancies_background():
    """Фоновая обработка вакансий"""
    global processing_active
    
    try:
        logger.info("Начинаю фоновую обработку вакансий...")
        
        # Получаем общее количество вакансий
        total_rows = processor.get_total_rows()
        logger.info(f"Общее количество вакансий: {total_rows}")
        
        if total_rows == 0:
            logger.error("Не удалось получить данные из файла")
            processing_active = False
            return
        
        # Определяем с какой строки начинать (проверяем уже обработанные файлы)
        process_dir = processor.output_dir
        csv_files = []
        max_offset = 0
        
        if os.path.exists(process_dir):
            csv_files = [f for f in os.listdir(process_dir) if f.endswith('.csv')]
            if csv_files:
                # Находим максимальный offset из имен файлов
                offsets = []
                for file in csv_files:
                    try:
                        offset = int(file.replace('.csv', ''))
                        offsets.append(offset)
                    except ValueError:
                        continue
                if offsets:
                    max_offset = max(offsets)
        
        start_row = max_offset
        processed_count = len(csv_files) * 100
        
        logger.info(f"Найдено {len(csv_files)} обработанных файлов")
        logger.info(f"Максимальный offset: {max_offset}")
        logger.info(f"Начинаю с строки: {start_row}")
        
        batch_size = 100
        current_row = start_row
        batch_count = 0
        
        while current_row < total_rows and processing_active:
            logger.info(f"--- Батч {batch_count + 1} ---")
            logger.info(f"Обработка строк {current_row} - {min(current_row + batch_size, total_rows)}")
            
            # Читаем батч вакансий
            vacancies = processor.read_vacancies_batch(batch_size, current_row)
            
            if not vacancies:
                logger.info("Нет данных для обработки в этом батче")
                break
            
            logger.info(f"Загружено {len(vacancies)} вакансий из батча")
            
            # Обрабатываем батч
            offset = current_row + len(vacancies)
            success = processor.process_batch(vacancies, offset)
            
            if success:
                logger.info(f"Батч успешно обработан и сохранен как {offset}.csv")
                new_processed_count = processor.get_processed_count()
                logger.info(f"Всего обработано вакансий: {new_processed_count}")
            else:
                logger.error(f"Ошибка при обработке батча {offset}")
                break
            
            # Переходим к следующему батчу
            current_row += len(vacancies)
            batch_count += 1
            
            # Показываем прогресс
            progress = (current_row / total_rows) * 100
            logger.info(f"Прогресс: {progress:.1f}% ({current_row}/{total_rows})")
        
        logger.info("Фоновая обработка завершена!")
        final_count = processor.get_processed_count()
        logger.info(f"Итого обработано вакансий: {final_count}")
        
    except Exception as e:
        logger.error(f"Ошибка в фоновой обработке: {e}")
    finally:
        processing_active = False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение."""
    welcome_text = """
🤖 Бот для управления обработкой вакансий

🔄 Автоматическая обработка запущена при старте бота!

Доступные команды:
/get_process - показать количество обработанных вакансий
/get_by_offset - получить CSV файл по offset
/merge_vacs - объединить все CSV файлы в один
/merge_by_id - объединить обработанные данные с оригинальным файлом (только обработанные)
/fill_empty - заполнить пустые навыки в merged_results.csv
/stop_fill_empty - остановить заполнение пустых навыков
/statistic - показать статистику по merged_with_original.xlsx
/start_processing - запустить обработку вручную
/stop_processing - остановить обработку
/help - показать это сообщение
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет справку по командам."""
    help_text = """
📋 Доступные команды:

/get_process - Показывает количество обработанных вакансий
Считается как: количество файлов в папке process_vacs × 100

/get_by_offset - Возвращает CSV файл по offset
Введите offset (4 = 100.csv, 150 = 200.csv и т.д.)

/merge_vacs - Объединяет все CSV файлы в один merged_results.csv
Полезно для создания единого файла со всеми обработанными данными

/merge_by_id - Объединяет все обработанные вакансии с исходным файлом
Возвращает только те строки, которые были обработаны (не весь файл)

/fill_empty - Заполняет частично пустые навыки (hard или soft)
Заполняет только пустые поля и записывает результат в merged_with_original.xlsx

/stop_fill_empty - Останавливает процесс заполнения пустых навыков

/statistic - Показывает статистику по файлу merged_with_original.xlsx
Анализирует количество вакансий с пропущенными навыками

/start_processing - Запускает обработку вакансий вручную
Полезно если обработка была остановлена

/stop_processing - Останавливает текущую обработку

/help - Показывает это сообщение

ℹ️ Обработка автоматически запускается при старте бота
"""
    await update.message.reply_text(help_text)


async def get_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает количество обработанных вакансий."""
    try:
        processed_count = processor.get_processed_count()
        total_rows = processor.get_total_rows()
        
        # Получаем список файлов для детальной информации
        process_dir = processor.output_dir
        csv_files = []
        if os.path.exists(process_dir):
            csv_files = sorted([f for f in os.listdir(process_dir) if f.endswith('.csv')])
        
        status_icon = "🔄" if processing_active else "⏸️"
        status_text = "активна" if processing_active else "остановлена"
        
        fill_status_icon = "🔄" if filling_empty_active else "⏸️"
        fill_status_text = "активно" if filling_empty_active else "остановлено"
        
        # Проверяем количество пустых навыков
        empty_skills_count = processor.count_empty_skills_in_merged()
        
        message = f"""
📊 Статистика обработки вакансий:

{status_icon} Обработка: {status_text}
{fill_status_icon} Заполнение пустых: {fill_status_text}
✅ Обработано вакансий: {processed_count}
📁 Количество CSV файлов: {len(csv_files)}
📄 Общее количество вакансий: {total_rows}
🔍 Пустых навыков: {empty_skills_count}

"""
        
        if total_rows > 0:
            progress = (processed_count / total_rows) * 100
            message += f"📈 Прогресс: {progress:.1f}%\n"
        
        if csv_files:
            message += f"\n📂 Последние файлы:\n"
            # Показываем последние 5 файлов
            for file in csv_files[-5:]:
                message += f"• {file}\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        error_message = f"❌ Ошибка при получении статистики: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in get_process: {e}")


async def start_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает обработку вакансий вручную."""
    global processing_active, processing_thread
    
    try:
        if processing_active:
            await update.message.reply_text("🔄 Обработка уже активна!")
            return
        
        await update.message.reply_text("🚀 Запускаю обработку вакансий...")
        
        processing_active = True
        processing_thread = threading.Thread(target=process_vacancies_background)
        processing_thread.daemon = True
        processing_thread.start()
        
        await update.message.reply_text("✅ Обработка запущена в фоновом режиме!")
        
    except Exception as e:
        error_message = f"❌ Ошибка запуска обработки: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in start_processing: {e}")


async def stop_processing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Останавливает обработку вакансий."""
    global processing_active
    
    try:
        if not processing_active:
            await update.message.reply_text("⏸️ Обработка уже остановлена!")
            return
        
        processing_active = False
        await update.message.reply_text("⏹️ Обработка остановлена!")
        
    except Exception as e:
        error_message = f"❌ Ошибка остановки обработки: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in stop_processing: {e}")


async def get_by_offset_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог для получения файла по offset"""
    await update.message.reply_text(
        "📁 Введите offset для получения CSV файла:\n\n"
        "Примеры:\n"
        "• 4 → вернет 100.csv\n"
        "• 150 → вернет 200.csv\n"
        "• 250 → вернет 300.csv\n\n"
        "Или /cancel для отмены"
    )
    return GET_OFFSET


async def get_by_offset_handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает введенный offset"""
    try:
        user_input = update.message.text.strip()
        
        # Проверяем команду отмены
        if user_input.lower() in ['/cancel', 'отмена']:
            await update.message.reply_text("❌ Операция отменена")
            return ConversationHandler.END
        
        # Парсим offset
        try:
            offset = int(user_input)
        except ValueError:
            await update.message.reply_text("❌ Неверный формат. Введите число или /cancel")
            return GET_OFFSET
        
        if offset <= 0:
            await update.message.reply_text("❌ Offset должен быть положительным числом")
            return GET_OFFSET
        
        # Определяем имя файла на основе offset
        # offset 4 → 100.csv, offset 150 → 200.csv
        file_offset = ((offset - 1) // 100 + 1) * 100
        filename = f"{file_offset}.csv"
        filepath = os.path.join(processor.output_dir, filename)
        
        # Проверяем существование файла
        if not os.path.exists(filepath):
            await update.message.reply_text(
                f"❌ Файл {filename} не найден!\n"
                f"Offset {offset} соответствует файлу {filename}, который еще не обработан."
            )
            return ConversationHandler.END
        
        # Отправляем файл
        await update.message.reply_text(f"📄 Отправляю файл {filename}...")
        
        with open(filepath, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=filename,
                caption=f"CSV файл для offset {offset} (файл {filename})"
            )
        
        return ConversationHandler.END
        
    except Exception as e:
        error_message = f"❌ Ошибка при получении файла: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in get_by_offset_handle: {e}")
        return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог"""
    await update.message.reply_text("❌ Операция отменена")
    return ConversationHandler.END


async def merge_vacs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Объединяет все CSV файлы в один и отправляет файл."""
    try:
        await update.message.reply_text("🔄 Начинаю объединение CSV файлов...")
        
        result = processor.merge_all_csv_files()
        
        # Путь к объединенному файлу
        merged_file_path = os.path.join(processor.output_dir, "merged_results.csv")
        
        if os.path.exists(merged_file_path):
            await update.message.reply_text(f"✅ {result}")
            
            # Отправляем файл пользователю
            with open(merged_file_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename="merged_results.csv",
                    caption="Объединенный CSV файл со всеми обработанными вакансиями"
                )
        else:
            await update.message.reply_text(f"⚠️ {result}")
        
    except Exception as e:
        error_message = f"❌ Ошибка при объединении файлов: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in merge_vacs: {e}")


async def merge_by_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Объединяет обработанные данные с оригинальным файлом (только обработанные строки)."""
    try:
        await update.message.reply_text("🔄 Начинаю объединение с оригинальным файлом...")
        await update.message.reply_text("📊 Этап 1: Объединяю все CSV файлы...")
        
        # Сначала мержим все CSV
        merge_result = processor.merge_all_csv_files()
        
        await update.message.reply_text("📋 Этап 2: Объединяю с оригинальным файлом...")
        
        # Затем объединяем с оригинальным файлом
        result = processor.merge_with_original()
        
        # Путь к результирующему файлу
        result_file_path = os.path.join(processor.output_dir, "merged_with_original.xlsx")
        
        if os.path.exists(result_file_path):
            await update.message.reply_text(f"✅ {result}")
            
            # Отправляем файл пользователю
            with open(result_file_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename="merged_with_original.xlsx",
                    caption="Обработанные вакансии с навыками (только обработанные строки)"
                )
        else:
            await update.message.reply_text(f"⚠️ {result}")
        
    except Exception as e:
        error_message = f"❌ Ошибка при объединении с оригинальным файлом: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in merge_by_id: {e}")


def fill_empty_skills_background():
    """Фоновое заполнение пустых навыков"""
    global filling_empty_active
    
    try:
        logger.info("Начинаю заполнение пустых навыков...")
        
        total_processed = 0
        batch_size = 10  # Обрабатываем по 10 вакансий за раз
        
        while filling_empty_active:
            # Получаем следующую партию вакансий с пустыми навыками
            empty_vacancies = processor.get_empty_skills_from_merged(limit=batch_size)
            
            if not empty_vacancies:
                logger.info("Больше нет вакансий с пустыми навыками")
                break
            
            current_batch_size = len(empty_vacancies)
            logger.info(f"Обрабатываю партию из {current_batch_size} вакансий...")
            
            batch_processed = 0
            
            for vacancy_id, description, csv_index, current_hard, current_soft in empty_vacancies:
                if not filling_empty_active:
                    logger.info("Заполнение остановлено пользователем")
                    break
                    
                # Определяем, какие навыки нужно заполнить
                need_hard = not current_hard
                need_soft = not current_soft
                
                logger.info(f"Заполняю навыки для вакансии ID={vacancy_id} (партия: {batch_processed + 1}/{current_batch_size}) - нужно: hard={need_hard}, soft={need_soft}")
                logger.info(f"Текущие навыки: hard='{current_hard}', soft='{current_soft}'")
                
                # Определяем тип запроса к API
                skill_type = None
                if need_hard and need_soft:
                    skill_type = None  # Ищем оба типа
                elif need_hard:
                    skill_type = "hard"  # Только хард скиллы
                elif need_soft:
                    skill_type = "soft"  # Только софт скиллы
                
                logger.info(f"Тип запроса к API: {skill_type if skill_type else 'both'}")
                
                # Повторяем запросы до получения результата
                max_attempts = 5
                attempt = 0
                skills = None
                
                while attempt < max_attempts and filling_empty_active:
                    attempt += 1
                    logger.info(f"Попытка {attempt}/{max_attempts} для вакансии {vacancy_id}")
                    
                    skills = processor.send_api_request(description, skill_type)
                    
                    # Проверяем, получили ли мы нужные навыки
                    got_needed_skills = False
                    if skills:
                        # Если нужны hard и получили hard, или нужны soft и получили soft
                        if need_hard and need_soft:
                            # Нужны оба типа - достаточно получить хотя бы один
                            if skills.get("hard") or skills.get("soft"):
                                got_needed_skills = True
                        elif need_hard and skills.get("hard"):
                            got_needed_skills = True
                        elif need_soft and skills.get("soft"):
                            got_needed_skills = True
                        elif not need_hard and not need_soft:
                            # Если не нужны навыки (странная ситуация), считаем успешным
                            got_needed_skills = True
                    
                    # Если это последняя попытка, принимаем любой результат
                    if attempt >= max_attempts:
                        logger.info(f"Последняя попытка для вакансии {vacancy_id}, принимаем результат")
                        got_needed_skills = True
                    
                    if got_needed_skills:
                        logger.info(f"Получены навыки для вакансии {vacancy_id}: hard={len(skills.get('hard', []) if skills else [])}, soft={len(skills.get('soft', []) if skills else [])}")
                        break
                    else:
                        logger.warning(f"Не получены нужные навыки для вакансии {vacancy_id}, попытка {attempt}")
                        time.sleep(1)  # Пауза перед повтором
                
                # Обновляем файлы (merged_results.csv и merged_with_original.xlsx)
                # Обновляем merged_results.csv (для отслеживания прогресса)
                if skills and (skills.get("hard") or skills.get("soft")):
                    # Получили навыки - обновляем с новыми
                    final_hard = skills.get("hard", []) if need_hard else current_hard.split(",") if current_hard else []
                    final_soft = skills.get("soft", []) if need_soft else current_soft.split(",") if current_soft else []
                    
                    # Обновляем CSV
                    success1 = processor.update_skills_in_merged(csv_index, final_hard, final_soft)
                    
                    # Обновляем Excel только если есть новые навыки
                    success2 = processor.update_skills_in_merged_with_original(
                        vacancy_id, current_hard, current_soft,
                        skills.get("hard", []) if need_hard else [],
                        skills.get("soft", []) if need_soft else []
                    )
                    
                    if success1 and success2:
                        batch_processed += 1
                        total_processed += 1
                        remaining_in_file = processor.count_empty_skills_in_merged()
                        logger.info(f"Обновлена вакансия {vacancy_id} с новыми навыками. Всего обработано: {total_processed}, осталось в файле: {remaining_in_file}")
                    else:
                        logger.error(f"Ошибка обновления вакансии {vacancy_id}: CSV={success1}, Excel={success2}")
                else:
                    # Навыки не получены - помечаем как обработанную, чтобы не повторять
                    final_hard = current_hard.split(",") if current_hard else []
                    final_soft = current_soft.split(",") if current_soft else []
                    
                    # Обновляем только CSV для отслеживания прогресса
                    success1 = processor.update_skills_in_merged(csv_index, final_hard, final_soft)
                    
                    batch_processed += 1
                    total_processed += 1
                    remaining_in_file = processor.count_empty_skills_in_merged()
                    logger.info(f"Пропущена вакансия {vacancy_id} - навыки не получены. Всего обработано: {total_processed}, осталось в файле: {remaining_in_file}")
                
                # Небольшая пауза между запросами
                time.sleep(0.2)
            
            logger.info(f"Партия завершена! Обработано в партии: {batch_processed}/{current_batch_size}")
            
            # Небольшая пауза между партиями
            if filling_empty_active:
                time.sleep(1)
        
        logger.info(f"Заполнение завершено! Всего обработано: {total_processed}")
        
    except Exception as e:
        logger.error(f"Ошибка в заполнении пустых навыков: {e}")
    finally:
        filling_empty_active = False


async def fill_empty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает заполнение пустых навыков"""
    global filling_empty_active, filling_empty_thread
    
    try:
        # Проверяем, не запущено ли уже заполнение
        if filling_empty_active:
            await update.message.reply_text("🔄 Заполнение пустых навыков уже активно!")
            return
        
        # Проверяем существование merged_results.csv
        merged_file = os.path.join(processor.output_dir, "merged_results.csv")
        if not os.path.exists(merged_file):
            await update.message.reply_text("❌ Файл merged_results.csv не найден! Сначала выполните /merge_vacs")
            return
        
        # Подсчитываем количество пустых навыков
        empty_count = processor.count_empty_skills_in_merged()
        
        if empty_count == 0:
            await update.message.reply_text("✅ Все навыки уже заполнены!")
            return
        
        await update.message.reply_text(
            f"🚀 Запускаю заполнение пустых навыков...\n"
            f"Найдено {empty_count} вакансий с пустыми навыками"
        )
        
        # Запускаем фоновое заполнение
        filling_empty_active = True
        filling_empty_thread = threading.Thread(target=fill_empty_skills_background)
        filling_empty_thread.daemon = True
        filling_empty_thread.start()
        
        await update.message.reply_text("✅ Заполнение запущено в фоновом режиме!")
        
        # Отправляем периодические обновления
        await send_fill_progress_updates(update, context)
        
    except Exception as e:
        error_message = f"❌ Ошибка запуска заполнения: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in fill_empty: {e}")


async def send_fill_progress_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет обновления прогресса заполнения"""
    import asyncio
    
    initial_count = processor.count_empty_skills_in_merged()
    
    while filling_empty_active:
        await asyncio.sleep(30)  # Обновления каждые 30 секунд
        
        if not filling_empty_active:
            break
            
        current_empty = processor.count_empty_skills_in_merged()
        filled = initial_count - current_empty
        
        if filled > 0:
            progress_message = (
                f"📈 Прогресс заполнения:\n"
                f"✅ Заполнено: {filled}\n"
                f"⏳ Осталось: {current_empty}\n"
                f"📊 Прогресс: {(filled/initial_count)*100:.1f}%"
            )
            
            try:
                await update.message.reply_text(progress_message)
            except Exception as e:
                logger.error(f"Ошибка отправки прогресса: {e}")
    
    # Финальное сообщение
    if not filling_empty_active:
        final_empty = processor.count_empty_skills_in_merged()
        final_filled = initial_count - final_empty
        
        final_message = (
            f"🎉 Заполнение завершено!\n"
            f"✅ Заполнено навыков: {final_filled}\n"
            f"⏳ Осталось пустых: {final_empty}"
        )
        
        try:
            await update.message.reply_text(final_message)
        except Exception as e:
            logger.error(f"Ошибка отправки финального сообщения: {e}")


async def stop_fill_empty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Останавливает заполнение пустых навыков."""
    global filling_empty_active
    
    try:
        if not filling_empty_active:
            await update.message.reply_text("⏸️ Заполнение пустых навыков уже остановлено!")
            return
        
        filling_empty_active = False
        await update.message.reply_text("⏹️ Заполнение пустых навыков остановлено!")
        
    except Exception as e:
        error_message = f"❌ Ошибка остановки заполнения: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in stop_fill_empty: {e}")


async def statistic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает статистику по файлу merged_with_original.xlsx"""
    try:
        await update.message.reply_text("📊 Анализирую файл merged_with_original.xlsx...")
        
        stats = processor.get_statistics_from_merged_with_original()
        
        if stats.get("error"):
            error_message = f"❌ Ошибка: {stats['error']}"
            await update.message.reply_text(error_message)
            return
        
        # Формируем сообщение со статистикой
        total = stats["total"]
        missing_hard_only = stats["missing_hard_only"]
        missing_soft_only = stats["missing_soft_only"]
        missing_both = stats["missing_both"]
        has_both = stats["has_both"]
        
        # Подсчитываем проценты
        if total > 0:
            missing_hard_pct = (missing_hard_only / total) * 100
            missing_soft_pct = (missing_soft_only / total) * 100
            missing_both_pct = (missing_both / total) * 100
            has_both_pct = (has_both / total) * 100
        else:
            missing_hard_pct = missing_soft_pct = missing_both_pct = has_both_pct = 0
        
        message = f"""
📊 **Статистика по merged_with_original.xlsx**

📄 **Общее количество вакансий:** {total:,}

🔴 **Вакансии без навыков:** {missing_both:,} ({missing_both_pct:.1f}%)

🟡 **Вакансии с одним пропуском:**
• Нет hard skills: {missing_hard_only:,} ({missing_hard_pct:.1f}%)
• Нет soft skills: {missing_soft_only:,} ({missing_soft_pct:.1f}%)

🟢 **Вакансии с полными навыками:** {has_both:,} ({has_both_pct:.1f}%)

📈 **Сводка пропусков:**
• Всего с пропусками: {missing_hard_only + missing_soft_only + missing_both:,} ({((missing_hard_only + missing_soft_only + missing_both) / total * 100 if total > 0 else 0):.1f}%)
• Только один тип пропущен: {missing_hard_only + missing_soft_only:,}
• Оба типа пропущены: {missing_both:,}
"""
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        error_message = f"❌ Ошибка получения статистики: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error in statistic: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Update {update} caused error {context.error}")


def start_background_processing():
    """Запускает фоновую обработку при старте бота"""
    global processing_active, processing_thread
    
    logger.info("Запуск автоматической обработки вакансий...")
    processing_active = True
    processing_thread = threading.Thread(target=process_vacancies_background)
    processing_thread.daemon = True
    processing_thread.start()


def main() -> None:
    """Запуск бота."""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Создаем обработчик для диалога get_by_offset
    get_offset_handler = ConversationHandler(
        entry_points=[CommandHandler("get_by_offset", get_by_offset_start)],
        states={
            GET_OFFSET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_by_offset_handle)]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("get_process", get_process))
    application.add_handler(get_offset_handler)
    application.add_handler(CommandHandler("start_processing", start_processing))
    application.add_handler(CommandHandler("stop_processing", stop_processing))
    application.add_handler(CommandHandler("merge_vacs", merge_vacs))
    application.add_handler(CommandHandler("merge_by_id", merge_by_id))
    application.add_handler(CommandHandler("fill_empty", fill_empty))
    application.add_handler(CommandHandler("stop_fill_empty", stop_fill_empty))
    application.add_handler(CommandHandler("statistic", statistic))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем автоматическую обработку
    start_background_processing()
    
    # Запускаем бота
    logger.info("Запуск бота...")
    logger.info("Автоматическая обработка вакансий запущена!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
