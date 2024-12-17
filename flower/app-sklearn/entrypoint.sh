#!/bin/sh

# docker run --rm quay.io/myan/flower-app server --num-rounds 20
# docker run --rm quay.io/myan/flower-app client --data-config "data-partition-1" --server-address 172.17.0.2:8080

# Map input commands to the appropriate Python script
if [ "$1" = "server" ]; then
  shift
  exec python app_sklearn/server_app.py "$@"
elif [ "$1" = "client" ]; then
  shift
  exec python app_sklearn/client_app.py "$@"
else
  echo "Error: Unsupported command '$1'. Use 'server' or 'client'."
  exit 1
fi
