
from collections import OrderedDict
import argparse

import flwr as fl
import torch
from flwr_datasets import FederatedDataset
from torchvision.transforms import Compose, Normalize, ToTensor
from torch.utils.data import DataLoader
from tqdm import tqdm

from centralized import Net

# #############################################################################
# 1. Regular PyTorch pipeline: nn.Module, train, test, and DataLoader
# #############################################################################

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
PARTITIONS = 2
EPOCHS = 5

def load_data(partition_id):
    """Load partition CIFAR10 data."""
    fds = FederatedDataset(dataset="cifar10", partitioners={"train": PARTITIONS})
    partition = fds.load_partition(partition_id)
    # Divide data on each node: 80% train, 20% test
    partition_train_test = partition.train_test_split(test_size=0.2, seed=42)
    pytorch_transforms = Compose(
        [ToTensor(), Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    )

    def apply_transforms(batch):
        """Apply transforms to the partition from FederatedDataset."""
        batch["img"] = [pytorch_transforms(img) for img in batch["img"]]
        return batch

    partition_train_test = partition_train_test.with_transform(apply_transforms)
    trainloader = DataLoader(partition_train_test["train"], batch_size=32, shuffle=True)
    testloader = DataLoader(partition_train_test["test"], batch_size=32)
    return trainloader, testloader

def train(net, trainloader, epochs):
    """Train the model on the training set."""
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
    for _ in range(epochs):
        for batch in tqdm(trainloader, "Training"):
            images = batch["img"]
            labels = batch["label"]
            optimizer.zero_grad()
            criterion(net(images.to(DEVICE)), labels.to(DEVICE)).backward()
            optimizer.step()

def test(net, testloader):
    """Validate the model on the test set."""
    criterion = torch.nn.CrossEntropyLoss()
    correct, loss = 0, 0.0
    with torch.no_grad():
        for batch in tqdm(testloader, "Testing"):
            images = batch["img"].to(DEVICE)
            labels = batch["label"].to(DEVICE)
            outputs = net(images)
            loss += criterion(outputs, labels).item()
            correct += (torch.max(outputs.data, 1)[1] == labels).sum().item()
    accuracy = correct / len(testloader.dataset)
    return loss/len(testloader.dataset), accuracy

# #############################################################################
# 2. Federation of the pipeline with Flower
# #############################################################################

# Get partition id
parser = argparse.ArgumentParser(description="Flower")
parser.add_argument(
    "--partition-id",
    choices=[0, 1],
    default=0,
    type=int,
    help="Partition of the dataset divided into 2 iid partitions created artificially.",
)
partition_id = parser.parse_known_args()[0].partition_id

# Load model and data (simple CNN, CIFAR-10)
net = Net().to(DEVICE)
trainloader, testloader = load_data(partition_id=partition_id)

class FlowerClient(fl.client.NumPyClient):
  """NumPyClient makes it easier to implement the Client interface when your workload use PyTorch"""

  def set_parameters(self, parameters):
    """Optional: Update the local model weights with parameter received from the server"""
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)

  def get_parameters(self, config):
    """Return the current local model parameters"""
    return [val.cpu().numpy() for _, val in net.state_dict().items()]  
    
  def fit(self, parameters, config):
    # TODO: update the repos document
    """Set the local model weights; train the local model; return the updated local model weights""" 
    self.set_parameters(parameters)
    train(net, trainloader, epochs=EPOCHS)
    return self.get_parameters({}), len(trainloader.dataset), {}
  
  def evaluate(self, parameters, config):
    """Set the local model with parameters from server; evaluate the model parameters on the local data, return the evaluation result to server""" 
    self.set_parameters(parameters)
    loss, accuracy = test(net, testloader)
    return float(loss), len(testloader.dataset), {"accuracy": accuracy}
  
fl.client.start_client(
  server_address="127.0.0.1:8080", 
  client=FlowerClient().to_client(),# <-- where FlowerClient is of type flwr.client.NumPyClient object
  )