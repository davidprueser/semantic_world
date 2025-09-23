from functools import lru_cache
from typing import Type

from ormatic.utils import recursive_subclasses

from semantic_world.adapters.procthor.procthor_views import HouseholdObject


@lru_cache(maxsize=None)
def concrete_subclasses_of(cls: Type) -> list[Type]:
    return [
        subclass
        for subclass in recursive_subclasses(cls)
        if not subclass.__subclasses__()
    ]


def reason(world):
    result = []
    for cls in concrete_subclasses_of(HouseholdObject):
        result += cls.from_world(world)
    return result
