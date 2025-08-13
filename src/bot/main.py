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
        
        message = f"""
📊 Статистика обработки вакансий:

{status_icon} Обработка: {status_text}
✅ Обработано вакансий: {processed_count}
📁 Количество CSV файлов: {len(csv_files)}
📄 Общее количество вакансий: {total_rows}

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
