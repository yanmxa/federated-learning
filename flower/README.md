# Flower Example using PyTorch

## Dependencies

```bash
pip -q install flwr torch torchvision 
```

## Demo

- Define a CNN model and train it with `CIFAR-10` dataset

- DEMO1 - Federated: Split the `CIFAR-10` dataset into 2 partitions. Each client/organization will train its local model using its respective partition of the data

- DEMO2 - Centralized: Train the CNN model for 5 epochs using the entire dataset, while keeping all other hyperparameters the same as those used in the federated local model(client)

[DEMOs](./federated.cast) 

## References

- [Get started with Flower](https://flower.ai/docs/framework/tutorial-series-get-started-with-flower-pytorch.html)
- [Flower Example using PyTorch](https://github.com/adap/flower/blob/main/examples/quickstart-pytorch)