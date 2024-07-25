import matplotlib.pyplot as plt

# Federated accuracy data
federated_accuracy = [(1, 0.3836), (2, 0.4782), (3, 0.5422)]
rounds, accuracies = zip(*federated_accuracy)

# Centralized accuracy
centralized_accuracy = 0.518

# Plotting the data
plt.figure(figsize=(10, 6))
plt.plot(rounds, accuracies, marker='o', label='Federated Accuracy')
plt.axhline(y=centralized_accuracy, color='r', linestyle='--', label='Centralized Accuracy')

# Adding titles and labels
plt.title('Federated vs Centralized Accuracy')
plt.xlabel('Round')
plt.ylabel('Accuracy')
plt.xticks(rounds)  # Ensure the x-axis only has the round numbers

# Set y-axis limits to focus closely on the range of accuracies
plt.ylim(min(min(accuracies), centralized_accuracy) - 0.05, max(max(accuracies), centralized_accuracy) + 0.05)

# Adding legend
plt.legend()

# Display the plot
plt.grid(True)
plt.show()
