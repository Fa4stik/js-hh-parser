import { apiInstance } from './index'
import { Company, CompanyPage, CompanyPageSchema, CompanySchema } from '../model/companyResponse'
import { executeWithRetry } from '../utils/helpers'
import { Vacancy } from '../model'
import { HttpsProxyAgent } from 'https-proxy-agent'
import axios from 'axios'
import UserAgent from 'user-agents'
import { JSDOM } from 'jsdom'

export const getEmployer = <TUri extends string>(
	{ id }: { id: number },
	httpsAgent?: HttpsProxyAgent<TUri>,
): Promise<Company> => apiInstance(CompanySchema).get({ path: `/employers/${id}`, httpsAgent })

const userAgent = new UserAgent().data.userAgent
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
