from typing import Optional

from apps.core.consts import VANILLA
from apps.core.redis import get_redis_client
from redis_om import Field, HashModel, Migrator


class Dom6Nation(HashModel):
    name: str = Field(index=True, full_text_search=True)
    dominions_id: int
    era: str
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


class Dom6Unit(HashModel):
    name: str = Field(index=True, full_text_search=True)
    dominions_id: int = Field(index=True)
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


class Dom6Item(HashModel):
    name: str = Field(index=True, full_text_search=True)
    mod: Optional[str] = Field(index=True, default=VANILLA)

    class Meta:
        database = get_redis_client()


Migrator().run()
