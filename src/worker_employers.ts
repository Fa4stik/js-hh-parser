import { workerData as _workerData, parentPort } from 'worker_threads'
import { HttpsProxyAgent } from 'https-proxy-agent'
import { getEmployer } from './api/getEmployer'
import { chainFnPromises } from './utils/helpers'
import { convertEmployersToExcel } from './utils/converts'

export interface IWorkerEmployerData {
	path: string
	group: {
		proxy: string
		ids: number[]
	}[]
}
const workerData = _workerData as IWorkerEmployerData

workerData.group.forEach(({ proxy, ids }, i) => {
	const [login, pass, ip, port] = proxy.split('@').flatMap(v => v.split(':'))
	const proxyUrl = `http://${login}:${pass}@${ip}:${port}`
	const httpsAgent = new HttpsProxyAgent(proxyUrl)
	parentPort?.postMessage(`start for ${proxyUrl}, amount ${ids.length}`)
	const promises = ids.map(id => [getEmployer, [{ id }, httpsAgent]])
	// @ts-ignore
	chainFnPromises(promises, 0).then(employers => {
		const filteredEmployers = employers.filter(e => e !== 'not found')
		parentPort?.postMessage(`done for ${ip}_${port}. Filtered ${employers.length - filteredEmployers.length}`)
		convertEmployersToExcel(filteredEmployers, `${ip}_${port}_${i}`)
	})
})
