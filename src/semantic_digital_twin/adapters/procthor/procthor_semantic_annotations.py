from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property, lru_cache

from typing_extensions import List, Self
from typing import ClassVar, Optional, Iterable, Tuple, Type, Dict, Set
import re

from semantic_digital_twin.semantic_annotations.semantic_annotations import Furniture, Table, Container, SupportingSurface

from ...world_description.world_entity import SemanticAnnotation, Body, Region
import re
from abc import ABC
from dataclasses import dataclass


def camel_case_split(word: str) -> List[str]:
    """
    :param word: The word to split
    :return: A set of strings where each string is a camel case split of the original word
    """
    result = []
    start = 0
    for i, c in enumerate(word[1:], 1):
        if c.isupper():
            result.append(word[start:i])
            start = i
    result.append(word[start:])
    return result


class AmbiguousNameError(ValueError):
    """Raised when more than one semantic annotation class matches a given name with the same score."""


class UnresolvedNameError(ValueError):
    """Raised when no semantic annotation class matches a given name."""


@dataclass
class ProcthorResolver:
    """Central resolver that deterministically maps a ProcTHOR name to exactly one class."""

    classes: List[Type[HouseholdObject]] = field(default_factory=list)

    def resolve(self, name: str) -> Optional[Type[HouseholdObject]]:
        # remove all numbers from the name
        name_tokens = set(n.lower() for n in re.sub(r"\d+", "", name).split("_"))
        possible_results = []
        for cls in self.classes:
            matches = cls.class_name_tokens().intersection(
                name_tokens
            ) or cls._additional_names.intersection(name_tokens)
            possible_results.append((cls, matches))

        if len(possible_results) == 0:
            return None
        # sort by max number of matches
        possible_results = sorted(
            possible_results, key=lambda x: len(x[1]), reverse=True
        )

        # if there are no matches, don't choose a class
        if len(possible_results[0][1]) == 0:
            return None
        best_cls, best_matches = possible_results[0]
        return best_cls


@dataclass(eq=False)
class HouseholdObject(SemanticAnnotation, ABC):
    """
    Abstract base class for all household objects. Each semantic annotation refers to a single Body.
    Each subclass automatically derives a MatchRule from its own class name and
    the names of its HouseholdObject ancestors. This makes specialized subclasses
    naturally more specific than their bases.
    """

    body: Body

    _additional_names: ClassVar[Set[str]] = set()
    """
    Additional names that can be used to match this object.
    """

    @classmethod
    @lru_cache(maxsize=None)
    def class_name_tokens(cls) -> Set[str]:
        return set(n.lower() for n in camel_case_split(cls.__name__))


@dataclass(eq=False)
class Bottle(Container, HouseholdObject):
    """
    Abstract class for bottles.
    """


@dataclass(eq=False)
class Statue(HouseholdObject): ...


@dataclass(eq=False)
class SoapBottle(Bottle):
    """
    A soap bottle.
    """


@dataclass(eq=False)
class WineBottle(Bottle):
    """
    A wine bottle.
    """


@dataclass(eq=False)
class MustardBottle(Bottle):
    """
    A mustard bottle.
    """


@dataclass(eq=False)
class DrinkingContainer(Container, HouseholdObject): ...


@dataclass(eq=False)
class Cup(DrinkingContainer):
    """
    A cup.
    """


@dataclass(eq=False)
class Mug(DrinkingContainer):
    """
    A mug.
    """


@dataclass(eq=False)
class CookingContainer(Container, HouseholdObject): ...


@dataclass(eq=False)
class Lid(HouseholdObject): ...


@dataclass(eq=False)
class Pan(CookingContainer):
    """
    A pan.
    """


@dataclass(eq=False)
class PanLid(Lid):
    """
    A pan lid.
    """


@dataclass(eq=False)
class Pot(CookingContainer):
    """
    A pot.
    """


@dataclass(eq=False)
class PotLid(Lid):
    """
    A pot lid.
    """


@dataclass(eq=False)
class Plate(HouseholdObject, SupportingSurface):
    """
    A plate.
    """


@dataclass(eq=False)
class Bowl(HouseholdObject, SupportingSurface):
    """
    A bowl.
    """


# Food Items
@dataclass(eq=False)
class Food(HouseholdObject): ...


@dataclass(eq=False)
class TunaCan(Food):
    """
    A tuna can.
    """


@dataclass(eq=False)
class Bread(Food):
    """
    Bread.
    """

    _additional_names = {
        "bumpybread",
        "whitebread",
        "loafbread",
        "honeybread",
        "grainbread",
    }


@dataclass(eq=False)
class CheezeIt(Food):
    """
    Some type of cracker.
    """


@dataclass(eq=False)
class Pringles(Food):
    """
    Pringles chips
    """


@dataclass(eq=False)
class GelatinBox(Food):
    """
    Gelatin box.
    """


@dataclass(eq=False)
class TomatoSoup(Food):
    """
    Tomato soup.
    """


@dataclass(eq=False)
class Produce(Food):
    """
    In American English, produce generally refers to fresh fruits and vegetables intended to be eaten by humans.
    """

    pass


@dataclass(eq=False)
class Tomato(Produce):
    """
    A tomato.
    """


@dataclass(eq=False)
class Lettuce(Produce):
    """
    Lettuce.
    """


@dataclass(eq=False)
class Apple(Produce):
    """
    An apple.
    """


@dataclass(eq=False)
class Banana(Produce):
    """
    A banana.
    """


@dataclass(eq=False)
class Orange(Produce):
    """
    An orange.
    """


@dataclass(eq=False)
class CoffeeTable(Table, Furniture, HouseholdObject):
    """
    A coffee table.
    """


@dataclass(eq=False)
class DiningTable(Table, Furniture, HouseholdObject):
    """
    A dining table.
    """


@dataclass(eq=False)
class SideTable(Table, Furniture, HouseholdObject):
    """
    A side table.
    """


@dataclass(eq=False)
class Desk(Table, Furniture, HouseholdObject):
    """
    A desk.
    """


@dataclass(eq=False)
class Chair(Furniture, HouseholdObject):
    """
    Abstract class for chairs.
    """


@dataclass(eq=False)
class OfficeChair(Chair):
    """
    An office chair.
    """


@dataclass(eq=False)
class Armchair(Chair):
    """
    An armchair.
    """


@dataclass(eq=False)
class ShelvingUnit(Furniture, HouseholdObject, SupportingSurface):
    """
    A shelving unit.
    """


@dataclass(eq=False)
class Bed(Furniture, HouseholdObject, SupportingSurface):
    """
    A bed.
    """


@dataclass(eq=False)
class Sofa(Furniture, HouseholdObject, SupportingSurface):
    """
    A sofa.
    """


@dataclass(eq=False)
class Sink(HouseholdObject):
    """
    A sink.
    """


@dataclass(eq=False)
class Kettle(CookingContainer): ...


@dataclass(eq=False)
class Decor(HouseholdObject): ...


@dataclass(eq=False)
class WallDecor(Decor):
    """
    Wall decorations.
    """


@dataclass(eq=False)
class Cloth(HouseholdObject): ...


@dataclass(eq=False)
class Poster(WallDecor):
    """
    A poster.
    """


@dataclass(eq=False)
class WallPanel(HouseholdObject):
    """
    A wall panel.
    """


@dataclass(eq=False)
class Potato(Produce): ...


@dataclass(eq=False)
class GarbageBin(Container, HouseholdObject):
    """
    A garbage bin.
    """


@dataclass(eq=False)
class Drone(HouseholdObject): ...


@dataclass(eq=False)
class ProcthorBox(Container, HouseholdObject): ...


@dataclass(eq=False)
class Houseplant(HouseholdObject):
    """
    A houseplant.
    """


@dataclass(eq=False)
class SprayBottle(HouseholdObject):
    """
    A spray bottle.
    """


@dataclass(eq=False)
class Vase(HouseholdObject):
    """
    A vase.
    """


@dataclass(eq=False)
class Book(HouseholdObject):
    """
    A book.
    """

    book_front: Optional[BookFront] = None


@dataclass(eq=False)
class BookFront(HouseholdObject): ...


@dataclass(eq=False)
class SaltPepperShaker(HouseholdObject):
    """
    A salt and pepper shaker.
    """


@dataclass(eq=False)
class Cuttlery(HouseholdObject): ...


@dataclass(eq=False)
class Fork(Cuttlery):
    """
    A fork.
    """


@dataclass(eq=False)
class Knife(Cuttlery):
    """
    A butter knife.
    """


@dataclass(eq=False)
class Spoon(Cuttlery): ...


@dataclass(eq=False)
class Pencil(HouseholdObject):
    """
    A pencil.
    """


@dataclass(eq=False)
class Pen(HouseholdObject):
    """
    A pen.
    """


@dataclass(eq=False)
class Baseball(HouseholdObject):
    """
    A baseball.
    """


@dataclass(eq=False)
class LiquidCap(HouseholdObject):
    """
    A liquid cap.
    """
