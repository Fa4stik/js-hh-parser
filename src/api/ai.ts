import { z } from 'zod'
import { apiInstance } from '.'

const ExtractSchema = z.object({
	soft: z.array(z.string()),
	hard: z.array(z.string()),
})

export const extractSkills = async (description: string) =>
	apiInstance(ExtractSchema).post({
		path: 'http://10.230.206.201:8000/api/vacancy',
		body: {
			body: description,
		},
	})
