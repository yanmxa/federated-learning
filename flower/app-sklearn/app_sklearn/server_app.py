"""app-sklearn: A Flower / sklearn app."""

from flwr.common import Context, ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg
from app_sklearn.task import get_model, get_model_params, set_initial_params


def server_fn(context: Context):
    # Read from config
    num_rounds = context.run_config["num-server-rounds"]

    # Create LogisticRegression Model
    penalty = context.run_config["penalty"]
    local_epochs = context.run_config["local-epochs"]
    model = get_model(penalty, local_epochs)

    # Setting initial parameters, akin to model.compile for keras models
    set_initial_params(model)

    initial_parameters = ndarrays_to_parameters(get_model_params(model))

    # Define strategy
    strategy = FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_available_clients=2,
        initial_parameters=initial_parameters,
        evaluate_metrics_aggregation_fn=client_weighted_average,
    )
    config = ServerConfig(num_rounds=num_rounds)

    return ServerAppComponents(strategy=strategy, config=config)


# Create ServerApp
# app = ServerApp(server_fn=server_fn)






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
    args = parser.parse_args()


    # Create LogisticRegression Model
    model = get_model("l2", 3)

    # Setting initial parameters, akin to model.compile for keras models
    set_initial_params(model)

    initial_parameters = ndarrays_to_parameters(get_model_params(model))

        
    fl.server.start_server(
      server_address=args.server_address,
      config=fl.server.ServerConfig(num_rounds = args.num_rounds),
      strategy=fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_available_clients=2,
        initial_parameters=initial_parameters,
        evaluate_metrics_aggregation_fn=client_weighted_average,
      ),
    )
  
start_server()