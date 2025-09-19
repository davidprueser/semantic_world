from typing import Type

from ormatic.utils import recursive_subclasses

from semantic_world.adapters.procthor.procthor_views import HouseholdObject


def reason(world):
    result = []
    for cls in recursive_subclasses(HouseholdObject):
        cls: Type[HouseholdObject]
        if not cls.__subclasses__():
            result += cls.from_world(world)
    return result
