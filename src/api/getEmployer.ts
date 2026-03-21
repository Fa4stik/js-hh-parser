import { apiInstance } from './index'
import { Company, CompanyPage, CompanyPageSchema, CompanySchema } from '../model/companyResponse'
import { HttpsProxyAgent } from 'https-proxy-agent'
import axios, { AxiosError } from 'axios'
import UserAgent from 'user-agents'
import { JSDOM } from 'jsdom'
import { writeError } from '../utils/helpers'

export const getEmployer = <TUri extends string>(
	{ id }: { id: number },
	httpsAgent?: HttpsProxyAgent<TUri>,
): Promise<Company | 'not found'> =>
	apiInstance(CompanySchema)
		.get({ path: `/employers/${id}`, httpsAgent })
		.catch((err: AxiosError<object>) => {
			writeError({ id, message: err.message, body: err.response?.data as object, trg: 'employer' })
			if (err.status === 404) return 'not found' as const
			return Promise.reject(err)
		})

export const getEmployerPage = <TUri extends string>(
	{ query }: { query: string },
	httpsAgent?: HttpsProxyAgent<TUri>,
): Promise<CompanyPage | void> => {
	console.log('sv link to check', `https://dreamjob.ru/site/search-all?query=${encodeURI(query)}`)
	return axios
		.get(`https://dreamjob.ru/site/search-all?query=${encodeURI(query)}`, {
			httpsAgent,
			headers: {
				'User-Agent': new UserAgent().data.userAgent,
				Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9',
			},
		})
		.then(({ data }) => {
			const dom = new JSDOM(data)
			const document = dom.window.document
			const companyLink = (document.querySelector('a[data-pjax]') as HTMLAnchorElement | undefined)?.href

			if (!companyLink) return
			const id = (companyLink.match(/((?<=\/)\d+)/i) ?? [])[0]

			return axios
				.get(`https://dreamjob.ru${companyLink}/career`, {
					httpsAgent,
					headers: {
						'User-Agent': new UserAgent().data.userAgent,
						Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9',
					},
				})
				.then(({ data }) =>
					CompanyPageSchema.parse({
						id,
						html: data,
					}),
				)
		})
}
