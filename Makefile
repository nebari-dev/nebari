all:  init deploy test
build: init deploy

TARGET := local-deployment/nebari-config.yaml
HOST := local-deployment.nebari.dev
TEST_USERNAME := "test-user"
TEST_PASSWORD := "P@sswo3d"
NEBARI_CONFIG_PATH = `realpath ./local-deployment/nebari-config.yaml`

clean:
	nebari destroy -c local-deployment/nebari-config.yaml --disable-prompt
	rm $(TARGET)
	kind delete clusters test-cluster
	rm -rf local-deployment/stages

pre-init-checks:
	@echo Checking prerequsits
	# @ping $(HOST) | head -1 | grep '172.18.1.100'
	kind --version
	docker --version
	if [ "$(uname -s)" = "Darwin" ]; then brew services info chipmk/tap/docker-mac-net-connect; else sudo usermod -aG docker $USER && newgrp docker; fi
	@echo "Check $(HOST) resolves"

install:
	pip install .[dev]
	playwright install
	@echo "Initialize Nebari Cloud."

init: pre-init-checks install
	@echo "Initializing deployment."
	mkdir -p local-deployment
	rm -rf loca-deployment/*
	cd local-deployment && nebari init local --project=thisisatest --domain $(HOST) --auth-provider=password
	#sed -i -E 's/(cpu_guarantee):\s+[0-9\.]+/\1: 0.25/g' "nebari-config.yaml"
	#sed -i -E 's/(mem_guarantee):\s+[A-Za-z0-9\.]+/\1: 0.25G/g' "nebari-config.yaml"
	@echo "Change default JupyterLab theme."
	@echo "jupyterlab:" >> $(TARGET)
	@echo "  default_settings:" >> $(TARGET)
	@echo '    "@jupyterlab/apputils-extension:themes":' >> $(TARGET)
	@echo "      theme: JupyterLab Dark" >> $(TARGET)
	@echo "monitoring:" >> $(TARGET)
	@echo "  enabled: true" >> $(TARGET)
	@echo "  overrides:" >> $(TARGET)
	@echo "    minio:" >> $(TARGET)
	@echo "      persistence:" >> $(TARGET)
	@echo "        size: 1Gi" >> $(TARGET)
	#	@echo "default_images:" >> $(TARGET)
	#	@echo "  jupyterhub: quay.io/nebari/nebari-jupyterhub:m1-image" >> $(TARGET)
	#	@echo "  jupyterlab: quay.io/nebari/nebari-jupyterlab:m1-image" >> $(TARGET)
	#	@echo "  dask_worker: quay.io/nebari/nebari-dask-worker:m1-image" >> $(TARGET)
	#	@echo "jhub_apps:" >> $(TARGET)
	#	@echo "  enabled: true" >> $(TARGET)
	#	@echo "argo_workflows:" >> $(TARGET)
	#	@echo "  enabled: false" >> $(TARGET)
	@echo "conda_store:" >> $(TARGET)
	@echo "  image: quay.io/aktech/conda-store-server" >> $(TARGET)
	@echo "  image_tag: sha-558beb8" >> $(TARGET)
	@awk -v n=13 -v s='    overrides:' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	@awk -v n=14 -v s='      image:' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	@awk -v n=15 -v s='        repository: quay.io/aktech/keycloak' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	#	@awk -v n=16 -v s='        tag: 15.0.2' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	#	@echo "certificate:" >> $(TARGET)
	#	@echo "  type: lets-encrypt" >> $(TARGET)
	#	@echo "  acme_email: priwari@quansight.com" >> $(TARGET)
	#	@echo "dns:" >> $(TARGET)
	#	@echo "  provider: cloudflare" >> $(TARGET)
	cat local-deployment/nebari-config.yaml



deploy:
	cd local-deployment && nebari deploy -c nebari-config.yaml
	@echo "Create example-user"
	./scripts/create_test_user.sh $(TEST_USERNAME) $(TEST_PASSWORD) $(NEBARI_CONFIG_PATH)
	@echo "Basic kubectl checks after deployment"
	kubectl get all,cm,secret,pv,pvc,ing -A
	@echo "Curl jupyterhub login page"
	curl -k "https://$(HOST)/hub/home" -i
	@echo "Get nebari-config.yaml full path"
	@echo "NEBARI_CONFIG_PATH = $(NEBARI_CONFIG_PATH)"


test-cypress-run:
	@echo "CYPRESS_EXAMPLE_USER_NAME=$(TEST_USERNAME) CYPRESS_EXAMPLE_USER_PASSWORD=$(TEST_PASSWORD) CYPRESS_BASE_URL=https://$(HOST)/"
	cd tests/tests_e2e/ && \
	npm install && \
	CYPRESS_EXAMPLE_USER_NAME=$(TEST_USERNAME) \
	CYPRESS_EXAMPLE_USER_PASSWORD=$(TEST_PASSWORD) \
	CYPRESS_BASE_URL=https://$(HOST) \
	NEBARI_CONFIG_PATH=/Users/prashant/work/nebari/local-deployment/nebari-config.yaml \
	npx cypress run # --headed

playwright-tests:
	@echo "Run playwright pytest tests in headed mode with the chromium browser"
	cd tests/tests_e2e/playwright && envsubst < .env.tpl > .env
	cd tests/tests_e2e/playwright && \
	KEYCLOAK_USERNAME=${TEST_USERNAME} \
	KEYCLOAK_PASSWORD=${TEST_PASSWORD} \
	NEBARI_FULL_URL=https://$(HOST) \
	pytest --browser chromium --headed

pytest:
	KEYCLOAK_USERNAME=${TEST_USERNAME} \
	KEYCLOAK_PASSWORD=${TEST_PASSWORD} \
	NEBARI_HOSTNAME=${HOST} \
	NEBARI_CONFIG_PATH=/Users/prashant/work/nebari/local-deployment/nebari-config.yaml \
	pytest tests/tests_deployment/test_jupyterhub_ssh.py -v -s



test: playwright-tests pytest # SKIPPED test-cypress-run
