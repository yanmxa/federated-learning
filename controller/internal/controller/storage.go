package controller

import (
	"context"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/klog/v2"
	"sigs.k8s.io/controller-runtime/pkg/client"
)

func (r *FederatedLearningReconciler) CheckAndCreatePVC(ctx context.Context, namespace, pvcName, size string) error {
	pvc := &corev1.PersistentVolumeClaim{}
	err := r.Get(ctx, client.ObjectKey{Namespace: namespace, Name: pvcName}, pvc)
	if err != nil {
		if errors.IsNotFound(err) {
			// PVC does not exist, create it
			newPVC := &corev1.PersistentVolumeClaim{
				ObjectMeta: metav1.ObjectMeta{
					Name:      pvcName,
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
			klog.Info("Created PVC", "name", pvcName, "namespace", namespace)
			return nil
		}
		return err
	}

	// PVC exists
	klog.Info("PVC already exists", "name", pvcName, "namespace", namespace)
	return nil
}
