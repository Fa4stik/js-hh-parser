import * as ExcelJS from 'exceljs';
import * as cheerio from 'cheerio';
import * as path from 'path';

// Интерфейс для результатов анализа
interface AnalysisResult {
  averageCharacterLength: number;
  averageWordCount: number;
  totalRecords: number;
  processedRecords: number;
}

// Функция для очистки HTML тегов из текста
function cleanHtmlTags(htmlString: string): string {
  if (!htmlString || typeof htmlString !== 'string') {
    return '';
  }
  
  // Используем cheerio для парсинга HTML и извлечения только текста
  const $ = cheerio.load(htmlString);
  return $.text().trim();
}

// Функция для подсчета слов в тексте
function countWords(text: string): number {
  if (!text || typeof text !== 'string') {
    return 0;
  }
  
  // Убираем лишние пробелы и разбиваем по словам
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

// Функция для анализа колонки description
async function analyzeDescriptionColumn(): Promise<AnalysisResult> {
  const workbook = new ExcelJS.Workbook();
  const filePath = path.resolve('merged_vacs.xlsx');
  
  try {
    // Читаем Excel файл
    await workbook.xlsx.readFile(filePath);
    
    // Получаем первый лист
    const worksheet = workbook.worksheets[0];
    
    if (!worksheet) {
      throw new Error('Лист не найден в Excel файле');
    }
    
    // Находим колонку description
    const headerRow = worksheet.getRow(1);
    let descriptionColumnIndex = -1;
    
    headerRow.eachCell((cell, colNumber) => {
      if (cell.value && cell.value.toString().toLowerCase().includes('description')) {
        descriptionColumnIndex = colNumber;
      }
    });
    
    if (descriptionColumnIndex === -1) {
      throw new Error('Колонка description не найдена');
    }
    
    console.log(`Найдена колонка description в позиции: ${descriptionColumnIndex}`);
    
    // Собираем данные для анализа
    const cleanedTexts: string[] = [];
    let totalRecords = 0;
    let processedRecords = 0;
    
    // Проходим по всем строкам, начиная со второй (пропускаем заголовок)
    for (let rowNumber = 2; rowNumber <= worksheet.rowCount; rowNumber++) {
      const row = worksheet.getRow(rowNumber);
      const cell = row.getCell(descriptionColumnIndex);
      
      totalRecords++;
      
      if (cell.value) {
        const htmlContent = cell.value.toString();
        const cleanedText = cleanHtmlTags(htmlContent);
        
        if (cleanedText.length > 0) {
          cleanedTexts.push(cleanedText);
          processedRecords++;
        }
      }
    }
    
    console.log(`Обработано записей: ${processedRecords} из ${totalRecords}`);
    
    // Подсчитываем статистику
    if (cleanedTexts.length === 0) {
      return {
        averageCharacterLength: 0,
        averageWordCount: 0,
        totalRecords,
        processedRecords: 0
      };
    }
    
    // Считаем среднюю длину символов
    const totalCharacters = cleanedTexts.reduce((sum, text) => sum + text.length, 0);
    const averageCharacterLength = totalCharacters / cleanedTexts.length;
    
    // Считаем среднее количество слов
    const totalWords = cleanedTexts.reduce((sum, text) => sum + countWords(text), 0);
    const averageWordCount = totalWords / cleanedTexts.length;
    
    return {
      averageCharacterLength: Math.round(averageCharacterLength * 100) / 100,
      averageWordCount: Math.round(averageWordCount * 100) / 100,
      totalRecords,
      processedRecords
    };
    
  } catch (error) {
    console.error('Ошибка при чтении файла:', error);
    throw error;
  }
}

// Основная функция для запуска анализа
export async function runAnalysis(): Promise<void> {
  try {
    console.log('Начинаю анализ файла merged_vacs.xlsx...\n');
    
    const result = await analyzeDescriptionColumn();
    
    console.log('=== РЕЗУЛЬТАТЫ АНАЛИЗА ===');
    console.log(`Общее количество записей: ${result.totalRecords}`); // 56,057
    console.log(`Обработано записей с description: ${result.processedRecords}`); // 56,057
    console.log(`Средняя длина текста (символы): ${result.averageCharacterLength}`); // 1,902.87
    console.log(`Среднее количество слов: ${result.averageWordCount}`); // 236.39
    console.log('========================\n');
    
  } catch (error) {
    console.error('Произошла ошибка при анализе:', error);
  }
}

// Если файл запущен напрямую, выполняем анализ
if (require.main === module) {
  runAnalysis();
}
