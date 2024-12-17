"""app-sklearn: A Flower / sklearn app."""

import warnings

from sklearn.metrics import log_loss

from flwr.client import ClientApp, NumPyClient
from flwr.common import Context
from app_sklearn.task import (
    get_model,
    get_model_params,
    load_data,
    set_initial_params,
    set_model_params,
)


class FlowerClient(NumPyClient):
    def __init__(self, model, X_train, X_test, y_train, y_test):
        self.model = model
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

    def fit(self, parameters, config):
        set_model_params(self.model, parameters)

        # Ignore convergence failure due to low local epochs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(self.X_train, self.y_train)

        return get_model_params(self.model), len(self.X_train), {}

    def evaluate(self, parameters, config):
        set_model_params(self.model, parameters)

        loss = log_loss(self.y_test, self.model.predict_proba(self.X_test))
        accuracy = self.model.score(self.X_test, self.y_test)

        return loss, len(self.X_test), {"accuracy": accuracy}


def client_fn(context: Context):
    partition_id = context.node_config["partition-id"]
    num_partitions = context.node_config["num-partitions"]

    X_train, X_test, y_train, y_test = load_data(partition_id, num_partitions)

    # Create LogisticRegression Model
    penalty = context.run_config["penalty"]
    local_epochs = context.run_config["local-epochs"]
    model = get_model(penalty, local_epochs)

    # Setting initial parameters, akin to model.compile for keras models
    set_initial_params(model)

    return FlowerClient(model, X_train, X_test, y_train, y_test).to_client()


# Flower ClientApp
# app = ClientApp(client_fn=client_fn)


import flwr as fl 
import argparse


# Get partition id
parser = argparse.ArgumentParser(description="Flower")
parser.add_argument(
    "--partition-id",
    choices=[0, 1],
    default=0,
    type=int,
    help="Partition of the dataset divided into 2 iid partitions created artificially.",
)
parser.add_argument(
    "--server-address", type=str, default="127.0.0.1:8080", help="Server Address"
)
args = parser.parse_args()

print(f"choose the dataset: {args.partition_id}")

fl.client.start_client(
  server_address=args.server_address, 
  client=client_fn(context=Context(
    run_id = "",
    node_id = "",
    state = None,
    node_config={
      "partition-id": args.partition_id,
      "num-partitions": 2
    },
    run_config = {
      "penalty": "l2", 
      "local-epochs": 3,
    },
    )),
  )