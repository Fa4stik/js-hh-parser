import { getVacancies } from './api/getVacncies'
import { VacancyGlobalParams } from './model'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { waitFor } from './utils/helpers'
import { Worker } from 'worker_threads'
import { chunk, zip } from 'lodash'
import { getEmployersFieldFromExcel } from './utils/converts'
import { IWorkerVacsData } from './worker_vacs'

// 403 captcha

const prRole = [
	// 96, 10, 157,
	156, 160, 12, 150, 25, 165, 34, 36, 73, 155, 164, 104, 107, 112, 113, 148, 114, 116, 121, 124, 125, 126,
].map(String) // salary: only_with_salary: true || salary: 9999999

const clusterIdFlow = ['education', 'experience', 'employment', 'schedule', 'area']
const getVacanciesLinks = (params: Readonly<VacancyGlobalParams>, clusterIdUsage: string[] = []): Promise<string[]> => {
	return getVacancies(params).then(async ({ found, clusters, url }) => {
		if (found < 2000 && clusterIdUsage.includes('education')) {
			return [url]
		}

		const nextClusterId = clusterIdFlow.find(cluster => !clusterIdUsage.includes(cluster))!
		const cluster = clusters?.find(cluster => cluster.id === nextClusterId)!

		const links: string[] = []
		for (const item of cluster.items) {
			const url = new URL(item.url)
			if (item.count < 2000) {
				links.push(item.url)
				continue
			}

			const paramValue = url.searchParams.get(nextClusterId)
			links.push(
				...(await getVacanciesLinks({ ...params, [nextClusterId]: paramValue }, [...clusterIdUsage, nextClusterId])),
			)
		}

		return links
	})
}
const mainLinks = async () => {
	const links: string[] = []
	for (const pr of prRole) {
		links.push(...(await getVacanciesLinks({ professional_role: pr, per_page: 100, area: '113', clusters: true })))
		console.log('done for', pr)
		await waitFor(5_150)
	}
	fs.writeFile(path.resolve(__dirname, './context/links.txt'), links.join('\n'), () => console.log('done'))
}
// mainLinks()

const THREADS_AMOUNT = 10
const mainVacancies = async () => {
	const proxies = fs.readFileSync(path.resolve(__dirname, './context/proxy.txt')).toString().split('\n').filter(Boolean)
	const links = fs.readFileSync(path.resolve(__dirname, './context/links.txt')).toString().split('\n').filter(Boolean)

	const group = zip(proxies.slice(0, links.length), links).flatMap(([proxy, link]) =>
		proxy && link ? [{ proxy, link }] : [],
	)
	const chunkedGroup = chunk(group, Math.floor(group.length / THREADS_AMOUNT))

	chunkedGroup.forEach(group => {
		console.log('group', group)
		const worker = new Worker('./worker.js', {
			workerData: { group, path: './src/worker_vacs.ts' } satisfies IWorkerVacsData,
		})
		worker.on('message', console.log)
		worker.on('error', console.log)
	})
}
// mainVacancies()

const mainEmployers = (workerName: string) => {
	const info =
		workerName === 'worker_employers'
			? { field: 'employer.id', type: Number }
			: { field: 'employer.name', type: String }
	getEmployersFieldFromExcel(path.resolve(__dirname, '../merged_vacs.xlsx'), info.field, info.type).then(ids => {
		if (!ids) return

		const proxies = fs
			.readFileSync(path.resolve(__dirname, './context/proxy.txt'))
			.toString()
			.split('\n')
			.filter(Boolean)
		const amountPerProxy = Math.ceil(ids.length / proxies.length)
		const chunkedIds = chunk(ids, amountPerProxy)
		const group = chunkedIds.map((ids, i) => ({
			proxy: proxies[i],
			[workerName === 'worker_employers' ? 'ids' : 'queries']: ids,
		}))
		const chunkedGroup = chunk(group, Math.floor(group.length / THREADS_AMOUNT))
		chunkedGroup.forEach(group => {
			const worker = new Worker('./worker.js', {
				workerData: { group, path: `./src/${workerName}.ts` },
			})
			worker.on('message', console.log)
			worker.on('error', console.log)
		})
	})
}
// mainEmployers('worker_employers')
mainEmployers('worker_employer_page')
