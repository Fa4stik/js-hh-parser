import ExcelJS from 'exceljs'
import * as cheerio from 'cheerio'
import * as path from 'path'
import * as fs from 'fs'
import { extractSkills } from '../api/ai'

// Функция для очистки HTML тегов из текста
function cleanHtmlTags(htmlString: string): string {
	if (!htmlString || typeof htmlString !== 'string') {
		return ''
	}

	const $ = cheerio.load(htmlString)
	return $.text().trim()
}

// Функция для экранирования CSV значений
function escapeCsvValue(value: string): string {
	if (!value) return ''
	// Экранируем кавычки и оборачиваем в кавычки если есть запятые или переносы строк
	if (value.includes(',') || value.includes('\n') || value.includes('"')) {
		return `"${value.replace(/"/g, '""')}"`
	}
	return value
}

// Интерфейс для данных обрабатываемой записи
interface ProcessingRecord {
	vacancyId: string
	rowNumber: number
	htmlContent: string
	cleanedDescription: string
}

// Основная функция для обработки первых 10 описаний вакансий
export async function processVacancyDescriptions(): Promise<void> {
	const workbook = new ExcelJS.Workbook()
	const inputFilePath = path.resolve('merged_vacs.xlsx')
	const outputFilePath = path.resolve('processed_vacancies.csv')

	return workbook.xlsx
		.readFile(inputFilePath)
		.then(() => {
			console.log('Excel файл прочитан')

			const worksheet = workbook.worksheets[0]
			if (!worksheet) {
				throw new Error('Лист не найден в Excel файле')
			}

			// Находим необходимые колонки
			const headerRow = worksheet.getRow(1)
			let descriptionColumnIndex = -1
			let idColumnIndex = -1

			headerRow.eachCell((cell, colNumber) => {
				const cellValue = cell.value?.toString().toLowerCase() || ''
				if (cellValue.includes('description')) {
					descriptionColumnIndex = colNumber
				}
				if (cellValue.includes('id') && !cellValue.includes('employer')) {
					idColumnIndex = colNumber
				}
			})

			if (descriptionColumnIndex === -1) {
				throw new Error('Колонка description не найдена')
			}

			if (idColumnIndex === -1) {
				throw new Error('Колонка id не найдена')
			}

			console.log(`Найдена колонка description в позиции: ${descriptionColumnIndex}`)
			console.log(`Найдена колонка id в позиции: ${idColumnIndex}`)

			// Собираем данные для обработки (первые 10 записей)
			const recordsToProcess: ProcessingRecord[] = []
			const maxRows = Math.min(11, worksheet.rowCount) // 11 потому что первая строка - заголовки

			for (let rowNumber = 2; rowNumber <= maxRows && recordsToProcess.length < 10; rowNumber++) {
				const row = worksheet.getRow(rowNumber)
				const descriptionCell = row.getCell(descriptionColumnIndex)
				const idCell = row.getCell(idColumnIndex)

				if (descriptionCell.value && idCell.value) {
					const htmlContent = descriptionCell.value.toString()
					const cleanedDescription = cleanHtmlTags(htmlContent)
					const vacancyId = idCell.value.toString()

					if (cleanedDescription.length > 0) {
						recordsToProcess.push({
							vacancyId,
							rowNumber,
							htmlContent,
							cleanedDescription,
						})
					}
				}
			}

			console.log(`Подготовлено ${recordsToProcess.length} записей для параллельной обработки`)

			// Создаем параллельные запросы к API
			const apiPromises = recordsToProcess.map((record, index) => {
				console.log(`Отправляю запрос ${index + 1}/${recordsToProcess.length}`)

				return extractSkills(record.cleanedDescription)
					.then(response => ({
						...record,
						success: true,
						skills: response.data,
					}))
					.catch(error => {
						console.error(`Ошибка при обработке записи ${index + 1}:`, error)
						return {
							...record,
							success: false,
							skills: { hard: [], soft: [] },
						}
					})
			})

			// Ждем завершения всех запросов
			return Promise.all(apiPromises).then(results => {
				console.log('Все запросы завершены, создаю CSV файл...')

				// Создаем CSV контент
				const csvHeaders = 'id,description,hard_skills,soft_skills\n'
				const csvRows = results
					.map(result => {
						const hardSkills = result.skills?.hard ? result.skills.hard.join(', ') : ''
						const softSkills = result.skills?.soft ? result.skills.soft.join(', ') : ''

						return [
							escapeCsvValue(result.vacancyId),
							escapeCsvValue(result.cleanedDescription),
							escapeCsvValue(hardSkills),
							escapeCsvValue(softSkills),
						].join(',')
					})
					.join('\n')

				const csvContent = csvHeaders + csvRows

				// Записываем CSV файл
				return new Promise<void>((resolve, reject) => {
					fs.writeFile(outputFilePath, csvContent, 'utf8', err => {
						if (err) {
							reject(err)
						} else {
							resolve()
						}
					})
				}).then(() => {
					console.log(`CSV файл создан: ${outputFilePath}`)
					console.log(`Обработано записей: ${results.length}`)

					// Выводим статистику
					const successfulCount = results.filter(r => r.success).length
					console.log(`Успешно обработано: ${successfulCount}/${results.length}`)

					const totalHardSkills = results.reduce((sum, r) => sum + (r.skills?.hard?.length || 0), 0)
					const totalSoftSkills = results.reduce((sum, r) => sum + (r.skills?.soft?.length || 0), 0)

					console.log(`Всего извлечено технических навыков: ${totalHardSkills}`)
					console.log(`Всего извлечено мягких навыков: ${totalSoftSkills}`)
				})
			})
		})
		.catch(error => {
			console.error('Ошибка при обработке файла:', error)
			throw error
		})
}

// Функция для запуска обработки
if (require.main === module) {
	processVacancyDescriptions().catch(console.error)
}
