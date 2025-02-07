.PHONY: setup

setup:
	@echo "Setting up correct pins for playwright user-journey tests"
	pip install -r requirements.txt
	@echo "Setting up playwright browser dependencies"
	playwright install
	@echo "Setting up .env file"
	cp .env.tpl .env
	@echo "Please fill in the .env file with the correct values"
