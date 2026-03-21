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

export async function getFieldFromExcel<T extends string>(
	path: string,
	fields: {
		key: T
		type: StringConstructor | NumberConstructor
	}[],
): Promise<Record<T, string | number>[] | undefined> {
	const rawBook = fs.readFileSync(path)
	const workbook = new ExcelJS.Workbook()
	await workbook.xlsx.load(rawBook.buffer as ArrayBuffer)

	const worksheet = workbook.getWorksheet(1)
	if (!worksheet) return
	const header = worksheet.getRow(1).values
	if (!header) return

	const headerValues = Object.values(header) as string[]
	const fieldColumns = fields.map(f => ({
		...f,
		column: headerValues.findIndex(value => value === f.key),
	}))

	if (fieldColumns.some(f => f.column === -1)) return

	const results: Record<string, string | number>[] = []

	for (let i = 2; i <= worksheet.rowCount; i++) {
		const row = worksheet.getRow(i)
		const obj: Record<string, string | number> = {}

		for (const f of fieldColumns) {
			const raw = row.getCell(f.column + 1).value
			if (raw == null) continue
			obj[f.key] = f.type(raw as any) as string | number
		}

		if (Object.keys(obj).length > 0) {
			results.push(obj)
		}
	}

	return results
}

const SKILLS_HEADERS = ['id', 'soft', 'hard'] as const
export async function createSkillsExcel(filePath: string) {
	const workbook = new ExcelJS.Workbook()
	const worksheet = workbook.addWorksheet('Skills')
	SKILLS_HEADERS.forEach((h, i) => {
		worksheet.getCell(1, i + 1).value = h
	})
	await workbook.xlsx.writeFile(filePath)
	return workbook
}

export async function getProcessedSkillIds(filePath: string): Promise<Set<number>> {
	if (!fs.existsSync(filePath)) return new Set()
	const rawBook = fs.readFileSync(filePath)
	const workbook = new ExcelJS.Workbook()
	await workbook.xlsx.load(rawBook.buffer as ArrayBuffer)
	const worksheet = workbook.getWorksheet(1)
	if (!worksheet) return new Set()

	const ids = new Set<number>()
	for (let i = 2; i <= worksheet.rowCount; i++) {
		const val = worksheet.getRow(i).getCell(1).value
		if (val != null) ids.add(Number(val))
	}
	return ids
}

export async function appendSkillRow(filePath: string, rowIndex: number, id: number, soft: string[], hard: string[]) {
	const workbook = new ExcelJS.Workbook()
	if (fs.existsSync(filePath)) {
		const rawBook = fs.readFileSync(filePath)
		await workbook.xlsx.load(rawBook.buffer as ArrayBuffer)
	}
	const worksheet = workbook.getWorksheet(1)!
	worksheet.getCell(rowIndex, 1).value = id
	worksheet.getCell(rowIndex, 2).value = soft.join(', ')
	worksheet.getCell(rowIndex, 3).value = hard.join(', ')
	await workbook.xlsx.writeFile(filePath)
}
