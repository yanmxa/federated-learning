"""cirfar10-torch: A Flower / PyTorch app."""

import torch
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR

from flwr.client import ClientApp, NumPyClient
from flwr.common import Context
from app_torch.task import Net, get_weights, load_data, set_weights, test, train


# Define Flower Client and client_fn
class FlowerClient(NumPyClient):
    def __init__(self, net, trainloader, valloader, local_epochs):
        self.net = net
        self.trainloader = trainloader
        self.valloader = valloader
        
        self.local_epochs = local_epochs
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.optimizer = optim.Adadelta(net.parameters(), lr=1.0)
        self.scheduler = StepLR(self.optimizer, step_size=1, gamma=0.7)

    def fit(self, parameters, config):
        set_weights(self.net, parameters)
      
        optimizer = optim.Adadelta(self.net.parameters(), lr=1.0)
        scheduler = StepLR(optimizer, step_size=1, gamma=0.7)

        epoch_loss = 0.0
        for epoch in range(1, self.local_epochs + 1):
            # test_loss = test(model, device, test_loader)
            # test_losses.append(test_loss)
            loss = train(self.net, self.device, self.trainloader, optimizer, epoch)
            epoch_loss += loss
            scheduler.step()
            
        return (
            get_weights(self.net),
            len(self.trainloader.dataset),
            {"train_loss": epoch_loss / self.local_epochs},
        )

    def evaluate(self, parameters, config):
        set_weights(self.net, parameters)
        
        loss, accuracy = test(self.net, self.device, self.valloader)
        print(f"Loss: {loss}, Accuracy: {accuracy}")
        return loss, len(self.valloader.dataset), {"accuracy": accuracy}

def client_fn(context: Context):
    # Load model and data
    net = Net()
    cluster_config = context.node_config["cluster-data-config"]
    # cluster_id = context.node_config["partition-id"]
    local_epochs = context.run_config["local-epochs"]

    trainloader, valloader = load_data(cluster_config)
    print(f"Cluster {cluster_config} -> epochs: {local_epochs}")
    # Return Client instance
    return FlowerClient(net, trainloader, valloader, local_epochs).to_client()


# # Flower ClientApp
# app = ClientApp(
#     client_fn,
# )

# cluster client
import flwr as fl 
import argparse

# Get partition id
parser = argparse.ArgumentParser(description="Flower")
parser.add_argument(
    "--data-config",
    default="cluster1",
    type=str,
    help="Data configuration for the cluster client.",
)
parser.add_argument('--epochs', type=int, default=1, help='number of epochs to train (default: 1)')
parser.add_argument(
    "--server-address", type=str, default="127.0.0.1:8080", help="Server Address"
)
args = parser.parse_args()
cluster_data_config = str(args.data_config)
local_epochs = args.epochs

print(f"choose the dataset: {cluster_data_config}")
print(f"epochs: {local_epochs}")
print(f"address: {args.server_address}")
        
import time

MAX_RETRIES = 60
RETRY_DELAY = 10  # seconds
for attempt in range(MAX_RETRIES):
    try:
        fl.client.start_client(
            server_address=args.server_address,
            client=client_fn(context=Context(
                run_id="",
                node_id="",
                state=None,
                node_config={
                    "cluster-data-config": cluster_data_config,
                },
                run_config={
                    "local-epochs": local_epochs,
                },
            )),
        )
        print("Client started successfully.")
        break  # Exit the loop if successful
    except Exception as e:
        print(f"Attempt {attempt + 1} failed with error: {e}")
        if attempt < MAX_RETRIES - 1:  # If not the last attempt, wait before retrying
            print(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            print("Max retries reached. Exiting.")
            raise e  # Re-raise the exception after the last attempt

