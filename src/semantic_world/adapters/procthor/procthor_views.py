from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property

from typing_extensions import List, Self
from typing import ClassVar, Optional, Iterable, Tuple, Type
import re

from ...views.views import Container, Table
from ...world import World

# Reuse the common world/view primitives so ProcTHOR views integrate seamlessly.
from ...world_description.world_entity import View, Body, Region
import re
from abc import ABC
from dataclasses import dataclass


@dataclass
class MatchRule:
    """Declarative matching rule over underscore-separated tokens.

    A rule matches if all required tokens are present, no forbidden tokens are present,
    and, if a prefix is defined, the name starts with that prefix followed by an underscore.
    """

    required: set[str] = field(default_factory=set)
    forbidden: set[str] = field(default_factory=set)
    prefix: Optional[str] = None
    base_priority: int = 0  # prefer specializations over generic classes

    def matches(self, name: str, tokens: list[str]) -> bool:
        if self.prefix and not name.startswith(self.prefix + "_"):
            return False
        if not self.required.issubset(tokens):
            return False
        if self.forbidden.intersection(tokens):
            return False
        return True


class AmbiguousNameError(ValueError):
    """Raised when more than one view class matches a given name with the same score."""


class UnresolvedNameError(ValueError):
    """Raised when no view class matches a given name."""


class ProcthorResolver:
    """Central resolver that deterministically maps a ProcTHOR name to exactly one class."""

    def __init__(self, classes: Iterable[Type["HouseholdObject"]]):
        self._classes: tuple[Type[HouseholdObject], ...] = tuple(classes)

    @staticmethod
    def _tokens(name: str) -> list[str]:
        # split and drop trailing numeric id tokens
        raw = name.lower().split("_")
        if raw and raw[-1].isdigit():
            raw = raw[:-1]
        return raw

    def resolve(self, name: str) -> Type["HouseholdObject"]:
        tokens = self._tokens(name)
        candidates: list[Tuple[Tuple[int, int, int], Type[HouseholdObject]]] = []
        for cls in self._classes:
            rule = getattr(cls, "rule", None)
            if rule is None:
                continue
            if rule.matches(name, tokens):
                # More required tokens and higher base_priority win; fewer forbidden preferred
                score = (len(rule.required), rule.base_priority, -len(rule.forbidden))
                candidates.append((score, cls))
        if not candidates:
            raise UnresolvedNameError(f"No class matches '{name}'")
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_cls = candidates[0]
        if len(candidates) > 1 and candidates[1][0] == best_score:
            other = candidates[1][1]
            raise AmbiguousNameError(
                f"Ambiguous mapping for '{name}': {best_cls.__name__} vs {other.__name__}"
            )
        return best_cls


@dataclass(eq=False)
class HouseholdObject(View, ABC):
    """
    Abstract base class for all household objects. Each view refers to a single Body.
    Each subclass automatically derives a MatchRule from its own class name and
    the names of its HouseholdObject ancestors. This makes specialized subclasses
    naturally more specific than their bases.
    """

    body: Body

    # Optional token rule used by the central resolver
    rule: ClassVar[Optional[MatchRule]] = None

    @staticmethod
    def _tokens_from_classname(name: str) -> list[str]:
        """Split a CamelCase class name into lowercase underscore-separated tokens."""
        # Insert underscore between lowercase/number followed by uppercase, then split
        s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        # Handle sequences like "RGBLED" -> "rgb_led"
        s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
        return s.lower().split("_")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # If a subclass did not provide an explicit rule, derive one from the class
        # hierarchy: include tokens from this class and all HouseholdObject ancestors
        # (excluding the abstract HouseholdObject itself). Sibling classes are
        # naturally excluded as we only consider the MRO.
        if getattr(cls, "rule", None) is None:
            required_tokens: set[str] = set()
            for base in cls.mro():
                if not issubclass(base, HouseholdObject):
                    continue
                if base is HouseholdObject:
                    continue
                # Only include classes declared in this module to avoid external mixins
                if base.__module__ != HouseholdObject.__module__:
                    continue
                required_tokens.update(HouseholdObject._tokens_from_classname(base.__name__))
            if required_tokens:
                cls.rule = MatchRule(required=required_tokens)


@dataclass(eq=False)
class Bottle(Container, HouseholdObject):
    """
    Abstract class for bottles.
    """

    rule = MatchRule(required={"bottle"}, forbidden={"soap", "wine"}, base_priority=-10)


@dataclass(eq=False)
class SoapBottle(Bottle):
    """
    A soap bottle.
    """

    rule = MatchRule(required={"soap", "bottle"}, base_priority=10)


@dataclass(eq=False)
class WineBottle(Bottle):
    """
    A wine bottle.
    """

    rule = MatchRule(required={"wine", "bottle"}, base_priority=10)


@dataclass(eq=False)
class Cup(Container, HouseholdObject):
    """
    A cup.
    """

    rule = MatchRule(required={"cup"})


@dataclass(eq=False)
class Mug(Container):
    """
    A mug.
    """

    rule = MatchRule(required={"mug"})


@dataclass(eq=False)
class Pan(HouseholdObject):
    """
    A pan.
    """

    rule = MatchRule(required={"pan"})


@dataclass(eq=False)
class PanLid(HouseholdObject):
    """
    A pan lid.
    """

    rule = MatchRule(required={"pan", "lid"})


@dataclass(eq=False)
class Pot(HouseholdObject):
    """
    A pot.
    """

    rule = MatchRule(required={"pot"})


@dataclass(eq=False)
class PotLid(HouseholdObject):
    """
    A pot lid.
    """

    rule = MatchRule(required={"pot", "lid"})


@dataclass(eq=False)
class Plate(HouseholdObject):
    """
    A plate.
    """

    rule = MatchRule(required={"plate"})


@dataclass(eq=False)
class Bowl(HouseholdObject):
    """
    A bowl.
    """

    rule = MatchRule(required={"bowl"})


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

    rule = MatchRule(required={"tomato"})


@dataclass(eq=False)
class Lettuce(Produce):
    """
    Lettuce.
    """

    rule = MatchRule(required={"lettuce"})


@dataclass(eq=False)
class Apple(Produce):
    """
    An apple.
    """

    rule = MatchRule(required={"apple"})


@dataclass(eq=False)
class Bread(HouseholdObject):
    """
    Bread.
    """

    rule = MatchRule(required={"bread"})


@dataclass(eq=False)
class FriedEgg(HouseholdObject):
    """
    A fried egg.
    """

    rule = MatchRule(required={"fried", "egg"})


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

    rule = MatchRule(required={"coffee", "table"}, base_priority=10)


@dataclass(eq=False)
class DiningTable(Table, HouseholdObject):
    """
    A dining table.
    """

    rule = MatchRule(required={"dining", "table"}, base_priority=10)


@dataclass(eq=False)
class SideTable(Table, HouseholdObject):
    """
    A side table.
    """

    rule = MatchRule(required={"side", "table"}, base_priority=10)


@dataclass(eq=False)
class Desk(Table, HouseholdObject):
    """
    A desk.
    """

    rule = MatchRule(required={"robothor", "desk"}, forbidden={"lamp"})


@dataclass(eq=False)
class Chair(Furniture):
    """
    Abstract class for chairs.
    """

    rule = MatchRule(
        required={"chair"},
        forbidden={"office", "armchair"},
        base_priority=-5,
    )


@dataclass(eq=False)
class OfficeChair(Chair):
    """
    An office chair.
    """

    rule = MatchRule(required={"robothor", "office", "chair"}, base_priority=10)


@dataclass(eq=False)
class Armchair(Chair):
    """
    An armchair.
    """

    rule = MatchRule(required={"robothor", "armchair"}, base_priority=10)


@dataclass(eq=False)
class ShelvingUnit(Furniture):
    """
    A shelving unit.
    """

    rule = MatchRule(required={"robothor", "shelving", "unit", "kallax"})


@dataclass(eq=False)
class Dresser(Furniture):
    """
    A dresser.
    """

    rule = MatchRule(required={"robothor", "dresser"})


@dataclass(eq=False)
class Bed(Furniture):
    """
    A bed.
    """

    rule = MatchRule(required={"robothor", "bed"})


@dataclass(eq=False)
class Sofa(Furniture):
    """
    A sofa.
    """

    rule = MatchRule(required={"robothor", "sofa"})


@dataclass(eq=False)
class ToiletPaperHanger(HouseholdObject):
    """
    A toilet paper hanger.
    """

    rule = MatchRule(required={"toilet", "paper", "hanger"})


@dataclass(eq=False)
class Sink(HouseholdObject):
    """
    A sink.
    """

    rule = MatchRule(required={"sink"}, forbidden={"faucet"})


@dataclass(eq=False)
class SinkFaucet(HouseholdObject):
    """
    A sink faucet.
    """

    rule = MatchRule(required={"sink", "faucet"}, forbidden={"knob"}, base_priority=5)


@dataclass(eq=False)
class SinkFaucetKnob(HouseholdObject):
    """
    A sink faucet knob.
    """

    rule = MatchRule(required={"sink", "faucet", "knob"}, base_priority=10)


@dataclass(eq=False)
class Faucet(HouseholdObject):
    """
    A standalone faucet.
    """

    rule = MatchRule(required={"faucet"}, forbidden={"sink"})


@dataclass(eq=False)
class LightSwitch(HouseholdObject):
    """
    A light switch.
    """

    rule = MatchRule(required={"light", "switch"}, forbidden={"dial"}, base_priority=10)


@dataclass(eq=False)
class LightSwitchDial(HouseholdObject):
    """
    A light switch dial.
    """

    rule = MatchRule(required={"light", "switch", "dial"}, base_priority=10)


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

    rule = MatchRule(required={"lamp"}, forbidden={"desk"})


@dataclass(eq=False)
class Television(Electronics):
    """
    A television.
    """

    rule = MatchRule(required={"television"}, forbidden={"stand"})


@dataclass(eq=False)
class Laptop(Electronics):
    """
    A laptop.
    """

    rule = MatchRule(required={"laptop"}, forbidden={"lid"})


@dataclass(eq=False)
class Cellphone(Electronics):
    """
    A cellphone.
    """

    rule = MatchRule(required={"cellphone"})


@dataclass(eq=False)
class AlarmClock(Electronics):
    """
    An alarm clock.
    """

    rule = MatchRule(
        required={"alarm", "clock"}, forbidden={"button", "minute", "hour"}
    )


@dataclass(eq=False)
class Remote(Electronics):
    """
    A remote control.
    """

    rule = MatchRule(required={"remote"})


@dataclass(eq=False)
class WallDecor(HouseholdObject):
    """
    Wall decorations.
    """

    rule = MatchRule(required={"wall", "decor"})


@dataclass(eq=False)
class WallPanel(HouseholdObject):
    """
    A wall panel.
    """

    rule = MatchRule(required={"wall", "panel"})


@dataclass(eq=False)
class Pillow(HouseholdObject):
    """
    A pillow.
    """

    rule = MatchRule(required={"pillow"})


@dataclass(eq=False)
class GarbageBin(HouseholdObject):
    """
    A garbage bin.
    """

    rule = MatchRule(required={"garbage", "bin"})


@dataclass(eq=False)
class Houseplant(HouseholdObject):
    """
    A houseplant.
    """

    rule = MatchRule(required={"houseplant"})


@dataclass(eq=False)
class SprayBottle(HouseholdObject):
    """
    A spray bottle.
    """

    rule = MatchRule(required={"spray", "bottle"})


@dataclass(eq=False)
class Vase(HouseholdObject):
    """
    A vase.
    """

    rule = MatchRule(required={"vase"})


@dataclass(eq=False)
class Book(HouseholdObject):
    """
    A book.
    """

    book_front: Optional[BookFront] = None
    rule = MatchRule(required={"book"}, forbidden={"front"})


@dataclass(eq=False)
class BookFront(HouseholdObject):
    rule = MatchRule(required={"book", "front"})


@dataclass(eq=False)
class Candle(HouseholdObject):
    """
    A candle.
    """

    rule = MatchRule(required={"candle"})


@dataclass(eq=False)
class SaltPepperShaker(HouseholdObject):
    """
    A salt and pepper shaker.
    """

    rule = MatchRule(required={"salt", "pepper", "shaker"})


@dataclass(eq=False)
class Fork(HouseholdObject):
    """
    A fork.
    """

    rule = MatchRule(required={"fork"})


@dataclass(eq=False)
class Knife(HouseholdObject):
    """
    A butter knife.
    """

    rule = MatchRule(required={"knife"})


@dataclass(eq=False)
class Pencil(HouseholdObject):
    """
    A pencil.
    """

    name_pattern = re.compile(r"^robothor_pencil$")


@dataclass(eq=False)
class Pen(HouseholdObject):
    """
    A pen.
    """

    name_pattern = re.compile(r"^robothor_pen_signo$")


@dataclass(eq=False)
class TennisRacquet(HouseholdObject):
    """
    A tennis racquet.
    """

    name_pattern = re.compile(r"^robothor_tennis_racquet_speed_kids$")


@dataclass(eq=False)
class BaseballBat(HouseholdObject):
    """
    A baseball bat.
    """

    name_pattern = re.compile(r"^robothor_baseball_bat_rawlings$")


@dataclass(eq=False)
class Basketball(HouseholdObject):
    """
    A basketball.
    """

    name_pattern = re.compile(r"^robothor_basketball_rhode_island_novelty$")


@dataclass(eq=False)
class LiquidCap(HouseholdObject):
    """
    A liquid cap.
    """

    name_pattern = re.compile(r"^liquid_cap_(\w+)$")
