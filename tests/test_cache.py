import pytest

from hybridrag.authorization.models import UserContext
from hybridrag.caching.redis_cache import RedisCache
from hybridrag.config import get_settings


def test_exact_cache():
    settings = get_settings()
    cache = RedisCache(settings)
    user = UserContext(user_id="u1", roles=("employee",), tenant_id="t1")

    query = "What is the remote work policy?"
    answer = "2 days per week."

    # Set and Get
    cache.set_exact(query, answer, user)
    assert cache.get_exact(query, user) == answer

    # Different user, same query -> No hit
    user2 = UserContext(user_id="u2", roles=("employee",), tenant_id="t2")
    assert cache.get_exact(query, user2) is None


def test_semantic_cache():
    settings = get_settings()
    cache = RedisCache(settings)
    user = UserContext(user_id="u1", roles=("employee",), tenant_id="t1")

    query = "Remote work policy"
    emb = [0.1] * 384
    answer = "2 days per week."

    cache.set_semantic(query, emb, answer, user)

    # Similar query (using same embedding for test)
    assert cache.get_semantic(emb, "Remote work guidelines", user) == answer

    # Different user -> No hit
    user2 = UserContext(user_id="u2", roles=("employee",), tenant_id="t2")
    assert cache.get_semantic(emb, "Remote work guidelines", user2) is None


if __name__ == "__main__":
    pytest.main([__file__])
