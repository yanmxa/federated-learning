import matplotlib.pyplot as plt

# Data from the logs
rounds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
collaborator1_agg_model_val_acc = [
    0.06279999762773514, 
    0.926800012588501, 
    0.9570000171661377, 
    0.9674000144004822, 
    0.972599983215332,
    0.9757999777793884,
    0.9783999919891357,
    0.9805999994277954,
    0.9810000061988831,
    0.9818000197410583
]
collaborator1_train_cross_entropy = [
    0.9409059286117554, 
    0.12404325604438782, 
    0.0749373510479927, 
    0.05283943936228752, 
    0.039963290095329285,
    0.03276584669947624,
    0.027651283890008926,
    0.022429443895816803,
    0.019461430609226227,
    0.01668413355946541
]
collaborator1_locally_tuned_model_val_acc = [
    0.9129999876022339, 
    0.9503999948501587, 
    0.9602000117301941, 
    0.9688000082969666, 
    0.9693999886512756,
    0.9735999703407288,
    0.9751999974250793,
    0.9753999710083008,
    0.9768000245094299,
    0.9818000197410583
]

collaborator2_agg_model_val_acc = [
    0.06921384483575821, 
    0.9247849583625793, 
    0.9525905251502991, 
    0.9675934910774231, 
    0.9717943668365479,
    0.9757951498031616,
    0.9801960587501526,
    0.9799960255622864,
    0.9803960919380188,
    0.9809961915016174
]
collaborator2_train_cross_entropy = [
    1.0785664319992065, 
    0.24602793157100677, 
    0.1680326759815216, 
    0.12732785940170288, 
    0.10157092660665512,
    0.0866941511631012,
    0.07262127101421356,
    0.06606701761484146,
    0.05299024656414986,
    0.04825533926486969
]
collaborator2_locally_tuned_model_val_acc = [
    0.9195839166641235, 
    0.9497899413108826, 
    0.9615923166275024, 
    0.9691938161849976, 
    0.973994791507721,
    0.976195216178894,
    0.976195216178894,
    0.9827965497970581,
    0.9785957336425781,
    0.9799960255622864
]

# Create the subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Plot for Collaborator 1
ax1.plot(rounds, collaborator1_agg_model_val_acc, marker='o', markersize=4,label='Aggregated Model Val Acc')
ax1.plot(rounds, collaborator1_train_cross_entropy, marker='o',  markersize=4,label='Train Cross Entropy')
ax1.plot(rounds, collaborator1_locally_tuned_model_val_acc, marker='o',  markersize=4,label='Locally Tuned Model Val Acc')

ax1.set_ylabel('Metrics')
ax1.legend()
ax1.grid(which='both', linestyle='--', linewidth=0.5)
ax1.tick_params(labelbottom=False)  # Remove x-axis labels from the upper subplot
ax1.set_xticks(rounds)  # Set x-ticks to be integers

# Plot for Collaborator 2
ax2.plot(rounds, collaborator2_agg_model_val_acc, marker='o', markersize=4,label='Aggregated Model Val Acc')
ax2.plot(rounds, collaborator2_train_cross_entropy, marker='o', markersize=4,label='Train Cross Entropy')
ax2.plot(rounds, collaborator2_locally_tuned_model_val_acc, marker='o',markersize=4, label='Locally Tuned Model Val Acc')

ax2.set_xlabel('Rounds')
ax2.set_ylabel('Metrics')
ax2.legend()
ax2.grid(which='both', linestyle='--', linewidth=0.5)
ax2.set_xticks(rounds)  # Set x-ticks to be integers

# Add titles on background
fig.text(0.5, 0.6, 'Collaborator 1', fontsize=18, color='gray', ha='center', va='center', alpha=0.8, transform=ax1.transAxes)
fig.text(0.5, 0.6, 'Collaborator 2', fontsize=18, color='gray', ha='center', va='center', alpha=0.8, transform=ax2.transAxes)

# Adjust layout
plt.tight_layout()
plt.show()
