# Federated Learning

## What is Federated Learning?

![alt text](./asset/image.png)

### Challenges of Centralized Machine Learning

- Data Privacy/Security

- Efficiency(Bandwidth and Storage)

- Scenarios:

  - Medical Systems: Handling sensitive patient data across different hospitals

  - Financial Institutions: Sharing information across organizations to combat financial fraud.

  - Electric Vehicles: Using location data from electric cars to improve range predictions.

### Definitions

Instead of moving the data to the computation, the FL moves the computation to the data.

*Federated learning is a distributed machine learning approach that enables collaboration on machine learning projects without sharing sensitive data.*

![alt text](./asset/fl.png)

#### Collaborator

- Edge devices like smartphones
- Servers belongs to organizations

#### Aggregator

- Combine all the model updates from the Collaborator to one single model
- The most basic way to do it is called [Federated Averaging](https://arxiv.org/abs/1602.05629)

#### Round

The following step 1 to 5 are what we call a single round of FL. 

1. Initialize global model
2. Send model to the connected collaborators
3. Train the model with the local data
4. Return model updates back to the sever
5. Aggregate the model updates into a new global model

*Repeat the above training process/steps over and over again to eventually arrive at a fully trained model that performs well across the data of all client nodes*

## Frameworks

### Popular Federated Learning Frameworks

| Criteria              | Flower                                             | OpenFL                                             | FATE                                              | TensorFlow Federated (TFF)                        | PySyft                                            |
|-----------------------|----------------------------------------------------|----------------------------------------------------|---------------------------------------------------|---------------------------------------------------|---------------------------------------------------|
| **GitHub Stars**      | ![Flower Stars](https://img.shields.io/github/stars/adap/flower?style=social) | ![OpenFL Stars](https://img.shields.io/github/stars/intel/openfl?style=social) | ![FATE Stars](https://img.shields.io/github/stars/FederatedAI/FATE?style=social) | ![TFF Stars](https://img.shields.io/github/stars/tensorflow/federated?style=social) | ![PySyft Stars](https://img.shields.io/github/stars/OpenMined/PySyft?style=social) |
| **Forks**             | ![Flower Forks](https://img.shields.io/github/forks/adap/flower) | ![OpenFL Forks](https://img.shields.io/github/forks/intel/openfl) | ![FATE Forks](https://img.shields.io/github/forks/FederatedAI/FATE) | ![TFF Forks](https://img.shields.io/github/forks/tensorflow/federated) | ![PySyft Forks](https://img.shields.io/github/forks/OpenMined/PySyft) |
| **Contributors**      | ![Flower Contributors](https://img.shields.io/github/contributors/adap/flower) | ![OpenFL Contributors](https://img.shields.io/github/contributors/intel/openfl) | ![FATE Contributors](https://img.shields.io/github/contributors/FederatedAI/FATE) | ![TFF Contributors](https://img.shields.io/github/contributors/tensorflow/federated) | ![PySyft Contributors](https://img.shields.io/github/contributors/OpenMined/PySyft) |
| **Watchers**          | ![GitHub followers](https://img.shields.io/github/watchers/adap/flower) | ![OpenFL Used By](https://img.shields.io/github/watchers/intel/openfl) | ![FATE Watchers](https://img.shields.io/github/watchers/FederatedAI/FATE) | ![TFF Watchers](https://img.shields.io/github/watchers/tensorflow/federated) | ![PySyft Watchers](https://img.shields.io/github/watchers/OpenMined/PySyft) |
| **Creation Date**     | March 25, 2020                                     | December 4, 2019                                   | February 28, 2019                                  | February 26, 2019                                  | March 10, 2018                                    |
| **Latest Release Date** | ![Flower Latest Release](https://img.shields.io/github/release-date/adap/flower) | ![OpenFL Latest Release](https://img.shields.io/github/release-date/intel/openfl) | ![FATE Latest Release](https://img.shields.io/github/release-date/FederatedAI/FATE) | ![TFF Latest Release](https://img.shields.io/github/release-date/tensorflow/federated) | ![PySyft Latest Release](https://img.shields.io/github/release-date/OpenMined/PySyft) |
| **Documentation**     | [Flower Documentation](https://flower.dev/docs/)   | [OpenFL Documentation](https://openfl.readthedocs.io/) | [FATE Documentation](https://fate.readthedocs.io/) | [TFF Documentation](https://www.tensorflow.org/federated) | [PySyft Documentation](https://pysyft.readthedocs.io/) |
| **Features**          | - Support for multiple ML libraries (TensorFlow, PyTorch, etc.)<br> - Customizable federated learning strategies<br> - Extensive ecosystem<br> - Cross-silo and cross-device federated learning | - Collaborative training across organizations<br> - Extensible and modular<br> - Secure and privacy-preserving<br> - Optimized for Intel technologies | - Comprehensive privacy-preserving technologies<br> - Supports various federated learning algorithms<br> - Extensive toolset for secure computing<br> - Multi-party collaboration and model sharing | - Strong integration with TensorFlow<br> - Designed for research and experimentation<br> - Support for various federated learning scenarios | - Focus on privacy-preserving techniques<br> - Integration with PyTorch<br> - Supports advanced cryptographic protocols<br> - Built for secure, federated learning environments |
| **Community**         | Growing community with active contributions        | Strong enterprise focus with Intel backing         | Large and active community, particularly in China  | Backed by Google and TensorFlow community          | Active community driven by the OpenMined organization |
| **Deployment**        | Easy deployment in cloud, edge, and hybrid setups  | Enterprise integration with Intel hardware and software | Designed for flexible deployment across industries | Research-focused, often used in academic settings  | Built for secure, multi-party environments, including industry applications |
| **Security Features** | Basic security and privacy-preserving techniques   | Emphasizes secure multi-party computations and privacy-preserving techniques | Advanced security protocols, including homomorphic encryption and differential privacy | Focus on research, security features customizable by developers | Strong emphasis on cryptographic protocols and privacy-preserving techniques |
| **Focus**             | Broad focus on federated learning use cases        | Strong enterprise focus with an emphasis on security and privacy | Focus on financial services, healthcare, and other regulated industries | Research and experimentation in federated learning | Privacy-preserving machine learning with strong cryptographic foundations |
| **Programming Language** | Python                                            | Python                                             | Python                                             | Python                                             | Python                                             |

- [Other Criteria Comparison](https://medium.com/elca-it/flower-pysyft-co-federated-learning-frameworks-in-python-b1a8eda68b0d)

### Flower Vs OpenFL

**Flower** is user-friendly for migrating from centralized to federated learning and integrates with various ML frameworks. A notable achievement is training [a billion-scale LLM with Flower](https://arxiv.org/html/2405.10853v1). This is also a reflection of its increased activity.

**OpenFL** offers built-in secure communication between the Aggregator and Collaborators. It provides detailed user control, such as creating a Federation Plan. I personally appreciate the [Task API](https://openfl.readthedocs.io/en/latest/about/features_index/taskrunner.html), which gives users flexibility in controlling which tasks are sent to collaborators.

## Thinking...

- Running the collaborators in edge devices?
- Deploying the federated learning in a multi-clusters environment?

  - Use the [Open Cluster Management](https://open-cluster-management.io/) to manage the FL process

  - Distribute global model to the spoken cluster by hub control-plane

  - Aggregate the local models from spoken clusters into the global model

  - Running the collaborators on the spoken clusters

... ...

## Reference

- [OpenFL Overview](https://openfl.readthedocs.io/en/latest/about/overview.html)
- [Flower](https://flower.ai/docs/framework/tutorial-series-what-is-federated-learning.html)