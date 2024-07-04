all:  init deploy test
build: init deploy

TARGET := local-deployment/nebari-config.yaml
HOST := local-deployment.nebari.dev
TEST_USERNAME := "test-user"
TEST_PASSWORD := "P@sswo3d"
NEBARI_CONFIG_PATH = `realpath ./local-deployment/nebari-config.yaml`
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
    IS_MAC := true
else
    IS_MAC := false
endif

clean: nebari-destroy delete-cluster

nebari-destroy:
	nebari destroy -c local-deployment/nebari-config.yaml --disable-prompt
	rm $(TARGET)

delete-cluster:
	@$(IS_MAC) && kind delete clusters test-cluster
	rm -rf local-deployment/stages

pre-init-checks:
	@echo Checking prerequsits
	@docker --version
	@$(IS_MAC) && ping $(HOST) | head -1 | grep '172.18.1.100'
	@$(IS_MAC) && brew services info chipmk/tap/docker-mac-net-connect
	@$(IS_MAC) && kind --version
	@$(IS_MAC) || sudo usermod -aG docker $USER newgrp docker

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
	@$(IS_MAC) && echo "conda_store:" >> $(TARGET)
	@$(IS_MAC) && echo "  image: quay.io/aktech/conda-store-server" >> $(TARGET)
	@$(IS_MAC) && echo "  image_tag: sha-558beb8" >> $(TARGET)
	@$(IS_MAC) && awk -v n=13 -v s='    overrides:' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	@$(IS_MAC) && awk -v n=14 -v s='      image:' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	@$(IS_MAC) && awk -v n=15 -v s='        repository: quay.io/aktech/keycloak' 'NR == n {print s} {print}' $(TARGET) > tmp && mv tmp $(TARGET)
	@cat local-deployment/nebari-config.yaml

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
	pytest tests/tests_deployment/ -v -s

test: playwright-tests pytest # SKIPPED test-cypress-run
