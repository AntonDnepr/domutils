import pytest
from core.redis import get_redis_client
from domdata.models import TEST, Nation, Unit


@pytest.fixture(scope="session", autouse=True)
def generated_data():
    client = get_redis_client()
    pipeline = client.pipeline()
    unit1 = Unit(
        dominions_id=999999,
        name="TestMonster",
        mod=TEST,
    )
    unit1.save(pipeline=pipeline)
    unit2 = Unit(
        dominions_id=999998,
        name="AlohaMonster2",
        mod=TEST,
    )
    unit2.save(pipeline=pipeline)
    nation1 = Nation(
        dominions_id="000000",
        name="AlohaNation",
        era="LA",
        mod=TEST,
    )
    nation1.save(pipeline=pipeline)
    nation2 = Nation(
        dominions_id="111111",
        name="MonsterNation",
        era="LA",
        mod=TEST,
    )
    nation2.save(pipeline=pipeline)
    pipeline.execute()
    yield
    units = Unit.find(Unit.mod == TEST).all()
    for unit in units:
        unit.delete(pk=unit.pk, pipeline=pipeline)
    nations = Nation.find(Nation.mod == TEST).all()
    for nation in nations:
        nation.delete(pk=nation.pk, pipeline=pipeline)
    pipeline.execute()
