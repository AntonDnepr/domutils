from typing import Optional

from apps.core.consts import VANILLA
from apps.core.redis import get_redis_client
from redis_om import Field, HashModel, Migrator


class Nation(HashModel):
    name: str = Field(index=True, full_text_search=True)
    dominions_id: int
    era: str
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


class Unit(HashModel):
    name: str = Field(index=True, full_text_search=True)
    dominions_id: int
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


Migrator().run()
