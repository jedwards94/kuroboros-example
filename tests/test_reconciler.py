import threading
import unittest
from unittest.mock import patch
from kuroboros.config import KuroborosConfig

from controllers.cache.v1beta1.crd import Cache, CacheStatus
from controllers.cache.v1beta1.reconciler import CacheReconciler
from controllers.cache.group_version import gvi


test_data = {
    "metadata": {
        "name": "test",
        "namespace": "default",
        "uid": "1",
        "resource_version": "1",
    },
    "spec": {
        "engine": "redis",
        "engine_version": "latest",
        "volume_size": "1Gi",
        "desired_size": "1",
        "resources": {
            "requests": {"cpu": "1", "memory": "1Gi"},
            "limits": {"cpu": "1", "memory": "1Gi"},
        },
    },
}


class TestReconciler(unittest.TestCase):

    def setUp(self) -> None:
        CacheReconciler.set_gvi(gvi)
        Cache.set_gvi(gvi)
        KuroborosConfig.load("operator.toml")
        return super().setUp()

    def test_reconciler_run(self):
        def mock_get(**kwargs):
            return []

        reconciler = CacheReconciler(("default", "test"))
        cache = Cache(**test_data)
        stop = threading.Event()
        with patch.object(
            reconciler, "patch", return_value=None
        ) as patch_, patch.object(
            reconciler, "get", side_effect=mock_get
        ) as get_list_:

            res = reconciler.reconcile(cache, stop)

            self.assertTrue(res.requeue)
            self.assertEqual(res.requeue_after_seconds, 0)
            self.assertIsNotNone(cache.status)
            self.assertIsInstance(cache.status, CacheStatus)
            patch_.assert_called_once()
            get_list_.assert_called_once()
