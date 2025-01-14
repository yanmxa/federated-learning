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
    if "cluster1" in data_path:
        labels_to_include = [0, 1, 2, 3, 4]
    elif "cluster2" in data_path:
        labels_to_include = [5, 6, 7, 8, 9]
    else:
        raise ValueError(f"Invalid data_path {data_path}. Should be 'cluster1' or 'cluster2'.")
      

    X_filtered = X[np.isin(y, labels_to_include)]
    y_filtered = y[np.isin(y, labels_to_include)]
    
    # Split the filtered data into 90% train and 10% test
    X_train, X_test = X_filtered[: int(0.9 * len(X_filtered))], X_filtered[int(0.1 * len(X_filtered)) :]
    y_train, y_test = y_filtered[: int(0.9 * len(y_filtered))], y_filtered[int(0.1 * len(y_filtered)) :]
    
    # Keep the test data intact (no partitioning)
    X_test_all = X[int(0.8 * len(X)) :]  # Full test data
    y_test_all = y[int(0.8 * len(y)) :]  # Full test data labels

    # # Split the on edge data: 80% train, 20% test
    # X_train, X_test = X[: int(0.8 * len(X))], X[int(0.8 * len(X)) :]
    # y_train, y_test = y[: int(0.8 * len(y))], y[int(0.8 * len(y)) :]
    return X_train, X_test_all, y_train, y_test_all


def get_model(penalty: str, local_epochs: int):

    return LogisticRegression(
        penalty=penalty,
        max_iter=local_epochs,
        warm_start=True,
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
