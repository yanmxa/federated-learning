package controller

import (
	"context"
	"fmt"
	"reflect"

	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/klog/v2"
	clusterclient "open-cluster-management.io/api/client/cluster/clientset/versioned"
	clusterv1 "open-cluster-management.io/api/cluster/v1"
	clusterv1beta1 "open-cluster-management.io/api/cluster/v1beta1"
	clusterv1beta2 "open-cluster-management.io/api/cluster/v1beta2"
	workv1 "open-cluster-management.io/api/work/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	flv1alpha1 "github/open-cluster-management/federated-learning/api/v1alpha1"
	"github/open-cluster-management/federated-learning/internal/controller/manifests"
	"github/open-cluster-management/federated-learning/internal/controller/manifests/applier"
)

var clusterclientset *clusterclient.Clientset

// +kubebuilder:rbac:groups=policy.open-cluster-management.io,resources=placementbindings,verbs=get;update;watch;list
// +kubebuilder:rbac:groups=cluster.open-cluster-management.io,resources=placementdecisions,verbs=get;update;watch;list
// +kubebuilder:rbac:groups=cluster.open-cluster-management.io,resources=placements,verbs=get;update;watch;list
// +kubebuilder:rbac:groups=cluster.open-cluster-management.io,resources=managedclustersetbindings,verbs=get;update;watch;list
// +kubebuilder:rbac:groups=cluster.open-cluster-management.io,resources=managedclusters,verbs=get;update;watch;list
// +kubebuilder:rbac:groups=work.open-cluster-management.io,resources=manifestworkreplicasets,verbs=get;list;watch;update
// +kubebuilder:rbac:groups=work.open-cluster-management.io,resources=manifestworks,verbs=get;list;watch;update

func (r *FederatedLearningReconciler) federatedLearningClient(ctx context.Context,
	instance *flv1alpha1.FederatedLearning,
) (requeue bool, err error) {
	// delete the placement and manifestwork of it
	if instance.DeletionTimestamp != nil {
		if err = r.pruneResources(ctx, instance); err != nil {
			return false, err
		}
		return false, nil
	}

	// generate placement
	err = r.deployPlacement(ctx, instance)
	if err != nil {
		return false, err
	}

	placement := &clusterv1beta1.Placement{
		ObjectMeta: metav1.ObjectMeta{
			Name: instance.Name, Namespace: instance.Namespace,
		},
	}
	if err := r.Get(ctx, client.ObjectKeyFromObject(placement), placement); err != nil {
		return false, err
	}

	// requeue if pending status
	requeue, err = r.toInProcess(ctx, instance, placement)
	if requeue || err != nil {
		return requeue, err
	}

	// generate manifestwork for the selected cluster
	err = r.generateWorkload(ctx, instance, placement)
	if err != nil {
		return false, err
	}

	return false, nil
}

// Determine dataKey based on the placement(and instance), and render the workload from the decisions
func (r *FederatedLearningReconciler) generateWorkload(ctx context.Context, instance *flv1alpha1.FederatedLearning,
	placement *clusterv1beta1.Placement,
) error {
	// TODO: provide a reasonable way to determine the data configuration
	dataKey := ""
	for _, predicate := range placement.Spec.Predicates {
		for _, matchExpression := range predicate.RequiredClusterSelector.ClaimSelector.MatchExpressions {
			if matchExpression.Operator == metav1.LabelSelectorOpExists {
				dataKey = matchExpression.Key
			}
		}
	}
	count := 0
	for _, decisionGroup := range placement.Status.DecisionGroups {
		for _, decisionName := range decisionGroup.Decisions {
			decision := clusterv1beta1.PlacementDecision{}
			if err := r.Get(ctx, types.NamespacedName{
				Namespace: instance.Namespace, Name: decisionName,
			}, &decision); err != nil {
				return err
			}
			// generate workload
			for _, clusterDecision := range decision.Status.Decisions {
				cluster := &clusterv1.ManagedCluster{}
				if err := r.Get(ctx, types.NamespacedName{Namespace: clusterDecision.ClusterName}, cluster); err != nil {
					return err
				}
				dataConfig := ""
				for _, clusterClaim := range cluster.Status.ClusterClaims {
					if dataKey == clusterClaim.Name {
						dataConfig = clusterClaim.Value
					}
				}
				if dataConfig == "" {
					return fmt.Errorf("failed to the dataConfig(%s) from cluster(%s)", dataKey, cluster.Name)
				}
				if err := r.clusterWorkload(ctx, instance, cluster.Name, dataConfig); err != nil {
					return err
				}
				count++
			}

		}
		message := fmt.Sprintf("applied %d manifests to the clusters", count)
		if instance.Status.Phase == flv1alpha1.PhaseInProcess && instance.Status.Message != message {
			instance.Status.Message = message
			if err := r.Update(ctx, instance); err != nil {
				return err
			}
		}
	}
	return nil
}

func (r *FederatedLearningReconciler) pruneResources(ctx context.Context, instance *flv1alpha1.FederatedLearning,
) (err error) {
	placement := &clusterv1beta1.Placement{
		ObjectMeta: metav1.ObjectMeta{
			Name: instance.Name, Namespace: instance.Namespace,
		},
	}
	if err = r.Get(ctx, client.ObjectKeyFromObject(placement), placement); err != nil && !errors.IsNotFound(err) {
		return err
	}
	if errors.IsNotFound(err) {
		return nil
	}

	// delete the mainfestwork based on the placement status
	// TODO: Use the Label to delete it
	for _, decisionGroup := range placement.Status.DecisionGroups {
		for _, decisionName := range decisionGroup.Decisions {
			decision := clusterv1beta1.PlacementDecision{}
			if err := r.Get(ctx, types.NamespacedName{
				Namespace: instance.Namespace, Name: decisionName,
			}, &decision); err != nil {
				return err
			}
			// generate workload
			for _, clusterDecision := range decision.Status.Decisions {
				namesapce := clusterDecision.ClusterName
				work := &workv1.ManifestWork{}
				err = r.Get(ctx, types.NamespacedName{Namespace: namesapce, Name: instance.Name}, work)
				if err != nil && !errors.IsNotFound(err) {
					return err
				} else if errors.IsNotFound(err) {
					continue
				}
				if err = r.Delete(ctx, work); err != nil {
					return err
				}
			}
		}
	}

	if err = r.Delete(ctx, placement); err != nil {
		return err
	}

	return nil
}

func (r *FederatedLearningReconciler) clusterWorkload(ctx context.Context, instance *flv1alpha1.FederatedLearning,
	clusterName, dataConfig string,
) error {
	serverAddress := ""
	for _, listener := range instance.Status.ServerStatus.Listeners {
		serverAddress = listener.Address
	}
	// if serverAddress == "" {
	// 	return fmt.Errorf("wait the server address to be ready!")
	// }

	clientParams := &manifests.FederatedLearningClientParams{
		ManifestName:       instance.Name,
		ManifestNamespace:  clusterName,
		ClientJobNamespace: instance.Namespace,
		ClientJobName:      instance.Name,
		ClientJobImage:     instance.Spec.Client.Image,
		ClientDataConfig:   dataConfig,
		ServerAddress:      serverAddress,
	}

	render, deployer := applier.NewRenderer(manifests.ClientFiles), applier.NewDeployer(r.Client)
	unstructuredObjects, err := render.Render("client", "", func(profile string) (interface{}, error) {
		return clientParams, nil
	})
	if err != nil {
		return err
	}
	for _, obj := range unstructuredObjects {
		if err := deployer.Deploy(obj); err != nil {
			return err
		}
	}
	return nil
}

// 1. If selectedClusters < minimizeClients, then requeue and update pending message
// 2. Else switch to InProcess
func (r *FederatedLearningReconciler) toInProcess(ctx context.Context, instance *flv1alpha1.FederatedLearning,
	placement *clusterv1beta1.Placement) (bool, error,
) {
	selectedClusters := placement.Status.NumberOfSelectedClusters
	minimizeClients := instance.Spec.Server.MinAvailableClients
	if selectedClusters < int32(minimizeClients) {
		message := fmt.Sprintf(PendingAvailableClientMessage, minimizeClients, selectedClusters)
		if message != instance.Status.Message {
			instance.Status.Message = message
			if err := r.Client.Update(ctx, instance); err != nil {
				return false, err
			}
		}
		return true, nil
	}

	message := fmt.Sprintf(InProcessMessage, selectedClusters)
	if instance.Status.Phase != flv1alpha1.PhaseInProcess || instance.Status.Message != message {
		instance.Status.Phase = flv1alpha1.PhaseInProcess
		instance.Status.Message = message
		if err := r.Client.Update(ctx, instance); err != nil {
			return false, err
		}
	}
	return false, nil
}

func (r *FederatedLearningReconciler) deployPlacement(ctx context.Context,
	instance *flv1alpha1.FederatedLearning,
) error {
	// placement
	expectedPlacement := &clusterv1beta1.Placement{
		ObjectMeta: metav1.ObjectMeta{
			Name: instance.Name, Namespace: instance.Namespace,
		},
		Spec: instance.Spec.Client.Placement,
	}
	// for namespaced resource, set ownerreference of controller
	if err := controllerutil.SetControllerReference(expectedPlacement, instance, r.GetScheme()); err != nil {
		return err
	}

	// Attempt to get the existing Placement
	existingPlacement := &clusterv1beta1.Placement{}
	if err := r.Get(ctx, client.ObjectKeyFromObject(expectedPlacement), existingPlacement); err != nil {
		if errors.IsNotFound(err) {
			// Create the Placement if it does not exist

			klog.Info("create the placement")
			if err := r.Create(ctx, expectedPlacement); err != nil {
				return err
			}
		} else {
			return err
		}
	} else {
		// If the Placement exists but differs, update it
		if !reflect.DeepEqual(existingPlacement.Spec, expectedPlacement.Spec) {
			existingPlacement.Spec = expectedPlacement.Spec
			klog.Info("update the placement for clients")
			if err := r.Update(ctx, existingPlacement); err != nil {
				return err
			}
		}
	}

	// managedclustersetbinding
	if clusterclientset == nil {
		var err error
		clusterclientset, err = clusterclient.NewForConfig(r.GetConfig())
		if err != nil {
			return err
		}
	}

	for _, clusterSet := range instance.Spec.Client.Placement.ClusterSets {
		expectedClusterSetBinding := &clusterv1beta2.ManagedClusterSetBinding{
			ObjectMeta: metav1.ObjectMeta{
				Name:      clusterSet,
				Namespace: instance.Namespace,
			},
			Spec: clusterv1beta2.ManagedClusterSetBindingSpec{
				ClusterSet: clusterSet,
			},
		}

		// Attempt to get the existing Placement
		existingClusterSetBinding := &clusterv1beta2.ManagedClusterSetBinding{}
		if err := r.Get(ctx, types.NamespacedName{Namespace: instance.Namespace, Name: instance.Name}, existingClusterSetBinding); err != nil {
			if errors.IsNotFound(err) {
				klog.Info("create the clustersetbinding for clients")
				_, err = clusterclientset.ClusterV1beta2().ManagedClusterSetBindings(instance.Namespace).Create(
					ctx, expectedClusterSetBinding, metav1.CreateOptions{})
				if err != nil {
					return err
				}
			} else {
				return err
			}
		} else {
			// If the Placement exists but differs, update it
			if !reflect.DeepEqual(existingClusterSetBinding.Spec, expectedClusterSetBinding.Spec) {
				existingClusterSetBinding.Spec = expectedClusterSetBinding.Spec
				klog.Info("update the clustersetbinding for clients")
				_, err = clusterclientset.ClusterV1beta2().ManagedClusterSetBindings(instance.Namespace).Update(ctx, existingClusterSetBinding, metav1.UpdateOptions{})
				if err != nil {
					return err
				}
			}
		}
	}

	return nil
}
