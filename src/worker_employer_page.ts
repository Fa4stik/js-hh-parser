import { workerData as _workerData } from 'worker_threads'
import { IWorkerEmployerData } from './worker_employers'
import { HttpsProxyAgent } from 'https-proxy-agent'
import { getEmployer, getEmployerPage } from './api/getEmployer'
import { chainFnPromises } from './utils/helpers'
import * as fs from 'node:fs'
import path from 'node:path'

interface IWorkerEmployerPageData {
	path: string
	group: {
		proxy: string
		queries: string[]
	}[]
}
const workerData = _workerData as IWorkerEmployerPageData

workerData.group.forEach(({ proxy, queries }, i) => {
	const [login, pass, ip, port] = proxy.split('@').flatMap(v => v.split(':'))
	const proxyUrl = `http://${login}:${pass}@${ip}:${port}`
	const httpsAgent = new HttpsProxyAgent(proxyUrl)
	console.log(`start for ${proxyUrl}, amount ${queries.length}`)
	const promises = queries.map(query => [getEmployerPage, [{ query }, httpsAgent]])
	// @ts-ignore
	chainFnPromises(promises, 37_500, (page, fnArgs) => {
		if (!page) return
		fs.writeFileSync(path.resolve(__dirname, './context/employers_page', `${page.id}.html`), page.html)
		fs.writeFileSync(
			path.resolve(__dirname, './context/employers_page', `${page.id}.txt`),
			(fnArgs[0] as { query: string }).query,
		)
	})
})
