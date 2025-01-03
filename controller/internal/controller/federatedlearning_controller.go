/*
Copyright 2024.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"time"

	batchv1 "k8s.io/api/batch/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/event"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	flv1alpha1 "github/open-cluster-management/federated-learning/api/v1alpha1"
	"github/open-cluster-management/federated-learning/internal/logger"
)

var (
	PendingInitMessage            = "Waiting for the server and clients to be ready"
	PendingAvailableClientMessage = "Expected at least %d clients, but only %d clusters meet the criteria"
	InProcessMessage              = "Selected %d clusters for the federated learning process"
	log                           = logger.DefaultZapLogger()
)

const FederatedLearningFinalizer = "federated-learning.open-cluster-management.io/resource-cleanup"

// FederatedLearningReconciler reconciles a FederatedLearning object
type FederatedLearningReconciler struct {
	ctrl.Manager
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=federation-ai.open-cluster-management.io,resources=federatedlearnings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=federation-ai.open-cluster-management.io,resources=federatedlearnings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=federation-ai.open-cluster-management.io,resources=federatedlearnings/finalizers,verbs=update
// +kubebuilder:rbac:groups="route.openshift.io",resources=routes,verbs=get;list;watch;create;update;delete
// +kubebuilder:rbac:groups=batch,resources=jobs,verbs=get;list;watch;create;update;delete

// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.19.1/pkg/reconcile
func (r *FederatedLearningReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	instance := &flv1alpha1.FederatedLearning{}
	err := r.Client.Get(ctx, req.NamespacedName, instance)
	if err != nil && !errors.IsNotFound(err) {
		return ctrl.Result{}, err
	}
	if errors.IsNotFound(err) {
		return ctrl.Result{}, nil
	}

	defer func() {
		if err != nil {
			instance.Status.Message = err.Error()
			instance.Status.Phase = flv1alpha1.PhaseFailed
			if e := r.Status().Update(ctx, instance); e != nil {
				log.Errorf("failed to update the instance phase into failed: %v", e)
			}
		}
	}()

	// add finalizer
	if instance.DeletionTimestamp == nil && containsString(instance.Finalizers, FederatedLearningFinalizer) {
		instance.Finalizers = append(instance.Finalizers, FederatedLearningFinalizer)
		if err = r.Update(ctx, instance); err != nil {
			return ctrl.Result{}, err
		}
	}

	// Initialize status.phase to Pending if not set
	if instance.DeletionTimestamp == nil && instance.Status.Phase == "" {
		instance.Status.Phase = flv1alpha1.PhasePending
		instance.Status.Message = PendingInitMessage
		if err := r.Status().Update(ctx, instance); err != nil {
			return ctrl.Result{}, err
		}
	}

	if instance.DeletionTimestamp == nil &&
		instance.Status.Phase == flv1alpha1.PhaseCompleted ||
		instance.Status.Phase == flv1alpha1.PhaseFailed {
		log.Infof("FederatedLearning %s is %s", instance.Name, instance.Status.Phase)
		return ctrl.Result{}, nil
	}

	if instance.Status.Phase == flv1alpha1.PhaseStart {
		instance.Status.Phase = flv1alpha1.PhasePending
		err = r.Client.Status().Update(ctx, instance)
		if err != nil {
			return ctrl.Result{}, err
		}
	}

	// Pending -> InProcess
	if instance.Status.Phase == flv1alpha1.PhasePending || instance.Status.Phase == flv1alpha1.PhaseInProcess {
		// 1. server: storage, job (rounds, minAvailableClients)
		if err := r.federatedLearningServer(ctx, instance); err != nil {
			return ctrl.Result{}, err
		}

		requeue, err := r.updateServerAddress(ctx, instance)
		if err != nil {
			log.Error(err, "failed to update the server address")
			return ctrl.Result{}, err
		}
		if requeue {
			return ctrl.Result{RequeueAfter: 5 * time.Second}, nil
		}

		// 2. client: placement(based on selected cluster -> InProcess), InProcess -> generate manifestwork
		requeue, err = r.federatedLearningClient(ctx, instance)
		if err != nil {
			log.Error(err, "failed to update the client status")
			return ctrl.Result{}, err
		}
		if requeue {
			return ctrl.Result{RequeueAfter: 5 * time.Second}, nil
		}
	}

	// InProcess -> Completed
	if instance.Status.Phase == flv1alpha1.PhaseInProcess {
		job := &batchv1.Job{}
		err = r.Get(ctx, types.NamespacedName{Namespace: instance.Namespace, Name: instance.Name}, job)
		if err != nil {
			return ctrl.Result{}, err
		}
		if job.Status.Succeeded > 0 {
			instance.Status.Phase = flv1alpha1.PhaseCompleted
			instance.Status.Message = "the models have been aggregated successfully!"
			if err = r.Status().Update(ctx, instance); err != nil {
				return ctrl.Result{}, err
			}
		}
	}

	if instance.DeletionTimestamp != nil {
		if containsString(instance.Finalizers, FederatedLearningFinalizer) {
			instance.Finalizers = removeString(instance.Finalizers, FederatedLearningFinalizer)
			if err = r.Update(ctx, instance); err != nil {
				return ctrl.Result{}, err
			}
		}
	}

	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *FederatedLearningReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&flv1alpha1.FederatedLearning{}).
		WithEventFilter(predicate.Funcs{
			CreateFunc: func(e event.CreateEvent) bool {
				return true
			},
			DeleteFunc: func(e event.DeleteEvent) bool {
				return true
			},
			UpdateFunc: func(e event.UpdateEvent) bool {
				return e.ObjectOld.GetGeneration() != e.ObjectNew.GetGeneration()
			},
		}).
		Named("federatedlearning").
		Complete(r)
}

func containsString(slice []string, str string) bool {
	for _, item := range slice {
		if item == str {
			return true
		}
	}
	return false
}

func removeString(slice []string, str string) []string {
	result := []string{}
	for _, item := range slice {
		if item != str {
			result = append(result, item)
		}
	}
	return result
}
