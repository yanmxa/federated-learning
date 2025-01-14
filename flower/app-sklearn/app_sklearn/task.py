"""app-sklearn: A Flower / sklearn app."""

import numpy as np
from flwr_datasets import FederatedDataset
from flwr_datasets.partitioner import IidPartitioner
from sklearn.linear_model import LogisticRegression

fds = None  # Cache FederatedDataset

def load_data(data_path: str):
    """Load partition MNIST data."""
    # Only initialize `FederatedDataset` once
    global fds
    if fds is None:
        partitioner = IidPartitioner(num_partitions=1)
        fds = FederatedDataset(
            dataset="mnist",
            partitioners={"train": partitioner},
        )

    dataset = fds.load_partition(0, "train").with_format("numpy")

    X, y = dataset["image"].reshape((len(dataset), -1)), dataset["label"]
    
    
    # Define partition labels
    y_value = 0
    if "cluster1" in data_path:
        y_value = 9
        labels_to_include = [0, 1, 2, 3, 4]
    elif "cluster2" in data_path:
        y_value = 0
        labels_to_include = [5, 6, 7, 8, 9]
    else:
        raise ValueError(f"Invalid data_path {data_path}. Should be 'cluster1' or 'cluster2'.")
      
    # Filter the training data based on the specified labels
    filter = [label in labels_to_include for label in y]
    X = X[filter]
    y = y[filter]
    
    print("total shape:")
    print(X.shape, y.shape)
    
    # Split the on edge data: 80% train, 20% test
    X_train, X_test = X[: 25000], X[-6000 :]
    y_train, y_test = y[: 25000], y[-6000 :]
    
    print("train shape:")
    print(X_train.shape, y_train.shape)
    
    print(y_train)

    # # Split the on edge data: 80% train, 20% test
    # X_train, X_test = X[: int(0.8 * len(X))], X[int(0.8 * len(X)) :]
    # y_train, y_test = y[: int(0.8 * len(y))], y[int(0.8 * len(y)) :]

    return X_train, X_test, y_train, y_test

def get_model(penalty: str, local_epochs: int):

    return LogisticRegression(
        penalty=penalty,
        max_iter=local_epochs,
        warm_start=True,
        multi_class="ovr",  # One-vs-rest for multi-class classification
        # classes=np.unique(10)  # Explicitl
    )


def get_model_params(model):
    if model.fit_intercept:
        params = [
            model.coef_,
            model.intercept_,
        ]
    else:
        params = [model.coef_]
    return params


def set_model_params(model, params):
    model.coef_ = params[0]
    if model.fit_intercept:
        model.intercept_ = params[1]
    return model


def set_initial_params(model):
    n_classes = 10  # MNIST has 10 classes
    n_features = 784  # Number of features in dataset
    model.classes_ = np.array([i for i in range(10)])

    model.coef_ = np.zeros((n_classes, n_features))
    if model.fit_intercept:
        model.intercept_ = np.zeros((n_classes,))
