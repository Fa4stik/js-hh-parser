import { z } from 'zod'

const VacancyExactParamsSchema = z.object({
	id: z.string(),
})
export type VacancyExactParams = z.infer<typeof VacancyExactParamsSchema>

const VacancyGlobalParamsSchema = z
	.object({
		page: z.number().max(20),
		per_page: z.number().max(100),
		text: z.string(),
		search_field: z.string(), //  /dictionaries => vacancy_search_fields
		experience: z.string(), // /dictionaries => id from experience
		employment: z.string(), // /dictionaries => id from employment
		schedule: z.string(), // /dictionaries => id from schedule
		area: z.string(), // /areas => id
		metro: z.string(), // /metro => id
		professional_role: z.string().or(z.string().array()), // /professional_roles => id
		industry: z.string(), // /industries => id
		employer_id: z.string(),
		currency: z.string(), // /dictionaries => code from currency
		salary: z.number(),
		label: z.string(), // /dictionaries => id from vacancy_label
		only_with_salary: z.boolean(),
		period: z.number(),
		date_from: z.string(), // ISO 8601. Incompatible with period
		date_to: z.string(), // ISO 8601. Incompatible with period
		top_lat: z.number(),
		bottom_lat: z.number(),
		left_lng: z.number(),
		right_lng: z.number(),
		order_by: z.string(), // /dictionaries => id from vacancy_search_order
		sort_point_lat: z.number(),
		sort_point_lng: z.number(),
		clusters: z.boolean(),
		describe_arguments: z.boolean(),
		no_magic: z.boolean(),
		premium: z.boolean(),
		responses_count_enabled: z.boolean(),
		part_time: z.string(), // /dictionaries => working_days, working_time_intervals, working_time_modes, part, project, employment, accept_temporary
		accept_temporary: z.boolean(),
		locale: z.string(), // /locales => id
		host: z.string(), // hh.ru, rabota.by, hh1.az, hh.uz, hh.kz, headhunter.ge, headhunter.kg,
	})
	.partial()
export type VacancyGlobalParams = z.infer<typeof VacancyGlobalParamsSchema>
