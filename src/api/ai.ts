import { z } from 'zod'
import { apiInstance } from '.'

type UrlType = 'remote' | 'local'

const ExtractSchema = z.object({
	soft: z.array(z.string()),
	hard: z.array(z.string()),
})

const REMOTE_URL = 'http://10.230.206.201:6381'
const LOCAL_URL = 'http://localhost:6380'
export const extractSkills = async (description: string, urlType: UrlType) =>
	apiInstance(ExtractSchema).post({
		path: (urlType === 'remote' ? REMOTE_URL : LOCAL_URL) + '/api/vacancy',
		body: {
			body: description,
		},
	})
