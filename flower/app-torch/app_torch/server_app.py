"""torch: A Flower / PyTorch app."""

from flwr.common import Context, ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg
from app_torch.task import Net, get_weights

from typing import List, Tuple
from flwr.common import Metrics

# Define metric aggregation function, each client have a metrics, and each metric contains the number of samples, and the value
def client_weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * metric["accuracy"] for num_examples, metric in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}
  
# def server_fn(context: Context):
#     # Read from config
#     num_rounds = context.run_config["num-server-rounds"]
#     fraction_fit = context.run_config["fraction-fit"]

#     # Initialize model parameters
#     ndarrays = get_weights(Net())
#     parameters = ndarrays_to_parameters(ndarrays)

#     # Define strategy
#     strategy = FedAvg(
#         fraction_fit=fraction_fit,
#         fraction_evaluate=1.0,
#         min_fit_clients=2,
#         min_evaluate_clients=2,
#         min_available_clients=2,
#         initial_parameters=parameters,
#         evaluate_metrics_aggregation_fn=client_weighted_average,
#     )
#     config = ServerConfig(num_rounds=num_rounds)

#     return ServerAppComponents(strategy=strategy, config=config)


# # Create ServerApp
# app = ServerApp(server_fn=server_fn)


# cluster server 
import argparse
import flwr as fl

parser = argparse.ArgumentParser(description="Start FL server.")
parser.add_argument(
    "--server-address", type=str, default="0.0.0.0:8080", help="Address of the server."
)
parser.add_argument(
    "--num-rounds", type=int, default=10, help="Number of training rounds."
)
parser.add_argument(
    "--min-available-clients", type=int, default=2, help="Number of clients for training."
)
# default model path
parser.add_argument(
    "--model-dir", type=str, default="/data/models", help="Path to save the model.", required=False
)

args = parser.parse_args()

print(vars(args))

import os
from datetime import datetime
from app_torch.utils import get_latest_model_file, load_model, save_model

def start_server():
    model_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.pkl"
    model = Net()
    
    # if the model path not exist create one
    if not os.path.exists(args.model_dir):
        os.makedirs(args.model_dir)
    model_dir = args.model_dir
    
    # /data/models/init.*
    # /data/models/2024-01-01-00-00-00.*
    # /data/models/2024-01-02-00-00-00.*
    last_model_file = get_latest_model_file(args.model_dir)
    if last_model_file is None:
        save_model(model, os.path.join(args.model_dir, "init.pkl"))
    else:
        print("Loading model from", last_model_file)
        model = load_model(model, last_model_file)
        
    ndarrays = get_weights(model)
    initial_parameters = ndarrays_to_parameters(ndarrays)
    
    # Custom strategy to save the latest aggregated model
    class SaveLatestModelStrategy(fl.server.strategy.FedAvg):
      def aggregate_fit(self, rnd, results, failures):
          """Aggregate model weights using weighted average and store checkpoint"""

          # Call aggregate_fit from base class (FedAvg) to aggregate parameters and metrics
          aggregated_parameters, aggregated_metrics = super().aggregate_fit(rnd, results, failures)

          if aggregated_parameters is not None:
              print(f"Saving round {rnd} aggregated_parameters...")
              net = Net()
              # print(f"Saving the latest aggregated model after round {rnd}...")
              # Convert `Parameters` to `list[np.ndarray]`
              import numpy as np
              import torch
              from collections import OrderedDict

              aggregated_ndarrays: list[np.ndarray] = fl.common.parameters_to_ndarrays(
                  aggregated_parameters
              )
              
              # Convert `list[np.ndarray]` to PyTorch `state_dict` -> list the set parameters
              params_dict = zip(net.state_dict().keys(), aggregated_ndarrays)
              state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
              net.load_state_dict(state_dict, strict=True)
              
              model_file = os.path.join(model_dir, f"model_{model_name}_round_{rnd}.pth")
              
              # algin with the save model
              torch.save(net.state_dict(), model_file)

          return aggregated_parameters, aggregated_metrics
    
    fl.server.start_server(
      server_address=args.server_address,
      config=fl.server.ServerConfig(num_rounds = args.num_rounds),
      strategy=SaveLatestModelStrategy(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_available_clients=args.min_available_clients,
        initial_parameters=initial_parameters,
        evaluate_metrics_aggregation_fn=client_weighted_average,
        inplace=True,
      ),
    )
    
  
start_server()