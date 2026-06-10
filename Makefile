.PHONY: help
help:
	@echo "make help            -- print this help"
	@echo "make generate        -- regenerate the json"
	@echo "make update-recipes  -- refresh the pyodide-recipes package list"

.PHONY: generate
generate:
	wget https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json -O top-pypi-packages.json
	./generate.py

.PHONY: update-recipes
update-recipes:
	./scripts/update_pyodide_recipes.py

.PHONY: live
live:
	uv run --no-project python -m http.server -b 0.0.0.0 1337

