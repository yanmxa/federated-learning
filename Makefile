
# Variables
REGISTRY ?= quay.io/myan
IMAGE_TAG ?= latest
PYINSTALLER = pyinstaller
SERVER_SCRIPT = flower/server.py
DIST_DIR = dist

# Build the Flower server binary
build-flower-server:
	$(PYINSTALLER) --onefile $(SERVER_SCRIPT) -n flower-server

build-app-image:
	cd flower/app-sklearn && docker build -t ${REGISTRY}/flower-app:${IMAGE_TAG} . -f Dockerfile && cd ../..

push-app-image:
	docker push ${REGISTRY}/flower-app:${IMAGE_TAG}

clean:
	rm -rf $(DIST_DIR) __pycache__ *.spec