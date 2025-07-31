import 'dotenv/config'

import { z } from 'zod'
import axios from 'axios'
import qs from 'qs'
import { HttpsProxyAgent } from 'https-proxy-agent'

class BaseApi<TSchema extends z.ZodRawShape, TUri extends string = ''> {
	baseUrl = process.env.API_HH_URL
	schema: z.ZodObject<TSchema>

	constructor(schema: z.ZodObject<TSchema>) {
		this.schema = schema
	}

	get<TParams extends object>({
		path,
		params,
		httpsAgent,
	}: {
		path: string
		params?: TParams
		httpsAgent?: HttpsProxyAgent<TUri>
	}) {
		return axios
			.get(`${this.baseUrl}${path}`, {
				params,
				paramsSerializer: params => qs.stringify(params, { arrayFormat: 'repeat' }),
				httpsAgent,
			})
			.then(({ data, config: { url, params } }) =>
				this.schema.parse({ ...data, url: `${url}?${new URLSearchParams(params)}` }),
			)
	}
}

export default <TSchema extends z.ZodRawShape>(schema: z.ZodObject<TSchema>) => new BaseApi(schema)
