from typing import List, Tuple

from flwr.common import Metrics, ndarrays_to_parameters
import flwr as fl


# Define metric aggregation function
def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}
  


DEVICE = "cpu"
from centralized import Net
net = Net()

def get_weights(net):
    return [val.cpu().numpy() for _, val in net.state_dict().items()]
  
ndarrays = get_weights(Net())
parameters = ndarrays_to_parameters(ndarrays)


# Parse command-line arguments
import argparse

parser = argparse.ArgumentParser(description="Start FL server.")
parser.add_argument(
    "--server-address", type=str, default="0.0.0.0:8080", help="Address of the server."
)
parser.add_argument(
    "--num-rounds", type=int, default=3, help="Number of training rounds."
)
args = parser.parse_args()


fl.server.start_server(
  server_address=args.server_address,
  config=fl.server.ServerConfig(num_rounds = args.num_rounds),
  strategy=fl.server.strategy.FedAvg(
    evaluate_metrics_aggregation_fn=weighted_average,
    initial_parameters=parameters,
    ),
)
