from typing import Optional

from redis_om import Field, HashModel, Migrator

DE = "de"
DEBUG = "debug"
VANILLA = "vanilla"
OTHER = "other"


class Nation(HashModel):
    name: str = Field(index=True)
    dominions_id: int
    era: str
    mod: Optional[str] = Field(index=True, default=VANILLA)


class Unit(HashModel):
    name: str = Field(index=True)
    dominions_id: int
    mod: Optional[str] = Field(index=True, default=VANILLA)


Migrator().run()
