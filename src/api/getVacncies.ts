import { apiInstance } from '.'
import { VacancyExactParams, VacancyExactResponse, VacancyGlobalParams, VacancyGlobalResponse } from '../model'
import { Vacancy, type VacancyGlobal } from '../model/vacancyResponse'
import { executeWithRetry } from '../utils/helpers'
import { HttpsProxyAgent } from 'https-proxy-agent'

export const getVacancies = <TUri extends string>(
	params: Readonly<VacancyGlobalParams>,
	httpsAgent?: HttpsProxyAgent<TUri>,
) => apiInstance(VacancyGlobalResponse).get({ path: `/vacancies`, params, httpsAgent })

export const getVacancy = <TUri extends string>(
	{ id, ...vacancyGlobal }: Readonly<VacancyExactParams & VacancyGlobal>,
	httpsAgent?: HttpsProxyAgent<TUri>,
): Promise<Vacancy> =>
	apiInstance(VacancyExactResponse)
		.get({ path: `/vacancies/${id}`, httpsAgent })
		.then(data => Vacancy.parse({ ...data, ...vacancyGlobal }))
		.catch(async () => {
			console.log('catch for', id)
			const res = await executeWithRetry<Vacancy>(() => getVacancy({ id, ...vacancyGlobal }, httpsAgent))
			return res ?? ({} as Vacancy)
		})
