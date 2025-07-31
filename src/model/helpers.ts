import { z } from 'zod'

type ZodObjectKeys = z.ZodBoolean | z.ZodNumber | z.ZodString
export const getRecord = <T extends string[], K extends z.ZodNullable<ZodObjectKeys> | ZodObjectKeys>(keys: T, type: K) =>
	z.object(
		keys.reduce(
			(acc, key) => {
				acc[key as T[number]] = type
				return acc
			},
			{} as Record<T[number], K>,
		),
	)

export const getLiteralUnion = <T extends string[]>(literals: T) => z.union(literals.map(l => z.literal(l)) as [z.ZodLiteral<T[number]>, z.ZodLiteral<T[number]>, ...z.ZodLiteral<T[number]>[]])