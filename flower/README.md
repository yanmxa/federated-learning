# Flower Example using PyTorch

## Dependencies

```bash
pip -q install flwr torch torchvision 
```

## Demo

- Define a CNN model and train it with `CIFAR-10` dataset

- DEMO1 - Federated: Set up 2 clients and split the dataset into 2 partitions, with each client training on one partition

- DEMO2 - Centralized: Train the model for 5 epochs on full dataset, using the same hyperparameters as the federated model

  <!-- ![DMOEs](./federated.gif) -->
  [![asciicast](https://asciinema.org/a/669589.svg)](https://asciinema.org/a/669589)


- Federated learning show a lot of promise

  ![Accuracy](./accuracy.png)

## References

- [Get started with Flower](https://flower.ai/docs/framework/tutorial-series-get-started-with-flower-pytorch.html)
- [Flower Example using PyTorch](https://github.com/adap/flower/blob/main/examples/quickstart-pytorch)