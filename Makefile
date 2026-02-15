.PHONY: help build install test clean lint format

help:
	@echo "Доступные команды:"
	@echo "  make build    - сборка пакета"
	@echo "  make install  - установка в режиме разработки"
	@echo "  make test     - запуск тестов"
	@echo "  make clean    - очистка временных файлов"
	@echo "  make lint     - проверка кода"
	@echo "  make format   - форматирование кода"

build:
	python -m build

install:
	pip install -e .

test:
	python tests/run_tests.py

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/