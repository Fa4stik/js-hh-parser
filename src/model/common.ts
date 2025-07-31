import { z } from 'zod'
import { getRecord } from './helpers'

export type ChangeTypes<T> = {
	[K in keyof T]: NonNullable<T[K]> extends object
		? NonNullable<T[K]> extends Array<infer U>
			? string
			: ChangeTypes<T[K]>
		: string
}

export const IdNamedSchema = z.object({}).merge(getRecord(['id', 'name'] as const, z.string()))
export const IdSchema = z.object({ id: z.string() })
