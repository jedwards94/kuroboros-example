from kuroboros.webhook import BaseMutationWebhook, Request, OperationsEnum
from controllers.cache.v1beta1.crd import Cache


class CacheMutation(BaseMutationWebhook[Cache]):
    register_on = [OperationsEnum.CREATE]

    def mutate(self, request: Request[Cache]) -> Cache:
        assert request.object is not None
        if request.object.metadata.labels is None:
            request.object.metadata.labels = {}
        
        request.object.metadata.labels["owner"] = request.user_info["username"]
        return request.object
