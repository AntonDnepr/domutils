from typing import List, Optional

from apps.core.consts import VANILLA
from apps.core.redis import get_redis_client
from redis_om import Field, HashModel, JsonModel, Migrator


class Dom6Nation(HashModel):
    name: str = Field(index=True, full_text_search=True)
    dominions_id: int = Field(index=True)
    era: str
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


class Dom6Unit(JsonModel):
    name: str = Field(index=True, full_text_search=True)
    dominions_id: int = Field(index=True)
    mod: Optional[str] = Field(index=True, default=VANILLA)
    goldcost: Optional[int] = None
    holycost: Optional[int] = None
    is_commander: bool
    # https://github.com/redis/redis-om-python/issues/605#issuecomment-2068726260
    nations_ids: List[str] = Field(index=True, default=[])

    class Meta:
        database = get_redis_client()


class Dom6Item(HashModel):
    name: str = Field(index=True, full_text_search=True)
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


Migrator().run()
