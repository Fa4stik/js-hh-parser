import { z } from 'zod'
import { getLiteralUnion, getRecord } from './helpers'
import { IdNamedSchema, IdSchema } from './common'

const AreaSchema = z
	.object({})
	.merge(IdNamedSchema)
	.merge(getRecord(['url'] as const, z.string()))

const LatLnSchema = z.object({}).merge(getRecord(['lat', 'lng'] as const, z.number().nullable()))

const MetroSchema = z
	.object({})
	.merge(LatLnSchema)
	.merge(getRecord(['line_id', 'line_name', 'station_id', 'station_name'] as const, z.string()))

const AddressSchema = z
	.object({})
	.merge(LatLnSchema)
	.merge(getRecord(['building', 'city', 'description', 'raw', 'street'] as const, z.string().nullable()))

const ralations = getLiteralUnion([
	'favorited',
	'got_response',
	'got_invitation',
	'got_rejection',
	'blacklisted',
	'got_question',
] as const)
const RelationsSchema = ralations.array()

const VacancyCommon = z.object({
	accept_incomplete_resumes: z.boolean(),
	accept_temporary: z.boolean().nullable(),
	address: AddressSchema.nullable(),
	alternate_url: z.string(),
	apply_alternate_url: z.string(),
	archived: z.boolean(),
	area: AreaSchema,
	contacts: z
		.object({
			call_tracking_enabled: z.boolean().nullable(),
			email: z.string().nullable(),
			name: z.string().nullable(),
			phones: z
				.object({
					country: z.string(),
					city: z.string(),
					number: z.string(),
					formatted: z.string(),
					comment: z.string().nullable(),
				})
				.array()
				.nullable(),
		})
		.nullable(),
	department: IdNamedSchema.nullable(),
	employer: z.object({
		alternate_url: z.string().optional(),
		id: z.string().nullable().optional(),
		logo_urls: z
			.object({
				'90': z.string().optional(),
				'240': z.string().optional(),
				original: z.string().optional(),
			})
			.nullable()
			.optional(),
		name: z.string(),
		trusted: z.boolean(),
		url: z.string().optional(),
		vacancies_url: z.string().optional(),
	}),
	employment_form: IdNamedSchema.nullable(),
	experience: IdNamedSchema.nullable(),
	fly_in_fly_out_duration: IdNamedSchema.array().nullable(),
	has_test: z.boolean(),
	id: z.string(),
	insider_interview: z
		.object({
			id: z.string(),
			url: z.string(),
		})
		.nullable(),
	internship: z.boolean().nullable(),
	name: z.string(),
	night_shifts: z.boolean().nullable(),
	premium: z.boolean(),
	professional_roles: IdNamedSchema.array(),
	published_at: z.string(),
	relations: RelationsSchema,
	response_letter_required: z.boolean(),
	response_url: z.string().nullable(),
	salary: z
		.object({
			currency: z.string().nullable(),
			from: z.number().nullable(),
			gross: z.boolean().nullable(),
			to: z.number().nullable(),
		})
		.nullable(),
	type: IdNamedSchema,
	video_vacancy: z
		.object({
			snippet_picture_url: z.string().nullable(),
			snippet_video_url: z.string().nullable(),
			video_url: z.string(),
			cover_picture: z.object({
				resized_height: z.number(),
				resized_width: z.number(),
				resized_path: z.string(),
			}),
		})
		.nullable()
		.optional(),
	work_format: IdNamedSchema.array().nullable(),
	work_schedule_by_days: IdNamedSchema.array().nullable(),
	working_hours: IdNamedSchema.array().nullable(),
})

// /vacancies/:id
export const VacancyExactResponse = z
	.object({
		accept_handicapped: z.boolean(),
		accept_kids: z.boolean(),
		allow_messages: z.boolean(),
		approved: z.boolean(),
		billing_type: IdSchema.nullable(),
		code: z.string().nullable(),
		description: z.string(),
		driver_license_types: z
			.object({
				id: z.string(),
			})
			.array()
			.nullable(),
		initial_created_at: z.string(),
		key_skills: z
			.object({
				name: z.string(),
			})
			.array(),
		languages: z
			.object({
				id: z.string(),
				level: IdNamedSchema,
				name: z.string(),
			})
			.array()
			.nullable(),
		negotiations_url: z.string().nullable(),
		suitable_resumes_url: z.string().nullable(),
		test: z
			.object({
				id: z.string().nullable().optional(),
				required: z.boolean().nullable(),
			})
			.nullable(),
	})
	.merge(VacancyCommon)

const VacancyGlobal = z.object({
	created_at: z.string(),
	metro_stations: MetroSchema.optional(),
	sort_point_distance: z.number().nullable(),
	url: z.string(),
	counters: z
		.object({
			responses: z.number(),
			total_responses: z.number(),
		})
		.optional(),
	snippet: z.object({
		requirement: z.string().nullable(),
		responsibility: z.string().nullable(),
	}),
	show_logo_in_search: z.boolean().nullable().optional(),
})
export type VacancyGlobal = z.infer<typeof VacancyGlobal>

// /vacancies
export const VacancyGlobalResponse = z.object({
	items: VacancyGlobal.merge(VacancyCommon).array(),
	found: z.number(),
	page: z.number(),
	pages: z.number(),
	per_page: z.number(),
	url: z.string(),
	clusters: z
		.object({
			id: z.string(),
			name: z.string(),
			items: z
				.object({
					count: z.number(),
					metro_line: z
						.object({
							area: AreaSchema,
							hex_color: z.string(),
							id: z.string(),
						})
						.nullable()
						.optional(),
					metro_station: z
						.object({
							area: AreaSchema,
							hex_color: z.string(),
							id: z.string(),
							lat: z.number(),
							lng: z.number(),
							order: z.number(),
						})
						.nullable()
						.optional(),
					name: z.string(),
					url: z.string(),
					type: z.string().nullable().optional(),
				})
				.array(),
		})
		.array()
		.nullable(),
	arguments: z
		.object({
			argument: z.string(),
			cluster_group: z
				.object({
					id: z.string(),
					name: z.string(),
				})
				.nullable(),
			disable_url: z.string(),
			hex_color: z.string().nullable().optional(),
			metro_type: z.string().nullable().optional(),
			name: z.string().nullable().optional(),
			value: z.string(),
			value_description: z.string().nullable(),
		})
		.array()
		.nullable(),
	alternate_url: z.string().nullable(),
	fixes: z
		.object({
			fixed: z.string(),
			original: z.string(),
		})
		.nullable(),
	suggests: z
		.object({
			found: z.number(),
			value: z.string(),
		})
		.nullable(),
})

export const Vacancy = z.object({}).merge(VacancyExactResponse).merge(VacancyGlobal)
export type Vacancy = z.infer<typeof Vacancy>
