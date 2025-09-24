from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property, lru_cache

from typing_extensions import List, Self
from typing import ClassVar, Optional, Iterable, Tuple, Type, Dict, Set
import re

from ...views.views import Container, Table
from ...world import World

# Reuse the common world/view primitives so ProcTHOR views integrate seamlessly.
from ...world_description.world_entity import View, Body, Region
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
    """Raised when more than one view class matches a given name with the same score."""


class UnresolvedNameError(ValueError):
    """Raised when no view class matches a given name."""


@dataclass
class ProcthorResolver:
    """Central resolver that deterministically maps a ProcTHOR name to exactly one class."""

    classes: List[Type[HouseholdObject]]

    def resolve(self, name: str) -> Type[HouseholdObject]:
        # remove all numbers from the name
        name_tokens = set(n.lower() for n in re.sub(r"\d+", "", name).split("_"))
        possible_results = []
        for cls in self.classes:
            if cls.class_name_tokens().issubset(name_tokens):
                possible_results.append(cls)

        if len(possible_results) == 1:
            return possible_results[0]
        elif len(possible_results) > 1:
            possible_results.sort(
                key=lambda c: len(c.class_name_tokens().intersection(name_tokens))
            )

            return possible_results[-1]

        else:
            raise UnresolvedNameError(f"No match found for '{name}'")


@dataclass(eq=False)
class HouseholdObject(View, ABC):
    """
    Abstract base class for all household objects. Each view refers to a single Body.
    Each subclass automatically derives a MatchRule from its own class name and
    the names of its HouseholdObject ancestors. This makes specialized subclasses
    naturally more specific than their bases.
    """

    body: Body

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
class Dumbbell(HouseholdObject): ...


@dataclass(eq=False)
class WineBottle(Bottle):
    """
    A wine bottle.
    """


@dataclass(eq=False)
class Cup(Container, HouseholdObject):
    """
    A cup.
    """


@dataclass(eq=False)
class Mug(Container, HouseholdObject):
    """
    A mug.
    """


@dataclass(eq=False)
class Pan(HouseholdObject):
    """
    A pan.
    """


@dataclass(eq=False)
class PanLid(HouseholdObject):
    """
    A pan lid.
    """


@dataclass(eq=False)
class Pot(HouseholdObject):
    """
    A pot.
    """


@dataclass(eq=False)
class PotLid(HouseholdObject):
    """
    A pot lid.
    """


@dataclass(eq=False)
class Plate(HouseholdObject):
    """
    A plate.
    """


@dataclass(eq=False)
class Bowl(HouseholdObject):
    """
    A bowl.
    """


# Food Items
@dataclass(eq=False)
class Produce(HouseholdObject):
    """
    Abstract class for produce.
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
class Bread(HouseholdObject):
    """
    Bread.
    """


@dataclass(eq=False)
class FriedEgg(HouseholdObject):
    """
    A fried egg.
    """


# Furniture and Fixtures
@dataclass(eq=False)
class Furniture(HouseholdObject):
    """
    Abstract class for furniture.
    """

    pass


@dataclass(eq=False)
class CoffeeTable(Table, HouseholdObject):
    """
    A coffee table.
    """


@dataclass(eq=False)
class DiningTable(Table, HouseholdObject):
    """
    A dining table.
    """


@dataclass(eq=False)
class Oven(HouseholdObject): ...


@dataclass(eq=False)
class Egg(Produce): ...


@dataclass(eq=False)
class Toaster(HouseholdObject): ...


@dataclass(eq=False)
class SideTable(Table, HouseholdObject):
    """
    A side table.
    """


@dataclass(eq=False)
class Desk(Table, HouseholdObject):
    """
    A desk.
    """


@dataclass(eq=False)
class Chair(Furniture):
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
class ShelvingUnit(Furniture):
    """
    A shelving unit.
    """


@dataclass(eq=False)
class Dresser(Furniture):
    """
    A dresser.
    """


@dataclass(eq=False)
class Bed(Furniture):
    """
    A bed.
    """


@dataclass(eq=False)
class Sofa(Furniture):
    """
    A sofa.
    """


@dataclass(eq=False)
class ToiletPaperHanger(HouseholdObject):
    """
    A toilet paper hanger.
    """


@dataclass(eq=False)
class PaperTowel(HouseholdObject): ...


@dataclass(eq=False)
class Omelette(HouseholdObject): ...


@dataclass(eq=False)
class Sink(HouseholdObject):
    """
    A sink.
    """


@dataclass(eq=False)
class SinkFaucet(HouseholdObject):
    """
    A sink faucet.
    """


@dataclass(eq=False)
class SinkFaucetKnob(HouseholdObject):
    """
    A sink faucet knob.
    """


@dataclass(eq=False)
class Faucet(HouseholdObject):
    """
    A standalone faucet.
    """


@dataclass(eq=False)
class LightSwitch(HouseholdObject):
    """
    A light switch.
    """


@dataclass(eq=False)
class LightSwitchDial(HouseholdObject):
    """
    A light switch dial.
    """


# Electronics and Accessories
@dataclass(eq=False)
class Electronics(HouseholdObject):
    """
    Abstract class for electronics.
    """

    pass


@dataclass(eq=False)
class Lamp(Electronics):
    """
    A lamp.
    """


@dataclass(eq=False)
class Television(Electronics):
    """
    A television.
    """


@dataclass(eq=False)
class Laptop(Electronics):
    """
    A laptop.
    """


@dataclass(eq=False)
class Cellphone(Electronics):
    """
    A cellphone.
    """


@dataclass(eq=False)
class AlarmClock(Electronics):
    """
    An alarm clock.
    """


@dataclass(eq=False)
class Remote(Electronics):
    """
    A remote control.
    """


@dataclass(eq=False)
class Kettle(Container, HouseholdObject): ...


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
class Pillow(HouseholdObject):
    """
    A pillow.
    """


@dataclass(eq=False)
class Bin(HouseholdObject): ...


@dataclass(eq=False)
class GarbageBin(Bin):
    """
    A garbage bin.
    """


@dataclass(eq=False)
class Drone(HouseholdObject): ...


@dataclass(eq=False)
class Box(Container, HouseholdObject): ...


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
class Candle(HouseholdObject):
    """
    A candle.
    """


@dataclass(eq=False)
class SaltPepperShaker(HouseholdObject):
    """
    A salt and pepper shaker.
    """


@dataclass(eq=False)
class Fork(HouseholdObject):
    """
    A fork.
    """


@dataclass(eq=False)
class Knife(HouseholdObject):
    """
    A butter knife.
    """


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
class TennisRacquet(HouseholdObject):
    """
    A tennis racquet.
    """


@dataclass(eq=False)
class BaseballBat(HouseholdObject):
    """
    A baseball bat.
    """


@dataclass(eq=False)
class Basketball(HouseholdObject):
    """
    A basketball.
    """


@dataclass(eq=False)
class LiquidCap(HouseholdObject):
    """
    A liquid cap.
    """
