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

	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/klog/v2"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"

	flv1alpha1 "github/open-cluster-management/federated-learning/api/v1alpha1"
)

// FederatedLearningReconciler reconciles a FederatedLearning object
type FederatedLearningReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// +kubebuilder:rbac:groups=federation-ai.open-cluster-management.io,resources=federatedlearnings,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=federation-ai.open-cluster-management.io,resources=federatedlearnings/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=federation-ai.open-cluster-management.io,resources=federatedlearnings/finalizers,verbs=update

// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.19.1/pkg/reconcile
func (r *FederatedLearningReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	instance := &flv1alpha1.FederatedLearning{}
	err := r.Client.Get(ctx, req.NamespacedName, instance)
	if err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	if instance.Status.Phase == flv1alpha1.PhaseCompleted ||
		instance.Status.Phase == flv1alpha1.PhaseFailed {
		klog.Infof("FederatedLearning %s is %s", instance.Name, instance.Status.Phase)
		return ctrl.Result{}, nil
	}

	if instance.Status.Phase == flv1alpha1.PhaseStart {
		instance.Status.Phase = flv1alpha1.PhaseInProcess
		err = r.Client.Status().Update(ctx, instance)
		if err != nil {
			return ctrl.Result{}, err
		}
	}

	// Pending -> InProcess
	// 1. storage
	if instance.Spec.Server.Storage.Type == flv1alpha1.PersistentVolumeClaim {
		err = r.CheckAndCreatePVC(ctx, instance.Namespace, instance.Name, instance.Spec.Server.Storage.Size)
		if err != nil {
			return ctrl.Result{}, err
		}
	}

	// 2. deploy the server job: storage, rounds, minClients

	// 3. generate the placement for the client

	// 4. if the placementDecision is made, and the chooseCluster is meet the minClients, deploy the client job, and change the status to InProcess




	// if the status is InProcess, check the serverJob, if it is completed, change the status to Completed, and extract the modelPath
	// if the status is InProcess, check the serverJob, if it is failed, change the status to Failed, and extract the error message
	// if the status is InProcess, check the serverJob, if it is running, do nothing and return


	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *FederatedLearningReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&flv1alpha1.FederatedLearning{}).
		Named("federatedlearning").
		Complete(r)
}
