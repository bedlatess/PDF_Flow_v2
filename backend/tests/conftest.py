"""
Pytest 配置与共享 fixture

由于本机无 Docker（PostgreSQL/Redis）且未安装 redis/celery/PIL/magic 等库，
本 conftest 在导入应用前向 sys.modules 注入轻量 stub，并用 SQLite + 内存 FakeRedis
替代真实基础设施，从而在无基础设施环境下端到端验证 认证流程 / 文件校验 / 下载逻辑。
"""
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# ---------------------------------------------------------------------------
# 1. 必须在导入 app 之前设置环境变量（config.py 用 pydantic-settings 强校验）
# ---------------------------------------------------------------------------
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
os.environ["DATABASE_URL"] = "sqlite:///./test_pdfflow.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "false"
os.environ["UPLOAD_DIR"] = os.path.join(os.getcwd(), ".tmp", "uploads")


# ---------------------------------------------------------------------------
# 2. FakeRedis：内存版，覆盖项目实际用到的方法（get/setex/pipeline/zset 等）
# ---------------------------------------------------------------------------
class _FakePipeline:
    def __init__(self, store):
        self._store = store
        self._results = []

    def zremrangebyscore(self, *a, **k):
        self._results.append(0); return self

    def zcard(self, key):
        z = self._store.get(key, {})
        self._results.append(len(z) if isinstance(z, dict) else 0); return self

    def zadd(self, key, mapping):
        z = self._store.setdefault(key, {})
        z.update(mapping); self._results.append(1); return self

    def expire(self, *a, **k):
        self._results.append(True); return self

    def execute(self):
        r = self._results; self._results = []; return r


class FakeRedis:
    def __init__(self):
        self.store = {}

    @classmethod
    def from_url(cls, *a, **k):
        return cls()

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value; return True

    def set(self, key, value, *a, **k):
        self.store[key] = value; return True

    def delete(self, *keys):
        for key in keys:
            self.store.pop(key, None)
        return True

    def pipeline(self):
        return _FakePipeline(self.store)

    def zrange(self, *a, **k):
        return []

    def ping(self):
        return True


# ---------------------------------------------------------------------------
# 3. 向 sys.modules 注入缺失库的 stub（在导入 app 之前）
# ---------------------------------------------------------------------------
def _install_stubs():
    # uvicorn（main.py 顶部 import，仅 __main__ 使用）
    uvicorn_mod = types.ModuleType("uvicorn")
    uvicorn_mod.run = MagicMock()
    sys.modules["uvicorn"] = uvicorn_mod

    # redis
    redis_mod = types.ModuleType("redis")
    redis_mod.Redis = FakeRedis
    sys.modules["redis"] = redis_mod

    # celery + celery.result
    celery_mod = types.ModuleType("celery")

    class _FakeTask:
        def __init__(self, fn=None):
            self.fn = fn

        def apply_async(self, *a, **k):
            return MagicMock(id=k.get("task_id", "fake-task"))

        def __call__(self, *a, **k):
            return self.fn(*a, **k) if self.fn else None

    class _FakeCelery:
        def __init__(self, *a, **k):
            self.conf = MagicMock()
            self.control = MagicMock()
            self.control.ping.return_value = [{"celery@fake": {"ok": "pong"}}]

        def task(self, *a, **k):
            def deco(fn):
                return _FakeTask(fn)
            # 支持 @task 与 @task(...)
            if a and callable(a[0]):
                return _FakeTask(a[0])
            return deco

        def autodiscover_tasks(self, *a, **k):
            pass

    celery_mod.Celery = _FakeCelery
    celery_mod.Task = object
    sys.modules["celery"] = celery_mod

    result_mod = types.ModuleType("celery.result")

    class AsyncResult:
        def __init__(self, *a, **k):
            self.state = "PENDING"
            self.result = None

    result_mod.AsyncResult = AsyncResult
    sys.modules["celery.result"] = result_mod

    # kombu
    kombu_mod = types.ModuleType("kombu")

    class Queue:
        def __init__(self, *a, **k):
            self.args = a
            self.kwargs = k

    kombu_mod.Queue = Queue
    sys.modules["kombu"] = kombu_mod

    # authlib
    authlib_mod = types.ModuleType("authlib")
    integrations_mod = types.ModuleType("authlib.integrations")
    starlette_client_mod = types.ModuleType("authlib.integrations.starlette_client")

    class OAuth:
        def __init__(self, *a, **k):
            pass

        def register(self, *a, **k):
            return None

    starlette_client_mod.OAuth = OAuth
    sys.modules["authlib"] = authlib_mod
    sys.modules["authlib.integrations"] = integrations_mod
    sys.modules["authlib.integrations.starlette_client"] = starlette_client_mod

    # stripe
    stripe_mod = types.ModuleType("stripe")
    stripe_mod.api_key = None
    stripe_mod.error = types.SimpleNamespace(StripeError=Exception)

    def _stripe_create(*a, **k):
        return types.SimpleNamespace(
            id="stripe_test_id",
            url="https://example.com/checkout",
        )

    stripe_mod.Customer = types.SimpleNamespace(create=_stripe_create)
    stripe_mod.checkout = types.SimpleNamespace(
        Session=types.SimpleNamespace(create=_stripe_create)
    )
    sys.modules["stripe"] = stripe_mod

    # google generative ai
    google_mod = types.ModuleType("google")
    generativeai_mod = types.ModuleType("google.generativeai")

    class _FakeGenerativeModel:
        def __init__(self, *a, **k):
            pass

        def generate_content(self, *a, **k):
            return types.SimpleNamespace(
                text='{"summary":"stub","key_points":[],"word_count":0,"topics":[]}'
            )

    generativeai_mod.configure = MagicMock()
    generativeai_mod.GenerativeModel = _FakeGenerativeModel
    sys.modules["google"] = google_mod
    sys.modules["google.generativeai"] = generativeai_mod

    # sentry
    sentry_sdk_mod = types.ModuleType("sentry_sdk")
    sentry_sdk_mod.init = MagicMock()
    sentry_sdk_mod.set_user = MagicMock()
    sentry_sdk_mod.set_context = MagicMock()
    sentry_sdk_mod.capture_exception = MagicMock()
    sys.modules["sentry_sdk"] = sentry_sdk_mod

    sentry_fastapi_mod = types.ModuleType("sentry_sdk.integrations.fastapi")
    sentry_fastapi_mod.FastApiIntegration = type("FastApiIntegration", (), {})
    sys.modules["sentry_sdk.integrations.fastapi"] = sentry_fastapi_mod

    sentry_sqlalchemy_mod = types.ModuleType("sentry_sdk.integrations.sqlalchemy")
    sentry_sqlalchemy_mod.SqlalchemyIntegration = type("SqlalchemyIntegration", (), {})
    sys.modules["sentry_sdk.integrations.sqlalchemy"] = sentry_sqlalchemy_mod

    # posthog
    posthog_mod = types.ModuleType("posthog")

    class _FakePosthog:
        def __init__(self, *a, **k):
            pass

    posthog_mod.Posthog = _FakePosthog
    sys.modules["posthog"] = posthog_mod

    # PIL + PIL.Image
    pil_mod = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")
    image_mod.Image = MagicMock
    image_mod.open = MagicMock()
    pil_mod.Image = image_mod
    sys.modules["PIL"] = pil_mod
    sys.modules["PIL.Image"] = image_mod

    # magic（python-magic）
    magic_mod = types.ModuleType("magic")
    magic_mod.from_buffer = MagicMock(return_value="application/pdf")
    sys.modules["magic"] = magic_mod

    # pdf2image
    pdf2image_mod = types.ModuleType("pdf2image")
    pdf2image_mod.convert_from_path = MagicMock(return_value=[])
    sys.modules["pdf2image"] = pdf2image_mod

    # pytesseract
    pyt_mod = types.ModuleType("pytesseract")
    pyt_mod.image_to_string = MagicMock(return_value="")
    pyt_mod.image_to_data = MagicMock(return_value={"conf": []})
    pyt_mod.Output = types.SimpleNamespace(DICT="dict")
    sys.modules["pytesseract"] = pyt_mod


_install_stubs()


# ---------------------------------------------------------------------------
# 4. SQLite 测试数据库 + 依赖覆盖（在 stub 之后导入 app）
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import Base
from app.core.database import get_db
from app.main import app

# 内存 SQLite（StaticPool 保证多连接共享同一内存库）
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """每个测试函数一套干净的表结构 + TestClient"""
    from fastapi.testclient import TestClient

    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
