.PHONY: install install-system install-node install-python install-ollama setup dirs help

help: ## Показать доступные команды
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-18s %s\n", $$1, $$2}'

install: install-system install-node install-python install-ollama dirs ## Установить всё

install-system: ## Установить системные зависимости (Node.js, pnpm, Go)
	@echo "=== Системные зависимости ==="
	@which node > /dev/null 2>&1 && echo "Node.js уже установлен: $$(node -v)" || (echo "Устанавливаю Node.js..." && sudo dnf install -y nodejs)
	@which pnpm > /dev/null 2>&1 && echo "pnpm уже установлен: $$(pnpm -v)" || (echo "Устанавливаю pnpm..." && npm install -g pnpm)
	@which go > /dev/null 2>&1 && echo "Go уже установлен: $$(go version)" || (echo "Устанавливаю Go..." && sudo dnf install -y golang)
	@which python3 > /dev/null 2>&1 && echo "Python уже установлен: $$(python3 --version)" || (echo "Устанавливаю Python..." && sudo dnf install -y python3 python3-pip)

install-node: ## Установить Node.js зависимости
	@echo "=== Node.js зависимости ==="
	pnpm install

install-python: ## Установить Python зависимости
	@echo "=== Python зависимости ==="
	pip install -r requirements.txt

install-ollama: ## Установить Ollama и скачать модель qwen2.5:7b
	@echo "=== Ollama ==="
	@which ollama > /dev/null 2>&1 && echo "Ollama уже установлена" || (echo "Устанавливаю Ollama..." && curl -fsSL https://ollama.com/install.sh | sh)
	@echo "Скачиваю модель qwen2.5:7b..."
	ollama pull qwen2.5:7b

install-go: ## Скачать Go модули
	@echo "=== Go модули ==="
	go mod download

dirs: ## Создать необходимые папки
	@echo "=== Создание папок ==="
	mkdir -p src/context/vacs
	mkdir -p src/context/employers
	mkdir -p src/context/errors
	@test -f src/context/proxy.txt || touch src/context/proxy.txt
	@echo "Готово. Не забудьте заполнить src/context/proxy.txt"

setup: install install-go ## Полная установка (всё + Go модули)
	@echo ""
	@echo "=== Установка завершена ==="
	@echo "1. Заполните .env (см. README.md)"
	@echo "2. Добавьте прокси в src/context/proxy.txt"
	@echo "3. Запустите: pnpm dev"
