import os
import joblib
from datetime import datetime

def load_model(model_path):
    """
    Load a LogisticRegression model from the disk.

    Args:
        model_path (str): Path to the model file.

    Returns:
        LogisticRegression or None: The loaded model, or None if no model file exists.
    """
    if os.path.exists(model_path):
        return joblib.load(model_path)
    print("No model found. Initializing a new model.")
    return None
  
def save_model(model, model_path):
    """
    Save the LogisticRegression model to the disk.

    Args:
        model (LogisticRegression): The model to save.
        model_path (str): Path to save the model file.
    """
    print(f"Saving model to {model_path}...")
    joblib.dump(model, model_path)
  

import os
from datetime import datetime

def get_latest_model_file(model_dir="/data/model"):
    """
    Get the latest model file from the specified directory.

    Args:
        model_dir (str): Path to the model directory.

    Returns:
        str or None: Path to the latest model file or None if no files match.
    """
    if not os.path.exists(model_dir):
        return None

    model_files = []
    for filename in os.listdir(model_dir):
        filepath = os.path.join(model_dir, filename)
        if os.path.isfile(filepath):
            # Check for "init.*" or timestamp patterns like "YYYY-MM-DD-HH-MM-SS.*"
            if filename.endswith(".pkl"):
                try:
                    if filename.startswith("init."):
                        # Assign "init.*" a high priority timestamp
                        timestamp = datetime.min
                    else:
                        timestamp = datetime.strptime(filename[:19], "%Y-%m-%d-%H-%M-%S")
                    model_files.append((timestamp, filepath))
                except ValueError:
                    # Skip files that don't match the expected timestamp format
                    pass

    if not model_files:
        return None

    # Sort by timestamp and get the latest
    latest_model = max(model_files, key=lambda x: x[0])[1]
    return latest_model

# file = get_latest_model_file("/home/myan/workspace/federated-learning")
# print(file)

from sklearn.linear_model import LogisticRegression
import numpy as np
def set_model_parameters(model: LogisticRegression, aggregated_ndarrays: list[np.ndarray]):
    """
    Set the parameters (weights and intercepts) of a LogisticRegression model
    from a list of aggregated ndarrays.

    Args:
        model (LogisticRegression): The LogisticRegression model.
        aggregated_ndarrays (list[np.ndarray]): A list containing the model's coefficients
                                                (weights) and intercept.
    """
    # # Set `coef_` (weights) and `intercept_` from aggregated parameters
    # model.coef_ = np.array(aggregated_ndarrays[:-1])  # All but the last ndarray are weights
    # model.intercept_ = np.array(aggregated_ndarrays[-1])  # Last ndarray is the intercept
    
    model.coef_ = aggregated_ndarrays[0]
    if model.fit_intercept:
        model.intercept_ = aggregated_ndarrays[1]

    # Ensure the model is marked as fitted
    model.classes_ = np.arange(model.coef_.shape[0])  # Define the number of classes (10 for MNIST)
    model.n_features_in_ = model.coef_.shape[1]  # Set number of features in the input