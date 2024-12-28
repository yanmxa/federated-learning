package controller

import (
	"context"
	"fmt"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/discovery"
	"k8s.io/client-go/discovery/cached/memory"
	"k8s.io/client-go/restmapper"
	"k8s.io/klog/v2"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	flv1alpha1 "github/open-cluster-management/federated-learning/api/v1alpha1"
	"github/open-cluster-management/federated-learning/internal/controller/manifests"
	"github/open-cluster-management/federated-learning/internal/controller/manifests/applier"
)

// +kubebuilder:rbac:groups="",resources=persistentvolumeclaims,verbs=create;delete;get;list;watch;update

func (r *FederatedLearningReconciler) federatedLearningServer(ctx context.Context, instance *flv1alpha1.FederatedLearning) error {
	// don't delete the storage and cause the job's owner is instance
	if instance.DeletionTimestamp != nil {
		return nil
	}
	if err := r.storage(ctx, instance); err != nil {
		return err
	}

	render, deployer := applier.NewRenderer(manifests.ServerFiles), applier.NewDeployer(r.Client)
	unstructuredObjects, err := render.Render("server", "", func(profile string) (interface{}, error) {
		return manifests.FederatedLearningServerParams{
			Namespace:           instance.Namespace,
			Name:                instance.Name,
			Image:               instance.Spec.Server.Image,
			NumberOfRounds:      instance.Spec.Server.Rounds,
			MinAvailableClients: instance.Spec.Server.MinAvailableClients,
			StoragePath:         instance.Spec.Server.Storage.Path,
			StorageName:         instance.Spec.Server.Storage.Name,
		}, nil
	})
	if err != nil {
		return err
	}

	// create discovery client
	dc, err := discovery.NewDiscoveryClientForConfig(r.GetConfig())
	if err != nil {
		return err
	}

	// create restmapper for deployer to find GVR
	mapper := restmapper.NewDeferredDiscoveryRESTMapper(memory.NewMemCacheClient(dc))
	if err := SetOwner(unstructuredObjects, instance, mapper, r.Scheme); err != nil {
		return err
	}

	for _, obj := range unstructuredObjects {
		if err := deployer.Deploy(obj); err != nil {
			return err
		}
	}
	return nil
}

func SetOwner(objects []*unstructured.Unstructured,
	ownerObject client.Object,
	mapper *restmapper.DeferredDiscoveryRESTMapper, scheme *runtime.Scheme,
) error {
	// manipulate the object
	for _, obj := range objects {
		mapping, err := mapper.RESTMapping(obj.GroupVersionKind().GroupKind(), obj.GroupVersionKind().Version)
		if err != nil {
			return err
		}

		if mapping.Scope.Name() == meta.RESTScopeNameNamespace {
			// for namespaced resource, set ownerreference of controller
			if err := controllerutil.SetControllerReference(ownerObject, obj, scheme); err != nil {
				return err
			}
		}

		// // set owner labels
		// labels := obj.GetLabels()
		// if labels == nil {
		// 	labels = make(map[string]string)
		// }
		// labels[constants.GlobalHubOwnerLabelKey] = constants.GHOperatorOwnerLabelVal
		// obj.SetLabels(labels)
	}
	return nil
}

func (r *FederatedLearningReconciler) storage(ctx context.Context, instance *flv1alpha1.FederatedLearning) error {
	namespace := instance.Namespace
	name := instance.Spec.Server.Storage.Name
	size := instance.Spec.Server.Storage.Size
	storageType := instance.Spec.Server.Storage.Type
	if storageType != flv1alpha1.PersistentVolumeClaim {
		return fmt.Errorf("unsupported storage type: %s", storageType)
	}

	pvc := &corev1.PersistentVolumeClaim{}
	err := r.Get(ctx, client.ObjectKey{Namespace: namespace, Name: name}, pvc)
	if err != nil {
		if errors.IsNotFound(err) {
			// PVC does not exist, create it
			newPVC := &corev1.PersistentVolumeClaim{
				ObjectMeta: metav1.ObjectMeta{
					Name:      name,
					Namespace: namespace,
				},
				Spec: corev1.PersistentVolumeClaimSpec{
					AccessModes: []corev1.PersistentVolumeAccessMode{
						corev1.ReadWriteOnce,
					},
					Resources: corev1.VolumeResourceRequirements{
						Requests: corev1.ResourceList{
							corev1.ResourceStorage: resource.MustParse(size),
						},
					},
				},
			}
			if err := r.Create(ctx, newPVC); err != nil {
				return err
			}
			klog.Info("Created PVC", "name", name, "namespace", namespace)
			return nil
		}
		return err
	}

	// PVC exists
	klog.Infof("PVC already exists: %s", name)
	return nil
}
