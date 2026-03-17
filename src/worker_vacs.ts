import { HttpsProxyAgent } from 'https-proxy-agent'
import { workerData as _workerData, parentPort } from 'worker_threads'
import { getVacancies, getVacancy } from './api/getVacncies'
import { chainFnPromises, convertParamsToQuery, waitFor } from './utils/helpers'
import { convertVacanciesToExcel } from './utils/converts'
import * as fs from 'node:fs'
import * as path from 'node:path'

export interface IWorkerVacsData {
	path: string
	group: {
		proxy: string
		link: string
	}[]
}
const workerData = _workerData as IWorkerVacsData

type Timestamp = number
const proxyTimeout = new Map<string, Timestamp>()
const OFFSET = 5_000

;(async () => {
	for (const { link, proxy } of workerData.group) {
		const timeout = proxyTimeout.get(proxy)
		if (timeout && timeout - Date.now() > 0) {
			const kd = timeout - Date.now()
			parentPort?.postMessage(`TIMEOUT FOR THE PROXY ${proxy} BETWEEN ${kd} AND ${kd + OFFSET}`)
			await waitFor([kd, kd + OFFSET])
			proxyTimeout.delete(proxy)
		}

		const [login, pass, ip, port] = proxy.split('@').flatMap(v => v.split(':'))
		const proxyUrl = `http://${login}:${pass}@${ip}:${port}`
		const httpsAgent = new HttpsProxyAgent(proxyUrl)

		const url = new URL(link)
		const params = Object.fromEntries(url.searchParams.entries())
		const logParams = Object.entries(params)
			.flatMap(([key, value]) =>
				(key === 'area' && value === '113') || key === 'clusters' || key === 'per_page' ? [] : [`[${key}=${value}]`],
			)
			.join(' ')

		getVacancies(params, httpsAgent).then(async ({ items, page, pages }) => {
			if (items.length === 0) return
			const firstHundredPromises: [typeof getVacancy, Parameters<typeof getVacancy>][] = items.map(vacancy => [
				getVacancy,
				[
					vacancy,
					httpsAgent,
					(err: Error) => {
						const errorsDir = path.resolve(__dirname, './context/errors')
						if (!fs.existsSync(errorsDir)) {
							fs.mkdirSync(errorsDir, { recursive: true })
						}
						const errorFile = path.resolve(errorsDir, `${vacancy.id}_${Date.now()}.json`)
						fs.writeFileSync(errorFile, JSON.stringify({ id: vacancy.id, error: err.message, body: err }, null, 2))

						parentPort?.postMessage(
							`ERROR FOR VACANCY ID ${vacancy.id} BY PARAMS ${logParams}, DESC ${err}, NEXT RETRY BETWEEN 15s AND 30s, PROXY ${proxy}`,
						)
					},
				],
			])
			const firstHundred = await chainFnPromises(firstHundredPromises, 500, undefined, false, [15_000, 30_000])
			parentPort?.postMessage(`PROGRESS ${page}/${pages} OF PARAMS ${logParams}`)
			convertVacanciesToExcel(firstHundred, `${convertParamsToQuery(params, ['clusters'])}`)
			proxyTimeout.set(proxy, Date.now() + 1_000 * 60)
			parentPort?.postMessage('HANDLED PR ID' + params.professional_role)
		})
	}
})()
