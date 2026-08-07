.PHONY: bootstrap bootstrap-py bootstrap-rs bootstrap-go bootstrap-hooks lint lint-py lint-rs lint-go lint-proto test test-py test-rs test-go fmt fmt-py fmt-rs fmt-go proto docker-up docker-down clean help

help: ## Show this help
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Install all toolchains and dependencies
	$(MAKE) bootstrap-py bootstrap-rs bootstrap-go bootstrap-hooks

bootstrap-py: ## Install Python dependencies
	uv sync --all-extras || pip install -e ".[dev]"

bootstrap-rs: ## Install Rust dependencies
	cargo fetch

bootstrap-go: ## Install Go dependencies
	cd services/gateway && go mod download

bootstrap-hooks: ## Install pre-commit hooks
	pre-commit install || echo 'pre-commit not installed, skipping hooks'

lint: lint-py lint-rs lint-go lint-proto ## Run all linters

lint-py: ## Lint Python
	ruff check src/ tests/ reference/
	ruff format --check src/ tests/ reference/

lint-rs: ## Lint Rust
	cargo clippy --workspace --all-targets -- -D warnings

lint-go: ## Lint Go
	cd services/gateway && go vet ./...

lint-proto: ## Lint protobuf
	buf lint || echo 'buf not installed, skipping proto lint'

test: test-py test-rs test-go ## Run all tests

test-py: ## Test Python
	pytest -q

test-rs: ## Test Rust
	cargo test --workspace

test-go: ## Test Go
	cd services/gateway && go test ./...

fmt: fmt-py fmt-rs fmt-go ## Format all code

fmt-py: ## Format Python
	ruff format src/ tests/ reference/

fmt-rs: ## Format Rust
	cargo fmt --all

fmt-go: ## Format Go
	cd services/gateway && gofmt -w .

proto: ## Generate code from protobuf
	buf generate || echo 'buf not installed. Install: go install github.com/bufbuild/buf/cmd/buf@latest'

docker-up: ## Start infrastructure services
	docker compose up -d

docker-down: ## Stop infrastructure services
	docker compose down

clean: ## Clean build artifacts
	rm -rf .ruff_cache .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cargo clean 2>/dev/null || true
	cd services/gateway && go clean 2>/dev/null || true
