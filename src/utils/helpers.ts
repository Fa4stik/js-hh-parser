import { transform, isObject, isArray } from 'lodash'

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

type Fn<T, K> = [(...args: K[]) => Promise<T>, args: K[]]
export const chainFnPromises = async <TReturn, TArgs>(
	promises: Fn<TReturn, TArgs>[],
	kd: number,
	onResolve?: (results: TReturn, fnArgs: TArgs[]) => void,
) => {
	const values: TReturn[] = []

	let i = 0
	for (const [fn, args] of promises) {
		const result = await executeWithRetry(() => fn(...args), [4_000, 5_500], 20)
		if (!result) continue
		onResolve && onResolve(result, args)
		console.log(`chain value of ${++i} to ${promises.length}`)
		await waitFor(kd)
		!onResolve && values.push(result)
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
