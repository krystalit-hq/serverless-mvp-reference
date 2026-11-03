TF_DIR := infra
PYTHON ?= python

.PHONY: package-worker package-api package-lambdas init fmt validate plan

package-worker:
	$(PYTHON) scripts/package_lambda.py src/worker build/worker.zip

package-api:
	$(PYTHON) scripts/package_lambda.py src/api build/api.zip

package-lambdas: package-worker package-api

init:
	terraform -chdir=$(TF_DIR) init

fmt:
	terraform -chdir=$(TF_DIR) fmt -recursive

validate: package-lambdas
	terraform -chdir=$(TF_DIR) validate

plan: package-lambdas
	terraform -chdir=$(TF_DIR) plan
