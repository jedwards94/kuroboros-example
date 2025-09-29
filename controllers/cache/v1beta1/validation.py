from kuroboros.webhook import BaseValidationWebhook, Request, OperationsEnum
from kuroboros.exceptions import ValidationWebhookError
from controllers.cache.v1beta1.crd import Cache


class CacheValidation(BaseValidationWebhook[Cache]):
    register_on = [OperationsEnum.CREATE, OperationsEnum.UPDATE]

    allowed_images = {
        "redis": ["7.1", "latest"],
        "memcached": ["latest"],
        "valkey": ["latest"],
    }

    def validate(self, request: Request[Cache]):
        assert request.object is not None
        engine = request.object.spec.engine
        engine_version = request.object.spec.engine_version

        if request.operation == OperationsEnum.UPDATE:
            assert request.old_object is not None
            old_engine = request.old_object.spec.engine
            if old_engine != engine:
                raise ValidationWebhookError(
                    f"Cannot change an already created engine ({old_engine} -> {engine})"
                )

        if engine_version not in self.allowed_images[engine]:
            raise ValidationWebhookError(
                f"{engine_version} is not a valid version for {engine}"
            )
