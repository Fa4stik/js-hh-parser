import { HttpsProxyAgent } from 'https-proxy-agent'
import { workerData as _workerData, parentPort } from 'worker_threads'
import { getVacancies, getVacancy } from './api/getVacncies'
import { convertParamsToQuery, waitFor } from './utils/helpers'
import { chainFnPromises } from './utils/helpers'
import { convertVacanciesToExcel } from './utils/converts'

export interface IWorkerVacsData {
	path: string
	group: {
		proxy: string
		link: string
	}[]
}
const workerData = _workerData as IWorkerVacsData

workerData.group.forEach(({ link, proxy }) => {
	const [login, pass, ip, port] = proxy.split('@').flatMap(v => v.split(':'))
	const proxyUrl = `http://${login}:${pass}@${ip}:${port}`
	const httpsAgent = new HttpsProxyAgent(proxyUrl)

	const url = new URL(link)
	const params = Object.fromEntries(url.searchParams.entries())
	getVacancies(params, httpsAgent).then(async ({ found }) => {
		const pages = Math.ceil(found / 100)
		const globalVacanciesPromises: [typeof getVacancies, Parameters<typeof getVacancies>][] = Array.from(
			{ length: pages },
			(_, i) => i + 1,
		).map(page => [getVacancies, [{ ...params, page }, httpsAgent]])
		// @ts-ignore
		const globalVacancies = await chainFnPromises(globalVacanciesPromises, 2_500)

		let progress = 0
		for (const { items } of globalVacancies) {
			const firstHundredPromises = items.map(vacancy => getVacancy(vacancy, httpsAgent))
			const firstHundred = await Promise.all(firstHundredPromises)
			parentPort?.postMessage(`progress of role ${params.professional_role} | ${++progress}/${globalVacancies.length}`)
			convertVacanciesToExcel(firstHundred, `${convertParamsToQuery(params, ['clusters', 'per_page'])}_${progress}`)
			await waitFor([60_000, 65_000])
		}

		parentPort?.postMessage('done for ' + params.professional_role)
	})
})
