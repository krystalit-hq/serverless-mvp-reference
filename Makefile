TF_DIR := infra
PYTHON ?= python

.PHONY: \
	package-worker package-api package-lambdas \
	init fmt fmt-check validate test check \
	plan apply destroy-plan destroy

package-worker:
	$(PYTHON) scripts/package_lambda.py src/worker build/worker.zip

package-api:
	$(PYTHON) scripts/package_lambda.py src/api build/api.zip

package-lambdas: package-worker package-api

init:
	terraform -chdir=$(TF_DIR) init

fmt:
	terraform -chdir=$(TF_DIR) fmt -recursive

fmt-check:
	terraform -chdir=$(TF_DIR) fmt -check -recursive

validate: package-lambdas
	terraform -chdir=$(TF_DIR) validate

test:
	$(PYTHON) -m pytest -q

check: fmt-check test validate

plan: package-lambdas
	terraform -chdir=$(TF_DIR) plan

apply: package-lambdas
	terraform -chdir=$(TF_DIR) apply

destroy-plan: package-lambdas
	terraform -chdir=$(TF_DIR) plan -destroy

destroy: package-lambdas
	terraform -chdir=$(TF_DIR) destroy
