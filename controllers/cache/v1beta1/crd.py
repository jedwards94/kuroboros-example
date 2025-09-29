"""
Remember to run
`kuroboros generate crd`
after modfying this file
"""

from kubernetes.client import V1ObjectMeta
from kuroboros.schema import CRDSchema, OpenAPISchema, prop


class CachePhase:
    PROGRESSING = "Progressing"
    HEALTHY = "Healthy"


class Conditon(OpenAPISchema):
    """
    Defines the conditions in the Cache
    """

    last_transition_time = prop(str, format="date-time")
    message = prop(str)
    reason = prop(str)
    status = prop(str, enum=["True", "False", "Unknown"], required=True)
    type = prop(str, required=True)


class CacheResource(OpenAPISchema):
    cpu = prop(str, required=True)
    memory = prop(str, required=True)


class CacheResources(OpenAPISchema):
    """
    Defines the limits ands requests of resources for the
    Cache
    """

    requests = prop(CacheResource, required=True)
    limits = prop(CacheResource, required=True)


class CacheStatus(OpenAPISchema):
    """
    Defines the current phase and conditions
    of the Cache resource
    """

    phase = prop(str, enum=[CachePhase.PROGRESSING, CachePhase.HEALTHY])
    conditions = prop(
        list[Conditon],
        x_kubernetes_list_map_keys=["type"],
        x_kubernetes_list_type="map",
    )
    current_size = prop(int, minimum=0)


class CacheSpec(OpenAPISchema):
    """
    Defines the specifications
    of the Cache V1Beta1 Resource
    """

    engine = prop(
        str,
        enum=["redis", "valkey", "memcached"],
        required=True,
        description="The engine that will be deployed",
    )
    engine_version = prop(
        str,
        required=True,
        description="The tag to use in the engine deployment image",
    )

    desired_size = prop(
        int,
        minimum=1,
        required=True,
        description="The desired number of replicas of the deployment",
    )
    resources = prop(CacheResources)


class Cache(CRDSchema):
    """
    Defines a Cache resource in kubernetes.
    A Cache resource is a Deployment of certain image, validated at creation
    """

    kind = prop(str)
    api_version = prop(str)
    metadata = prop(V1ObjectMeta)

    spec = prop(CacheSpec)
    status = prop(CacheStatus)
