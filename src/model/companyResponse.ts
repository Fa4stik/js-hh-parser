import { z } from 'zod'
import { IdNamedSchema } from './common'

const BrandingConstructor = z.object({
	constructor: z.object({
		url: z.string(),
		header_picture: z
			.object({
				resized_path: z.string(),
			})
			.nullable(),
		widgets: z
			.object({
				items: z
					.object({
						picture_id: z.number(),
						resized_path: z.string(),
					})
					.array(),
				type: z.string(),
			})
			.array()
			.optional(),
	}),
})

const BrandingCustom = z.object({
	makeup: z
		.object({
			url: z.string(),
		})
		.optional(),
	template_version_id: z.string().optional(),
	template_code: z.string().optional(),
})

export const CompanySchema = z.object({
	accredited_it_employer: z.boolean(),
	alternate_url: z.string(),
	applicant_services: z
		.object({
			target_employer: z.object({
				count: z.number(),
			}),
		})
		.optional(),
	area: z.object({
		id: z.string(),
		name: z.string(),
		url: z.string(),
	}),
	branding: z.union([BrandingConstructor, BrandingCustom]).nullable().optional(),
	description: z.string().nullable().optional(),
	id: z.string(),
	industries: IdNamedSchema.array(),
	insider_interviews: z
		.object({
			id: z.string(),
			title: z.string(),
			url: z.string(),
		})
		.array(),
	logo_urls: z
		.object({
			'90': z.string().optional(),
			'240': z.string().optional(),
			original: z.string(),
		})
		.nullable()
		.optional(),
	name: z.string(),
	open_vacancies: z.number().nullable().optional(),
	relations: z.string().array().nullable(),
	site_url: z.string(),
	trusted: z.boolean(),
	type: z.string().nullable(),
	vacancies_url: z.string(),
})
export type Company = z.infer<typeof CompanySchema>

export const CompanyPageSchema = z.object({
	id: z.string(),
	html: z.string(),
})
export type CompanyPage = z.infer<typeof CompanyPageSchema>
