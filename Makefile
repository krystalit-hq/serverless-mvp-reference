TF_DIR := infra

.PHONY: init fmt validate plan

init:
	terraform -chdir=$(TF_DIR) init

fmt:
	terraform -chdir=$(TF_DIR) fmt -recursive

validate:
	terraform -chdir=$(TF_DIR) validate

plan:
	terraform -chdir=$(TF_DIR) plan
