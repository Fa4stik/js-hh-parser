import ExcelJS from 'exceljs'
import { flattenObject } from './helpers'
import { isArray, isObject } from 'lodash'
import * as fs from 'node:fs'
import { Company } from '../model/companyResponse'
import { vacancyDescription } from '../model/vacancyDescription'
import { companyDescription } from '../model/companyDescription'
import { Vacancy } from '../model'
import * as path from 'node:path'

type ReverseTable = Record<string, number>

const writeRow = <T extends object>(
	data: T,
	worksheet: ExcelJS.Worksheet,
	reverseTable: ReverseTable,
	rowIndex: number,
	parent = '',
) => {
	for (const [key, value] of Object.entries(data)) {
		if ([null, undefined].includes(value)) continue

		if (isObject(value) && !isArray(value)) {
			writeRow(value, worksheet, reverseTable, rowIndex, `${parent}${key}.`)
			continue
		}

		const cell = worksheet.getCell(rowIndex, reverseTable[`${parent}${key}`])
		cell.value = value
	}
}

export const convertVacanciesToExcel = (data: Vacancy[], name: string) => {
	const workbook = new ExcelJS.Workbook()
	const worksheet = workbook.addWorksheet('Vacancies')

	const reverseTable = {} as ReverseTable
	Object.entries(flattenObject(vacancyDescription)).forEach(([key, value], index) => {
		const cell = worksheet.getCell(1, index + 1)
		cell.value = key
		cell.note = value
		reverseTable[key] = index + 1
	})

	data.forEach((vacancy, rowIndex) => {
		writeRow(vacancy, worksheet, reverseTable, rowIndex + 2)
	})

	workbook.xlsx.writeFile(path.resolve(__dirname, `../context/vacs/${name}.xlsx`))
}

export const convertEmployersToExcel = (data: Company[], name: string) => {
	const workbook = new ExcelJS.Workbook()
	const worksheet = workbook.addWorksheet('Companies')

	const reverseTable = {} as ReverseTable
	Object.entries(flattenObject(companyDescription)).forEach(([key, value], index) => {
		const cell = worksheet.getCell(1, index + 1)
		cell.value = key
		cell.note = value
		reverseTable[key] = index + 1
	})

	data.forEach((vacancy, rowIndex) => {
		writeRow(vacancy, worksheet, reverseTable, rowIndex + 2)
	})

	workbook.xlsx.writeFile(path.resolve(__dirname, `../context/employers/${name}.xlsx`))
}

export async function getEmployersFieldFromExcel(
	path: string,
	field: string,
	type: StringConstructor | NumberConstructor = String,
): Promise<(string | number)[] | undefined> {
	const rawBook = fs.readFileSync(path)
	const workbook = new ExcelJS.Workbook()
	await workbook.xlsx.load(rawBook.buffer as ArrayBuffer)

	const worksheet = workbook.getWorksheet(1)
	if (!worksheet) return
	const header = worksheet.getRow(1).values
	if (!header) return

	const fieldColumn = Object.values(header).findIndex(value => value === field)
	const fieldValues = worksheet.getColumn(fieldColumn + 1).values

	// @ts-ignore
	const uniq = Array.from(new Set(fieldValues.map(type).filter(Boolean)))

	if (field === 'employer.name') {
		const dreamjobIdColumn = Object.values(header).findIndex(value => value === 'dreamjob.id')
		if (dreamjobIdColumn === -1) return
		const filteredNames: string[] = []

		for (let i = 2; i <= worksheet.rowCount; i++) {
			const row = worksheet.getRow(i)
			const companyName = row.getCell(fieldColumn + 1).value
			const dreamjobId = row.getCell(dreamjobIdColumn + 1).value

			if (companyName && !dreamjobId) {
				filteredNames.push(String(companyName))
			}
		}

		return Array.from(new Set(filteredNames))
	}

	return uniq
}
