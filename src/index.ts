import 'dotenv/config'

import * as cheerio from 'cheerio'

import * as fs from 'node:fs'
import * as path from 'node:path'

import { getVacancies } from './api/getVacncies'
import { VacancyGlobalParams } from './model'
import { log, waitFor } from './utils/helpers'
import { Worker } from 'worker_threads'
import { omit } from 'lodash'
import { getFieldFromExcel, createSkillsExcel, getProcessedSkillIds, appendSkillRow } from './utils/converts'
import { IWorkerVacsData } from './worker_vacs'
import { extractSkills } from './api/ai'

const THREADS_AMOUNT = Number(process.env.THREADS_AMOUNT)

// 403 captcha
const prRole = [156, 160].map(String) // salary: only_with_salary: true || salary: 9999999

const clusterIdFlow = ['education', 'experience', 'employment', 'schedule', 'area']
const getVacanciesLinks = (
	params: Readonly<VacancyGlobalParams>,
	clusterIdUsage: string[] = [],
): Promise<{ url: string; pages: number }[]> => {
	return getVacancies(params).then(async ({ found, clusters, url, pages }) => {
		if (found < 2000 && clusterIdUsage.includes('education')) {
			return [{ url, pages }]
		}

		const nextClusterId = clusterIdFlow.find(cluster => !clusterIdUsage.includes(cluster))!
		const cluster = clusters?.find(cluster => cluster.id === nextClusterId)!

		const links: { url: string; pages: number }[] = []
		for (const item of cluster.items) {
			const url = new URL(item.url)
			if (item.count < 2000) {
				links.push({ url: item.url, pages: Math.ceil(item.count / 100) })
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
const generateLinks = async (prRole: string[]) => {
	const links: string[] = []
	for (const pr of prRole) {
		const limitedLinks = await getVacanciesLinks({ professional_role: pr, per_page: 100, area: '113', clusters: true })
		links.push(
			...limitedLinks.flatMap(l =>
				Array(l.pages)
					.fill(0)
					.flatMap((_, i) => l.url + `&page=${i + 1}`),
			),
		)
		const uniqParams = limitedLinks
			.map(l => Object.fromEntries(new URL(l.url).searchParams.entries()))
			.reduce(
				(acc, group) => ({
					...acc,
					...omit(group, 'area', 'clusters', 'per_page', 'professional_role'),
				}),
				{},
			)
		log('DONE PR ID', pr, 'CLUSTERS', Object.keys(uniqParams))
		await waitFor(5_150)
	}
	fs.writeFile(path.resolve(__dirname, './context/links.txt'), links.join('\n'), () => {})
}

const generateVacancies = async () => {
	const proxies = fs.readFileSync(path.resolve(__dirname, './context/proxy.txt')).toString().split('\n').filter(Boolean)
	const links = fs.readFileSync(path.resolve(__dirname, './context/links.txt')).toString().split('\n').filter(Boolean)

	const vacsDir = path.resolve(__dirname, './context/vacs')
	const handledFiles = fs.existsSync(vacsDir) ? fs.readdirSync(vacsDir).filter(f => f.endsWith('.xlsx')) : []
	const handledParamsSet = new Set(
		handledFiles.map(file => {
			const paramsStr = file.replace(/_\d+\.xlsx$/, '').replace(/\.xlsx$/, '')
			return new URLSearchParams(paramsStr).toString()
		}),
	)

	const filteredLinks = links.filter(link => {
		const url = new URL(link)
		const params = new URLSearchParams(url.search)
		params.delete('clusters')
		return !handledParamsSet.has(params.toString())
	})

	log(
		'PROXIES FOUND',
		proxies.length,
		'LINKS FOUND',
		links.length,
		'FILTERED LINKS',
		filteredLinks.length,
		'HANDLED',
		handledFiles.length,
	)

	const threads = Math.min(THREADS_AMOUNT, proxies.length)
	log('THREADS USED', threads)
	const uniqProxiesOnThread = Math.floor(proxies.length / threads)
	const repeatProxy = Math.max(1, Math.floor(filteredLinks.length / proxies.length))
	const baseGroupSize = uniqProxiesOnThread * repeatProxy
	const rest = filteredLinks.length % threads

	const chunkedByThread = Array(threads)
		.fill(0)
		.map((_, threadIndex) => {
			const groupProxies = proxies.slice(
				threadIndex * uniqProxiesOnThread,
				threadIndex * uniqProxiesOnThread + uniqProxiesOnThread,
			)

			const groupSize = baseGroupSize + (threadIndex < rest ? 1 : 0)
			const startIndex = threadIndex * baseGroupSize + Math.min(threadIndex, rest)

			return filteredLinks.slice(startIndex, startIndex + groupSize).map((l, i) => ({
				link: l,
				proxy: groupProxies[(i + groupProxies.length) % groupProxies.length],
			}))
		})

	chunkedByThread.forEach((group, thread) => {
		const worker = new Worker('./worker.js', {
			workerData: { group, path: './src/worker_vacs.ts' } satisfies IWorkerVacsData,
		})
		worker.on('message', msg => {
			log(`[worker:thread:${thread}]`, msg)
		})
		worker.on('error', err => {
			log(`[ERROR][worker:thread:${thread}]`, err)
		})
	})
}

const generateEmployers = async (workerName: string) => {
	const fieldDescriptor =
		workerName === 'worker_employers'
			? { key: 'employer.id', type: Number as NumberConstructor }
			: { key: 'employer.name', type: String as StringConstructor }

	const rows = await getFieldFromExcel(path.resolve(__dirname, './context/vacs/merged.xlsx'), [fieldDescriptor])
	if (!rows) return
	const ids = [...new Set(rows.map(r => r[fieldDescriptor.key]).filter(Boolean))]

	const proxies = fs.readFileSync(path.resolve(__dirname, './context/proxy.txt')).toString().split('\n').filter(Boolean)

	const threads = Math.min(THREADS_AMOUNT, proxies.length)
	const uniqProxiesOnThread = Math.floor(proxies.length / threads)
	const totalProxies = threads * uniqProxiesOnThread
	const idsPerProxy = Math.ceil(ids.length / totalProxies)
	const idKey = workerName === 'worker_employers' ? 'ids' : 'queries'

	log('PROXIES FOUND', proxies.length, 'IDS FOUND', ids.length, 'THREADS USED', threads)

	const chunkedByThread = Array(threads)
		.fill(0)
		.map((_, threadIndex) => {
			const threadProxies = proxies.slice(threadIndex * uniqProxiesOnThread, (threadIndex + 1) * uniqProxiesOnThread)
			return threadProxies
				.map((proxy, proxyIndex) => {
					const globalProxyIndex = threadIndex * uniqProxiesOnThread + proxyIndex
					const proxyIds = ids.slice(globalProxyIndex * idsPerProxy, (globalProxyIndex + 1) * idsPerProxy)
					return { proxy, [idKey]: proxyIds }
				})
				.filter(g => (g[idKey] as unknown[]).length > 0)
		})

	chunkedByThread.forEach((group, thread) => {
		const worker = new Worker('./worker.js', {
			workerData: { group, path: `./src/${workerName}.ts` },
		})
		worker.on('message', msg => log(`[worker:thread:${thread}]`, msg))
		worker.on('error', err => log(`[ERROR][worker:thread:${thread}]`, err))
	})
}

const generateSkills = async () => {
	const sourceDir = path.resolve(__dirname, './context/vacs')
	const mergedPath = sourceDir + '/merged.xlsx'
	const skillsPath = sourceDir + '/skills.xlsx'

	const rows = await getFieldFromExcel(mergedPath, [
		{ key: 'id', type: Number },
		{ key: 'description', type: String },
	])
	if (!rows) return

	if (!fs.existsSync(skillsPath)) {
		await createSkillsExcel(skillsPath)
		log('SKILLS FILE CREATED')
	}

	const processedIds = await getProcessedSkillIds(skillsPath)
	const pendingRows = rows.filter(r => !processedIds.has(Number(r.id)))

	log(
		`VACANCIES TOTAL ${rows.length}, ALREADY PROCESSED ${processedIds.size}, PENDING ${pendingRows.length}`,
	)
	if (!pendingRows.length) return

	const sanitizedRows = pendingRows.map(r => ({
		id: Number(r.id),
		description: cheerio.load(String(r.description)).text().trim(),
	}))

	const processRow = async (index: number): Promise<void> => {
		if (index >= sanitizedRows.length) return
		const row = sanitizedRows[index]

		const { data } = await extractSkills(row.description, 'local')
		log(`[${index + 1}/${sanitizedRows.length}] ID ${row.id} | soft: ${data.soft.length} hard: ${data.hard.length}`)

		const rowIndex = processedIds.size + index + 2
		await Promise.all([appendSkillRow(skillsPath, rowIndex, row.id, data.soft, data.hard), processRow(index + 1)])
	}

	await processRow(0)
	log('SKILLS GENERATION COMPLETE')
}

const bootstrap = async () => {
	await generateLinks(prRole)
	log('Links were generated to folder /src/context/links.txt')
	await generateVacancies()
	log('Vacancies were generated to folder /src/context/vacs')
	await generateEmployers('worker_employers')
	log('Employers were generated to folder /src/context/employers')
	await generateSkills()
	log('Skills were generated to folder /src/context/vacs')
}
bootstrap()
