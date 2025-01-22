"""cirfar10-torch: A Flower / PyTorch app."""

from collections import OrderedDict

import torch
import torch.nn as nn
import torch.nn.functional as F
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import IidPartitioner
from torch.utils.data import DataLoader
from torchvision.transforms import Compose, Normalize, ToTensor


class Net(nn.Module):
    """Model (simple CNN adapted from 'PyTorch: A 60 Minute Blitz')"""

    def __init__(self):
        super(Net, self).__init__()
        
        self.conv1 = nn.Conv2d(1, 10, kernel_size=5) # input 1 chan, ouput 10 chan: (5 * 5 * 1) * 10 + 10 = 260
        self.conv2 = nn.Conv2d(10, 20, kernel_size=5) # 5×5×10=250 * 20 + 20 = 5020
        self.conv2_drop = nn.Dropout2d()
        self.fc0 = nn.Linear(320, 120)
        self.fc1 = nn.Linear(120, 50)
        self.fc2 = nn.Linear(50, 10)
        
        # self.training = True

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        x = x.view(-1, 320)
        x = F.relu(self.fc0(x))
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

fds = None  # Cache FederatedDataset

from torch.utils.data import DataLoader, Subset


def load_data(partition_id: int, num_partitions: int):
    """Load partition CIFAR10 data."""
    # Only initialize `FederatedDataset` once
    global fds
    if fds is None:
        partitioner = IidPartitioner(num_partitions=num_partitions)
        fds = FederatedDataset(
            dataset="mnist",
            partitioners={"train": partitioner},
        )
    partition = fds.load_partition(partition_id)
    print(f"partition numb: {num_partitions}, current: {partition_id}")
    # Divide data on each node: 80% train, 20% test
    partition_train_test = partition.train_test_split(test_size=0.2, seed=42)
    # pytorch_transforms = Compose(
    #     [ToTensor(), Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    # )
    
    pytorch_transforms = Compose(
      [ToTensor(), Normalize((0.5,), (0.5,))]  # Only one channel for MNIST, hence single value tuple
    )

    def apply_transforms(batch):
        """Apply transforms to the partition from FederatedDataset."""
        batch["image"] = [pytorch_transforms(img) for img in batch["image"]]
        return batch

    partition_train_test = partition_train_test.with_transform(apply_transforms)
    trainloader = DataLoader(partition_train_test["train"], batch_size=32, shuffle=True)
    testloader = DataLoader(partition_train_test["test"], batch_size=32)
    return trainloader, testloader

    # n_epochs = 3
    # batch_size_train = 64
    # batch_size_test = 1000
    # import torchvision
    # train_loader = torch.utils.data.DataLoader(
    #   torchvision.datasets.MNIST('/files/', train=True, download=True,
    #                             transform=torchvision.transforms.Compose([
    #                               torchvision.transforms.ToTensor(),
    #                               torchvision.transforms.Normalize(
    #                                 (0.1307,), (0.3081,))
    #                             ])),
    #   batch_size=batch_size_train, shuffle=True)

    # test_loader = torch.utils.data.DataLoader(
    #   torchvision.datasets.MNIST('/files/', train=False, download=True,
    #                             transform=torchvision.transforms.Compose([
    #                               torchvision.transforms.ToTensor(),
    #                               torchvision.transforms.Normalize(
    #                                 (0.1307,), (0.3081,))
    #                             ])),
    #   batch_size=batch_size_test, shuffle=True)

def train(net, trainloader, epochs, device):
    """Train the model on the training set."""
    net.to(device)  # move model to GPU if available
    criterion = torch.nn.CrossEntropyLoss().to(device)
    optimizer = torch.optim.Adam(net.parameters(), lr=0.01)
    net.train()
    running_loss = 0.0
    for _ in range(epochs):
        for batch in trainloader:
            images = batch["image"]
            labels = batch["label"]
            optimizer.zero_grad()
            loss = criterion(net(images.to(device)), labels.to(device))
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

    avg_trainloss = running_loss / len(trainloader)
    return avg_trainloss


def test(net, testloader, device):
    """Validate the model on the test set."""
    net.to(device)
    criterion = torch.nn.CrossEntropyLoss()
    correct, loss = 0, 0.0
    with torch.no_grad():
        for batch in testloader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            outputs = net(images)
            loss += criterion(outputs, labels).item()
            correct += (torch.max(outputs.data, 1)[1] == labels).sum().item()
    accuracy = correct / len(testloader.dataset)
    loss = loss / len(testloader)
    return loss, accuracy


def get_weights(net):
    return [val.cpu().numpy() for _, val in net.state_dict().items()]


def set_weights(net, parameters):
    params_dict = zip(net.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    net.load_state_dict(state_dict, strict=True)
