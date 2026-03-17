import 'dotenv/config'

import { z } from 'zod'
import axios from 'axios'
import qs from 'qs'
import { HttpsProxyAgent } from 'https-proxy-agent'
import UserAgent from 'user-agents'

class BaseApi<TSchema extends z.ZodRawShape, TUri extends string = ''> {
	baseUrl = process.env.API_HH_URL
	schema: z.ZodObject<TSchema>

	constructor(schema: z.ZodObject<TSchema>) {
		this.schema = schema
	}

	private getHeaders() {
		const userAgent = new UserAgent().data.userAgent
		return {
			'User-Agent': userAgent,
			Accept: 'application/json, text/plain, */*',
			'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
			Referer: 'https://hh.ru/',
			Origin: 'https://hh.ru',
		}
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
				headers: this.getHeaders(),
			})
			.then(({ data, config: { url, params } }) =>
				this.schema.parse({ ...data, url: `${url}?${new URLSearchParams(params)}` }),
			)
	}

	post<TBody extends object>({
		path,
		body,
		httpsAgent,
	}: {
		path: string
		body?: TBody
		httpsAgent?: HttpsProxyAgent<TUri>
	}) {
		return axios.post(`${path.includes('http') ? '' : this.baseUrl}${path}`, body, {
			httpsAgent,
			headers: this.getHeaders(),
		})
	}
}

export default <TSchema extends z.ZodRawShape>(schema: z.ZodObject<TSchema>) => new BaseApi(schema)
