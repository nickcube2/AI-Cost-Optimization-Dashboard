.PHONY: local-up local-down local-logs docker-build docker-run tf-init tf-plan tf-apply tf-destroy

local-up:
	docker compose up --build -d

local-down:
	docker compose down

local-logs:
	docker compose logs -f

docker-build:
	docker build -t ai-cost-optimization-dashboard .

docker-run:
	docker run --rm -p 5000:5000 --env-file .env -e DASHBOARD_HOST=0.0.0.0 ai-cost-optimization-dashboard

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan

tf-apply:
	cd terraform && terraform apply

tf-destroy:
	cd terraform && terraform destroy
