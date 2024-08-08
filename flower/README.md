# Flower Example using PyTorch

## Installation

```bash
pip -q install flwr torch torchvision 
```

## Demo

  [![asciicast](https://asciinema.org/a/669589.svg)](https://asciinema.org/a/669589)

- Define a CNN model and train it with `CIFAR-10` dataset

- DEMO1 - Centralized: Train the model for 5 epochs on full dataset

- DEMO2 - Federated: Configure 2 clients and divide the dataset into 2 partitions, with each client training on a separate partition

- Federated learning show a lot of promise

  ![Accuracy](./accuracy.png)

## References

- [Get started with Flower](https://flower.ai/docs/framework/tutorial-series-get-started-with-flower-pytorch.html)
- [Flower Example using PyTorch](https://github.com/adap/flower/blob/main/examples/quickstart-pytorch)