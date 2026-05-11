.PHONY: test test-lexer test-parser test-semantic test-semantic-valid test-semantic-invalid test-cli clean install

install:
	pip install -e .

test: test-lexer test-parser test-semantic test-cli
	@echo "All tests passed!"

test-lexer:
	pytest tests/test_lexer.py -v

test-parser:
	pytest tests/parser/ -v

test-semantic:
	pytest tests/semantic/ -v

test-semantic-valid:
	pytest tests/semantic/test_valid_semantic.py tests/semantic/test_golden_valid.py -v

test-semantic-invalid:
	pytest tests/semantic/test_invalid_semantic.py tests/semantic/test_golden_invalid.py -v

test-cli:
	pytest tests/test_cli.py -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Semantic examples
example-valid:
	python -m src.cli semantic --input tests/semantic/valid/samples/valid_basic.src --show-symbols --show-types

example-invalid:
	python -m src.cli semantic --input tests/semantic/invalid/samples/argument_count.src --show-errors
