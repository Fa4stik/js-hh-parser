import { transform, isObject, isArray } from 'lodash'
import * as fs from 'node:fs'
import * as path from 'node:path'

export const flattenObject = <T extends object>(obj: T): Record<string, string> => {
	return transform<T, Record<string, string>>(
		obj,
		(result, value, key) => {
			const keyStr = String(key)
			if (isObject(value) && !isArray(value)) {
				const flatObject = flattenObject(value)
				for (const subKey in flatObject) {
					result[`${keyStr}.${subKey}`] = flatObject[subKey]
				}
			} else {
				result[keyStr] = String(value)
			}
		},
		{} as Record<string, string>,
	)
}

const getRandomFromTo = (start: number, end: number) => Math.floor(Math.random() * (end - start + 1)) + start

export const executeWithRetry = async <T>(
	fn: () => Promise<T>,
	[start, end]: [number, number] = [4_000, 5_500],
	retry: number = 999,
): Promise<T | undefined> => {
	let time = 0
	while (retry) {
		try {
			return await fn()
		} catch (err) {
			const error = err as { status: number }
			const retryDelay = getRandomFromTo(start, end)
			console.error(`Error occurred ${error}, retrying in`, retryDelay, 'ms', 'time', ++time)
			console.error(`Err full:`, err)
			retry--
			await waitFor(retryDelay)
		}
	}
	return
}

type Fn<T, TArgs extends unknown[]> = [(...args: TArgs) => Promise<T>, TArgs]
export const chainFnPromises = async <TReturn, TArgs extends unknown[]>(
	promises: Fn<TReturn, TArgs>[],
	kd: number,
	onResolve?: (results: TReturn, fnArgs: TArgs, i?: number) => void,
	isCollect = false,
	retryDelay: [number, number] = [4_000, 5_500],
	retryCount = 20,
) => {
	const values: TReturn[] = []

	let i = 0
	for (const [fn, args] of promises) {
		const result = await executeWithRetry(() => fn(...args), retryDelay, retryCount)
		if (!result) continue
		onResolve && onResolve(result, args, ++i)
		await waitFor(kd)
		;(!onResolve || isCollect) && values.push(result)
	}

	return values
}

export const waitFor = (value: number | [number, number]) =>
	new Promise(r => setTimeout(() => r(''), typeof value === 'number' ? value : getRandomFromTo(value[0], value[1])))

export const convertParamsToQuery = (params: Record<string, string>, ignore: string[]) => {
	const query = new URLSearchParams()
	for (const key in params) {
		if (ignore.includes(key)) continue
		query.append(key, params[key])
	}
	return query.toString()
}

const getCallerName = (): string => {
	const stack = new Error().stack
	if (!stack) return 'unknown'

	const stackLines = stack.split('\n')
	// Пропускаем первую строку (Error), вторую (getCallerName), третью (log) и берем четвертую (вызывающая функция)
	const callerLine = stackLines[3]
	if (!callerLine) return 'unknown'

	// Парсим строку стека для извлечения имени функции
	// Формат: "    at functionName (file:line:column)" или "    at Object.functionName (file:line:column)"
	const match = callerLine.match(/at\s+(?:Object\.)?(\w+)\s*\(/)
	return match ? match[1] : 'unknown'
}

export const log = (...ags: Parameters<typeof console.log>) => {
	const callerName = getCallerName()
	console.log(`[${new Date().toISOString()}]`, `[${callerName}]`, ...ags)
}

export const writeError = ({
	id,
	body,
	message,
	trg,
}: {
	id: string | number
	message: string
	body: object
	trg: 'employer' | 'vac'
}) => {
	const errorsDir = path.resolve(__dirname, '../context/errors')
	if (!fs.existsSync(errorsDir)) {
		fs.mkdirSync(errorsDir, { recursive: true })
	}
	const errorFile = path.resolve(errorsDir, `${trg}_${id}_${Date.now()}.json`)
	fs.writeFileSync(errorFile, JSON.stringify({ id: id, error: message, body }, null, 2))
}
