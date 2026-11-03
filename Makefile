TF_DIR := infra
PYTHON ?= python

.PHONY: package-worker init fmt validate plan

package-worker:
	$(PYTHON) scripts/package_lambda.py src/worker build/worker.zip

init:
	terraform -chdir=$(TF_DIR) init

fmt:
	terraform -chdir=$(TF_DIR) fmt -recursive

validate: package-worker
	terraform -chdir=$(TF_DIR) validate

plan: package-worker
	terraform -chdir=$(TF_DIR) plan
