import { AxiosError } from 'axios'
import { apiInstance } from '.'
import { VacancyExactParams, VacancyExactResponse, VacancyGlobalParams, VacancyGlobalResponse } from '../model'
import { Vacancy, type VacancyGlobal } from '../model/vacancyResponse'
import { HttpsProxyAgent } from 'https-proxy-agent'

export const getVacancies = <TUri extends string>(
	params: Readonly<VacancyGlobalParams>,
	httpsAgent?: HttpsProxyAgent<TUri>,
) => apiInstance(VacancyGlobalResponse).get({ path: `/vacancies`, params, httpsAgent })

export const getVacancy = <TUri extends string>(
	{ id, ...vacancyGlobal }: Readonly<VacancyExactParams & VacancyGlobal>,
	httpsAgent?: HttpsProxyAgent<TUri>,
	onCatch?: <T>(err: AxiosError<T>) => void,
): Promise<Vacancy> =>
	apiInstance(VacancyExactResponse)
		.get({ path: `/vacancies/${id}`, httpsAgent })
		.then(data => Vacancy.parse({ ...data, ...vacancyGlobal }))
		.catch(err => {
			onCatch?.(err)
			throw err
		})
