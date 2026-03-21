# hh_parser

Парсер вакансий и работодателей с [hh.ru](https://hh.ru) (HeadHunter API). Собирает вакансии, информацию о работодателях, а затем извлекает soft/hard навыки из описаний вакансий с помощью LLM (Qwen 2.5 через Ollama).

## Необходимые зависимости

| Зависимость | Версия | Назначение |
|---|---|---|
| **Node.js** | 18+ | Основной runtime для парсера |
| **pnpm** | любая | Пакетный менеджер |
| **Go** | 1.24+ | Утилита объединения XLSX файлов |
| **Python** | 3.10+ | API для извлечения навыков |
| **Ollama** | любая | Локальный запуск LLM (модель `qwen2.5:7b`) |
| **Docker** *(опционально)* | любая | Запуск Python API в контейнере |

### Быстрая установка (Makefile)

```bash
# Установить всё одной командой (системные зависимости + node + python + ollama + папки + go модули)
make setup
```

Или по отдельности:

```bash
make install-system   # Node.js, pnpm, Go, Python (dnf, Fedora)
make install-node     # pnpm install
make install-python   # pip install -r requirements.txt
make install-ollama   # Ollama + модель qwen2.5:7b
make install-go       # Go модули (go mod download)
make dirs             # Создать src/context/{vacs,employers,errors} и proxy.txt
```

Список всех доступных команд:

```bash
make help
```

### Ручная установка

```bash
# Node.js зависимости
pnpm install

# Go зависимости (скачаются автоматически при первом запуске merge)
# Проверить: go mod download

# Python зависимости
pip install -r requirements.txt

# Ollama — скачать модель
ollama pull qwen2.5:7b
```

## Структура проекта

```
hh_parser/
├── src/
│   ├── index.ts                 # Точка входа, функция bootstrap с пайплайном
│   ├── worker.js                # Загрузчик worker_threads (ts-node register)
│   ├── worker_vacs.ts           # Воркер: парсинг вакансий в потоках
│   ├── worker_employers.ts      # Воркер: парсинг работодателей в потоках
│   │
│   ├── api/
│   │   ├── index.ts             # Реэкспорт apiInstance
│   │   ├── baseApi.ts           # Базовый HTTP-клиент (axios + zod валидация)
│   │   ├── getVacncies.ts       # Запросы к /vacancies и /vacancies/:id
│   │   ├── getEmployer.ts       # Запросы к /employers/:id + парсинг dreamjob.ru
│   │   └── ai.ts                # Запросы к Python API для извлечения навыков
│   │
│   ├── model/
│   │   ├── index.ts             # Реэкспорт моделей
│   │   ├── vacancyResponse.ts   # Zod-схемы ответов по вакансиям
│   │   ├── vacancyRequest.ts    # Типы параметров запросов вакансий
│   │   ├── vacancyDescription.ts# Описание полей вакансии (для заголовков Excel)
│   │   ├── companyResponse.ts   # Zod-схемы ответов по работодателям
│   │   ├── companyDescription.ts# Описание полей работодателя (для заголовков Excel)
│   │   ├── common.ts            # Общие типы
│   │   ├── helpers.ts           # Вспомогательные zod-утилиты
│   │   ├── dictionaryResponse.ts# Схемы справочников HH
│   │   └── industryResponse.ts  # Схемы индустрий
│   │
│   ├── utils/
│   │   ├── helpers.ts           # waitFor, chainFnPromises, executeWithRetry, log
│   │   ├── converts.ts          # Конвертация данных в Excel (exceljs)
│   │   └── go/
│   │       └── mergeXLSXs.go    # Go-утилита для объединения XLSX файлов
│   │
│   ├── ai/
│   │   ├── qwen.py              # FastAPI сервер — извлечение навыков через Ollama
│   │   ├── simple_api.py        # Упрощённый API (поиск по ключевым словам, без LLM)
│   │   ├── promt.txt            # Шаблон промпта для LLM
│   │   ├── analyzy.ts           # Анализ навыков
│   │   └── skillPareser.ts      # Парсер навыков
│   │
│   ├── disco/
│   │   ├── skils/
│   │   │   ├── hard.txt         # Список hard-навыков (справочник)
│   │   │   └── soft.txt         # Список soft-навыков (справочник)
│   │   ├── disco-parser.ts      # Парсер навыков из DISCO
│   │   ├── disco-analyzer.ts    # Анализатор навыков
│   │   └── *.json / *.txt       # Данные DISCO (дерево навыков)
│   │
│   └── context/                 # *** Данные (создаётся автоматически, в .gitignore) ***
│       ├── links.txt            # Сгенерированные ссылки для парсинга
│       ├── proxy.txt            # Список прокси (формат: login:pass@ip:port)
│       ├── vacs/                # XLSX файлы с вакансиями (по страницам)
│       │   ├── *.xlsx           # Отдельные страницы вакансий
│       │   ├── merged.xlsx      # Объединённый файл (после merge)
│       │   └── skills.xlsx      # Извлечённые навыки
│       ├── employers/           # XLSX файлы с работодателями
│       │   ├── *.xlsx           # Отдельные файлы по прокси
│       │   └── merged.xlsx      # Объединённый файл (после merge)
│       ├── errors/              # JSON-логи ошибок при парсинге
│       └── arhcive/             # Архив предыдущих запусков
│
├── .env                         # Переменные окружения
├── environment.d.ts             # Типы для process.env
├── package.json                 # Node.js зависимости и скрипты
├── requirements.txt             # Python зависимости
├── go.mod / go.sum              # Go модули
├── Dockerfile.model             # Docker-образ: Python API (извлечение навыков)
├── Dockerfile.parser            # Docker-образ: Node.js парсер вакансий
├── docker-compose.yml           # Docker Compose (model + parser)
├── description.txt              # Описание стратегии парсинга
├── worker.js                    # Загрузчик воркеров (ts-node register)
└── start_api.py                 # Скрипт запуска Python API
```

## Папки, которые необходимо создать вручную

Папка `src/context/` находится в `.gitignore` и не версионируется. Перед первым запуском создайте:

```bash
mkdir -p src/context/vacs
mkdir -p src/context/employers
mkdir -p src/context/errors
```

Также создайте файл с прокси:

```bash
touch src/context/proxy.txt
```

Формат `proxy.txt` — по одному прокси на строку:
```
login:pass@ip:port
login:pass@ip:port
```

## Переменные окружения (.env)

```env
API_HH_URL=https://api.hh.ru    # Базовый URL API HeadHunter
THREADS_AMOUNT=4                 # Количество воркер-потоков
```

## Пайплайн (bootstrap)

Основной пайплайн запускается из `src/index.ts` и состоит из 4 последовательных шагов:

```typescript
const bootstrap = async () => {
    await generateLinks(prRole)       // 1. Генерация ссылок
    await generateVacancies()         // 2. Парсинг вакансий
    await generateEmployers('worker_employers') // 3. Парсинг работодателей
    await generateSkills()            // 4. Извлечение навыков (требует запущенный Python API)
}
```

### Если процесс был прерван

Каждый шаг поддерживает продолжение с места остановки:

- **generateLinks** — перезапишет `links.txt` заново. Выполняется быстро.
- **generateVacancies** — проверяет уже скачанные файлы в `src/context/vacs/` и пропускает обработанные ссылки.
- **generateEmployers** — **не поддерживает** продолжение, скачает заново.
- **generateSkills** — проверяет уже обработанные ID в `skills.xlsx` и пропускает их.

Если нужно запустить только определённый шаг, **закомментируйте остальные вызовы** в функции `bootstrap`:

```typescript
const bootstrap = async () => {
    // await generateLinks(prRole)     // уже выполнено
    // await generateVacancies()       // уже выполнено
    await generateEmployers('worker_employers') // запускаем только это
    // await generateSkills()          // запустим позже
}
```

## Команды

### Основные

```bash
# Запуск парсера (основной пайплайн)
pnpm dev

# Запуск парсера с авто-перезагрузкой (nodemon)
pnpm _dev
```

### Объединение XLSX файлов (Go)

После парсинга в папках `vacs/` и `employers/` создаётся множество отдельных XLSX файлов. Для объединения:

```bash
# Объединить вакансии → src/context/vacs/merged.xlsx
pnpm merge:v

# Объединить работодателей → src/context/employers/merged.xlsx
pnpm merge:e
```

### Python API для извлечения навыков

API необходимо для шага `generateSkills`. Есть два варианта:

**Вариант 1: С Ollama (LLM)**

```bash
# Запустить Ollama + Python API (порт 6380)
pnpm ai:watch

# Выгрузить модель из памяти
pnpm ai:unload
```

**Вариант 2: Без LLM (простой поиск по ключевым словам)**

```bash
cd src/ai && python simple_api.py   # порт 6381
```

**Вариант 3: Docker (модель + парсер)**

```bash
# Запустить оба сервиса (модель на порту 6380, парсер подключается к ней автоматически)
docker-compose up

# Только модель (без парсера)
docker-compose up model

# Только парсер (модель должна быть запущена)
docker-compose up parser
```

Парсер монтирует `./src/context` как volume — все данные сохраняются на хосте.
Ollama должна быть запущена на хосте (`ollama serve`), модель обращается к ней через `host.docker.internal:11434`.

### Прочее

```bash
# Анализатор навыков DISCO
pnpm analyze

# Форматирование кода
pnpm format
```

## Порты

| Сервис | Порт по умолчанию | Где менять |
|---|---|---|
| Python API (Ollama) | `6380` | `src/ai/qwen.py:229` — параметр `port` |
| Python API (Simple) | `6381` | `src/ai/simple_api.py:128` — параметр `port` |
| Docker model | `6380` | `docker-compose.yml:9` — секция `ports` |
| Ollama | `11434` | `src/ai/qwen.py:10` — `OLLAMA_BASE_URL` |

Если порт API был изменён, необходимо также обновить URL в `src/api/ai.ts`:

```typescript
const REMOTE_URL = 'http://10.230.206.201:6381'  // удалённый сервер
const LOCAL_URL = 'http://localhost:6380'          // локальный сервер
```

## Где хранятся данные

| Что | Где |
|---|---|
| Ссылки для парсинга | `src/context/links.txt` |
| Вакансии (постранично) | `src/context/vacs/*.xlsx` |
| Вакансии (объединённые) | `src/context/vacs/merged.xlsx` |
| Навыки (извлечённые) | `src/context/vacs/skills.xlsx` |
| Работодатели (постранично) | `src/context/employers/*.xlsx` |
| Работодатели (объединённые) | `src/context/employers/merged.xlsx` |
| Ошибки парсинга | `src/context/errors/*.json` |
| Прокси | `src/context/proxy.txt` |
| Справочник hard-навыков | `src/disco/skils/hard.txt` |
| Справочник soft-навыков | `src/disco/skils/soft.txt` |
| Промпт для LLM | `src/ai/promt.txt` |
| Архив прошлых запусков | `src/context/arhcive/` |
