from datetime import datetime, timezone
from typing import TypeVar
from kubernetes import client
from controllers.cache.v1beta1.crd import Cache, Conditon


image_map = {"redis": "redis", "valkey": "valkey/valkey", "memchached": "memcached"}
port_map = {"redis": 6370, "valkey": 6379, "memchached": 11211}

T = TypeVar("T", bound=client.V1Deployment)
def owned_by(obj: Cache, ls: list[T]) -> list[T]:
    result = []
    for resource in ls:
        assert resource.metadata is not None
        if resource.metadata.owner_references:
            for owner_ref in resource.metadata.owner_references:
                if owner_ref.uid == obj.metadata.uid:
                    result.append(resource)
    return result


def deployment_manifest(obj: Cache):
    obj_gvi = obj.get_gvi()
    assert obj_gvi is not None
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{obj.metadata.name}-deployment",
            "namespace": obj.metadata.namespace,
            "labels": {"app": obj.spec.engine},
            "ownerReferences": [
                {
                    "name": obj.metadata.name,
                    "uid": obj.metadata.uid,
                    "controller": True,
                    "kind": obj_gvi.kind,
                    "apiVersion": obj_gvi.api_version,
                }
            ],
        },
        "spec": {
            "replicas": obj.spec.desired_size,
            "selector": {"matchLabels": {"app": obj.spec.engine}},
            "template": {
                "metadata": {"labels": {"app": obj.spec.engine}},
                "spec": {
                    "containers": [
                        {
                            "name": f"{obj.spec.engine}-container",
                            "image": f"{image_map[obj.spec.engine]}:{obj.spec.engine_version}",
                            "ports": [{"containerPort": port_map[obj.spec.engine]}],
                            "resources": {
                                "requests": {
                                    "cpu": obj.spec.resources.requests.cpu,
                                    "memory": obj.spec.resources.requests.memory,
                                },
                                "limits": {
                                    "cpu": obj.spec.resources.limits.cpu,
                                    "memory": obj.spec.resources.limits.memory,
                                },
                            },
                        }
                    ]
                },
            },
        },
    }


def upsert_condition(obj: Cache, reason: str, status: str, msg: str, typ: str):
    for idx, cond in enumerate(obj.status.conditions):
        if cond.type == typ:
            if cond.reason == reason:
                return
            obj.status.conditions[idx] = Conditon(
                reason=reason,
                status=status,
                message=msg,
                type=typ,
                last_transition_time=datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            )
            return

    obj.status.conditions.append(
        Conditon(
            reason=reason,
            status=status,
            message=msg,
            type=typ,
            last_transition_time=datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        )
    )
