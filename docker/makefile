IMAGES := jupyterhub jupyterlab dask-worker workflow-controller
DOCKERFILE := Dockerfile
CONTEXT := .

.PHONY: all $(IMAGES) clean

# Build all images
all: $(IMAGES)

# Build individual images
jupyterhub:
	docker build -t nebari-dev/nebari-docker-images:nebari-jupyterhub -f $(DOCKERFILE) $(CONTEXT) --target jupyterhub

jupyterlab:
	docker build -t nebari-dev/nebari-docker-images:nebari-jupyterlab -f $(DOCKERFILE) $(CONTEXT) --target jupyterlab

dask-worker:
	docker build -t nebari-dev/nebari-docker-images:nebari-dask-worker -f $(DOCKERFILE) $(CONTEXT) --target dask-worker

workflow-controller:
	docker build -t nebari-dev/nebari-docker-images:nebari-workflow-controller -f $(DOCKERFILE) $(CONTEXT) --target workflow-controller

# Clean up images
clean:
	@for image in $(IMAGES); do \
		docker rmi nebari-dev/nebari-docker-images:nebari-$$image; \
	done
