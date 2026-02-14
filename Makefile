UV := uv

.PHONY: test test_cov build publish release install-dev


install-dev:
	@echo "Installing development dependencies..."
	@$(UV) sync --all-groups
	@echo "Development dependencies installed"


build:
	@echo "Building the project..."
	@$(UV) build
	@echo "Build completed"


publish:
	@echo "Publishing to PyPI..."
	@$(UV) publish -t $(PYPI_TOKEN)
	@echo "Published successfully"


release: build
	@echo "Running release script..."
	@bash scripts/release.sh $(ARGS)


test:
	@echo "Running all tests for typja..."
	@$(UV) run pytest
	@echo "All tests completed"


test_cov:
	@echo "Running all tests with coverage for typja..."
	@$(UV) run pytest --cov=typja --cov-report=html --cov-report=xml
	@echo "All tests completed with coverage report generated"
