# Flower Example using PyTorch

## Dependencies

```bash
pip -q install flwr torch torchvision 
```

## Demo

- Define a CNN model and train it with `CIFAR-10` dataset

- Federated: Split the dataset into 2 partitions, each client/organization will train its the local model using one of the partitions

- Centralized: Train the model for 5 epochs using the entire dataset, while keeping all other hyperparameters the same as those used in the federated local model(client)

  ![DEMOs](./federated.gif) 

## References

- [Get started with Flower](https://flower.ai/docs/framework/tutorial-series-get-started-with-flower-pytorch.html)
- [Flower Example using PyTorch](https://github.com/adap/flower/blob/main/examples/quickstart-pytorch)