import threading
from kubernetes import client

from kuroboros.reconciler import BaseReconciler, Result
from controllers.cache.v1beta1.crd import Cache, CachePhase, CacheStatus
from controllers.cache.v1beta1.reconciler import utils


FINALIZER = "kuroboros.io/cache-operator"


class CacheReconciler(BaseReconciler[Cache]):

    def _list_deployments(self, obj: Cache):
        return utils.owned_by(
            obj,
            self.get(
                kind="Deployment",
                namespace=obj.metadata.namespace,
                label_selector=f"app={obj.spec.engine}",
                klass=list[client.V1Deployment],
            ),
        )

    def _create_deployment(self, obj: Cache):
        deployment_dict = utils.deployment_manifest(obj)
        return self.create(
            api_version="apps/v1",
            kind="Deployment",
            namespace=obj.metadata.namespace,
            body=deployment_dict,
            klass=client.V1Deployment,
        )

    def _update_deployment_size(self, obj: Cache):
        deployments = self._list_deployments(obj)
        if len(deployments) > 0:
            if len(deployments) > 1:
                self.logger.warning(
                    f"{len(deployments)} deployments found, using first one"
                )

            assert deployments[0].metadata is not None
            assert deployments[0].spec is not None
            deployments[0].spec.replicas = obj.spec.desired_size
            self.patch(
                kind="Deployment",
                namespace=obj.metadata.namespace,
                name=deployments[0].metadata.name,
                patch_body={"spec": deployments[0].spec },
            )
        else:
            self.logger.debug("no deployment found")

    def _delete_deployments(self, deployments: list):
        for dep in deployments:
            self.delete(
                kind="Deployment",
                name=dep.metadata.name,
                namespace=dep.metadata.namespace,
            )

    def patch_cache_status(self, obj: Cache):
        return self.patch(
            klass=Cache,
            patch_body={"status": obj.status},
            name=obj.namespace_name[1],
            namespace=obj.namespace_name[0],
            subresources=["status"],
        )
    
    def patch_cache(self, obj: Cache):
        return self.patch(
            klass=Cache,
            patch_body=obj,
            name=obj.namespace_name[1],
            namespace=obj.namespace_name[0]
        )

    def reconcile(self, obj: Cache, stopped: threading.Event) -> Result:
        if stopped.is_set():
            return Result(requeue=False)

        current_deps = self._list_deployments(obj)
        
        # If the Cache has a deletion timetstamp handle deletion logic
        # if there is nothing to do, dont requeue this CRD and let it be deleted
        if obj.metadata.deletion_timestamp is not None:
            # If there is a finalizer, check for
            # the current deployments and delete them, check again in 5 seconds
            # Once there is no deployments left, remove the finalizer from the Cache
            if obj.metadata.finalizers is not None and len(obj.metadata.finalizers) > 0:
                if len(current_deps) > 0:
                    self._delete_deployments(current_deps)
                    return Result(requeue_after_seconds=5)
                
                obj.metadata.finalizers.remove(FINALIZER)
                obj = self.patch_cache(obj)
            
            return Result(requeue=False)
        # If the status is None, initialice the status
        # and reconcile again inmediately
        elif obj.status is None:
            obj.status = CacheStatus(
                phase=CachePhase.PROGRESSING, current_size=0, conditions=[]
            )
            self.patch_cache_status(obj)
            return Result()
        # If there is no finalizers and no deployments create them
        elif obj.metadata.finalizers is None and len(current_deps) == 0:
            obj.metadata.finalizers = [FINALIZER]
            self._create_deployment(obj)
            self.patch_cache(obj)
            return Result(requeue_after_seconds=10)
        # If there is a deployment update Cache status accordingly.
        # When:
        # deployment_size != desired_size = Progessing
        # deployment_size = desired_size = Healthy
        # 
        elif len(current_deps) > 0:
            dep = current_deps[0]
            assert dep.status is not None
            assert dep.spec is not None
            if dep.spec.replicas != obj.spec.desired_size:
                self._update_deployment_size(obj)

            current_healthy = 0
            if dep.status.available_replicas:
                current_healthy = int(dep.status.available_replicas)

            obj.status.current_size = current_healthy
            if current_healthy == obj.spec.desired_size:
                obj.status.phase = CachePhase.HEALTHY
                utils.upsert_condition(
                    obj,
                    "DesiredReached",
                    "True",
                    "Desired match current",
                    "Ready",
                )
            else:
                obj.status.phase = CachePhase.PROGRESSING
                utils.upsert_condition(
                    obj,
                    "Progressing",
                    "False",
                    "Desired dont match current",
                    "Ready",
                )
            self.patch_cache_status(obj)

        return Result(requeue_after_seconds=5)
