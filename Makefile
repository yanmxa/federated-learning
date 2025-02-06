
# Variables
REGISTRY ?= quay.io/myan
IMAGE_TAG ?= latest
DIST_DIR = dist
APP = flower/app-torch

build-app-image:
	cd ${APP} && docker build -t ${REGISTRY}/flower-app:${IMAGE_TAG} . -f Dockerfile && cd ../..

push-app-image:
	docker push ${REGISTRY}/flower-app:${IMAGE_TAG}

clean:
	rm -rf $(DIST_DIR) __pycache__ *.spec