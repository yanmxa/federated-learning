"""app-sklearn: A Flower / sklearn app."""

from flwr.common import Context, ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg
from app_sklearn.task import get_model, get_model_params, set_initial_params, set_model_params
import numpy
import os
from app_sklearn.utils import load_model, save_model, get_latest_model_file, set_model_parameters
import flwr as fl
from datetime import datetime

model_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.pkl"
model_dir = "/data/model"
model = get_model("l2", 3)
    
# Custom strategy to save the latest aggregated model
class SaveLatestModelStrategy(fl.server.strategy.FedAvg):
    def aggregate_fit(self, rnd, results, failures):
        # Perform the default aggregation
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(rnd, results, failures)

        if aggregated_parameters is not None:
            print(f"Saving the latest aggregated model after round {rnd}...")
            # Set the aggregated parameters to the model
            # Convert `Parameters` to `list[np.ndarray]`
            import numpy as np
            aggregated_ndarrays: list[np.ndarray] = fl.common.parameters_to_ndarrays(
                aggregated_parameters
            )
            
            set_model_parameters(model, aggregated_ndarrays)
            print(aggregated_ndarrays)
            # Save only the latest aggregated model
            model_file = os.path.join(model_dir, model_name)
            save_model(model, model_file)

        return aggregated_parameters, aggregated_metrics
from typing import List, Tuple
from flwr.common import Metrics

# Define metric aggregation function, each client have a metrics, and each metric contains the number of samples, and the avlue
def client_weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}
  
def start_server():
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
        "--model-dir", type=str, default="/data/model", help="Path to save the model.", required=False
    )
    
    args = parser.parse_args()

    print(vars(args))

    # # Create LogisticRegression Model
    model = get_model("l2", 3)
    
    # if the model path not exist create one
    if not os.path.exists(args.model_dir):
        os.makedirs(args.model_dir)
    model_dir = args.model_dir
    
    # /data/model/init.*
    # /data/model/2024-01-01-00-00-00.*
    # /data/model/2024-01-02-00-00-00.*
    last_model_file = get_latest_model_file(args.model_dir)
    if last_model_file is None:
       # Setting initial parameters, akin to model.compile for keras models
        set_initial_params(model)
        save_model(model, os.path.join(args.model_dir, "init.pkl"))
    else:
        print("Loading model from", last_model_file)
        model = load_model(last_model_file)
    
    initial_parameters = ndarrays_to_parameters(get_model_params(model))
    
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
