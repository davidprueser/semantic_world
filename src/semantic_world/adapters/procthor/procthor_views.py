from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property

from typing_extensions import List, Self
from typing import ClassVar, Optional, Iterable, Tuple, Type
import re


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


def build_procthor_resolver() -> ProcthorResolver:
    """Build a resolver from all concrete HouseholdObject subclasses in this module that define rules."""
    classes: list[type[HouseholdObject]] = []
    for obj in list(globals().values()):
        if (
            isinstance(obj, type)
            and issubclass(obj, HouseholdObject)
            and obj is not HouseholdObject
        ):
            if getattr(obj, "rule", None) is not None:
                classes.append(obj)
    return ProcthorResolver(classes)


@dataclass(eq=False)
class HouseholdObject(View, ABC):
    """
    Abstract base class for all household objects. Each view refers to a single Body.
    """

    body: Body
    name_pattern: ClassVar[Optional[re.Pattern]] = field(init=False, default=None)

    # Optional token rule used by the central resolver
    rule: ClassVar[Optional[MatchRule]] = None

    @classmethod
    def from_world(cls, world: World) -> List[Self]:
        """
        Create views for all bodies in the world whose unprefixed name matches the class' name_pattern.

        :param world: The world to search in.
        :return: A list of view instances with their corresponding body assigned.
        """
        views: List[Self] = []
        for body in world.bodies_with_enabled_collision:
            # Body names are PrefixedName; use the unprefixed part for matching
            body_name = body.name.name.lower()
            if cls.name_pattern and cls.name_pattern.match(body_name):
                views.append(cls(body=body))
        return views


# Containers and Kitchenware
@dataclass(eq=False)
class Container(HouseholdObject):
    """
    Abstract class for containers.
    """

    pass


@dataclass(eq=False)
class Bottle(Container):
    """
    Abstract class for bottles.
    """

    name_pattern = re.compile(r"^(?:(soap|wine)_)bottle(_volume)?_(\d+)?$")
    rule = MatchRule(required={"bottle"}, forbidden={"soap", "wine"}, base_priority=-10)


@dataclass(eq=False)
class SoapBottle(Bottle):
    """
    A soap bottle.
    """

    name_pattern = re.compile(r"^soap_bottle(_volume)?_(\d+)?$")
    rule = MatchRule(required={"soap", "bottle"}, base_priority=10)


@dataclass(eq=False)
class WineBottle(Bottle):
    """
    A wine bottle.
    """

    name_pattern = re.compile(r"^wine_bottle(_volume)?(_cork)?_(\d+)?$")
    rule = MatchRule(required={"wine", "bottle"}, base_priority=10)


@dataclass(eq=False)
class Cup(Container):
    """
    A cup.
    """

    name_pattern = re.compile(r"^cup(?:_volume)?(?:_\d+)?$")
    rule = MatchRule(required={"cup"})


@dataclass(eq=False)
class Mug(Container):
    """
    A mug.
    """

    name_pattern = re.compile(r"^mug(?:_liquid_volume)?(?:_ai2)?(?:_\d+)?$")
    rule = MatchRule(required={"mug"})


@dataclass(eq=False)
class Pan(HouseholdObject):
    """
    A pan.
    """

    name_pattern = re.compile(r"^pan_(\d+)$")
    rule = MatchRule(required={"pan"})


@dataclass(eq=False)
class PanLid(HouseholdObject):
    """
    A pan lid.
    """

    name_pattern = re.compile(r"^pan_lid_(\d+)$")
    rule = MatchRule(required={"pan", "lid"})


@dataclass(eq=False)
class Pot(HouseholdObject):
    """
    A pot.
    """

    name_pattern = re.compile(r"^pot(?:_liquid_volume)?(?:_volume)?_(\d+)$")
    rule = MatchRule(required={"pot"})


@dataclass(eq=False)
class PotLid(HouseholdObject):
    """
    A pot lid.
    """

    name_pattern = re.compile(r"^pot_lid_(\d+)$")
    rule = MatchRule(required={"pot", "lid"})


@dataclass(eq=False)
class Plate(HouseholdObject):
    """
    A plate.
    """

    name_pattern = re.compile(r"^robothor_plate_ai2$")
    rule = MatchRule(required={"robothor", "plate", "ai2"})


@dataclass(eq=False)
class Bowl(HouseholdObject):
    """
    A bowl.
    """

    name_pattern = re.compile(r"^robothor_bowl_ai2$")
    rule = MatchRule(required={"robothor", "bowl", "ai2"})


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

    name_pattern = re.compile(r"^tomato_[a-z]\d+_(?:slice_\d+|mesh)?$")
    rule = MatchRule(required={"tomato"})


@dataclass(eq=False)
class Lettuce(Produce):
    """
    Lettuce.
    """

    name_pattern = re.compile(r"^lettuce_[a-z]\d+_(?:slice_\d+)?$")
    rule = MatchRule(required={"lettuce"})


@dataclass(eq=False)
class Apple(Produce):
    """
    An apple.
    """

    name_pattern = re.compile(r"^apple(?:_slice)?[ab]\d+$")
    rule = MatchRule(required={"apple"})


@dataclass(eq=False)
class Bread(HouseholdObject):
    """
    Bread.
    """

    name_pattern = re.compile(r"^bread[123]_[abc]_(?:slice_\d+)?_mesh$")
    rule = MatchRule(required={"bread"})


@dataclass(eq=False)
class FriedEgg(HouseholdObject):
    """
    A fried egg.
    """

    name_pattern = re.compile(r"^fried_egg_\d+$")
    rule = MatchRule(required={"fried", "egg"})


# Furniture and Fixtures
@dataclass(eq=False)
class Furniture(HouseholdObject):
    """
    Abstract class for furniture.
    """

    pass


@dataclass(eq=False)
class Table(Furniture):
    """
    Abstract class for tables.
    """

    pass


@dataclass(eq=False)
class CoffeeTable(Table):
    """
    A coffee table.
    """

    name_pattern = re.compile(r"^(?:ps_)?robothor_coffee_table_(\w+)$")
    rule = MatchRule(required={"robothor", "coffee", "table"}, base_priority=10)


@dataclass(eq=False)
class DiningTable(Table):
    """
    A dining table.
    """

    name_pattern = re.compile(r"^robothor_dining_table_(\w+)$")
    rule = MatchRule(required={"robothor", "dining", "table"}, base_priority=10)


@dataclass(eq=False)
class SideTable(Table):
    """
    A side table.
    """

    name_pattern = re.compile(
        r"^(?:ps_)?robothor_side_table_(\w+)(?:_drawer_\d+)?(?:_lid)?$"
    )
    rule = MatchRule(required={"robothor", "side", "table"}, base_priority=10)


@dataclass(eq=False)
class Desk(Table):
    """
    A desk.
    """

    name_pattern = re.compile(
        r"^(?:ps_)?robothor_desk_(?!.*lamp_ai2)(?!.*lamp_)(?!.*lamp$)\w+(?:_drawer_\d+)?$"
    )
    rule = MatchRule(required={"robothor", "desk"}, forbidden={"lamp"})


@dataclass(eq=False)
class Chair(Furniture):
    """
    Abstract class for chairs.
    """

    name_pattern = re.compile(r"^robothor_chair_(\w+)$")
    rule = MatchRule(
        required={"robothor", "chair"},
        forbidden={"office", "armchair"},
        base_priority=-5,
    )


@dataclass(eq=False)
class OfficeChair(Chair):
    """
    An office chair.
    """

    name_pattern = re.compile(r"^robothor_office_chair_(\w+)$")
    rule = MatchRule(required={"robothor", "office", "chair"}, base_priority=10)


@dataclass(eq=False)
class Armchair(Chair):
    """
    An armchair.
    """

    name_pattern = re.compile(r"^robothor_armchair_(\w+)$")
    rule = MatchRule(required={"robothor", "armchair"}, base_priority=10)


@dataclass(eq=False)
class ShelvingUnit(Furniture):
    """
    A shelving unit.
    """

    name_pattern = re.compile(
        r"^(?:ps_)?robothor_shelving_unit_kallax_(\w+)(?:_drawer_\d+)?$"
    )
    rule = MatchRule(required={"robothor", "shelving", "unit", "kallax"})


@dataclass(eq=False)
class Dresser(Furniture):
    """
    A dresser.
    """

    name_pattern = re.compile(
        r"^robothor_dresser_(\w+)(?:_container)?(?:_drawer_\d+)?(?:_handle)?$"
    )
    rule = MatchRule(required={"robothor", "dresser"})


@dataclass(eq=False)
class Bed(Furniture):
    """
    A bed.
    """

    name_pattern = re.compile(
        r"^robothor_bed_(\w+)(?:_day)?(?:_drawer_\d+)?(?:_bedsheet)?(?:_mattress)?$"
    )
    rule = MatchRule(required={"robothor", "bed"})


@dataclass(eq=False)
class Sofa(Furniture):
    """
    A sofa.
    """

    name_pattern = re.compile(r"^robothor_sofa_(\w+)$")
    rule = MatchRule(required={"robothor", "sofa"})


@dataclass(eq=False)
class ToiletPaperHanger(HouseholdObject):
    """
    A toilet paper hanger.
    """

    name_pattern = re.compile(r"^toilet_paper_hanger_(\d+)$")
    rule = MatchRule(required={"toilet", "paper", "hanger"})


@dataclass(eq=False)
class Sink(HouseholdObject):
    """
    A sink.
    """

    name_pattern = re.compile(r"^sink_\d+$")
    rule = MatchRule(required={"sink"}, forbidden={"faucet"})


@dataclass(eq=False)
class SinkFaucet(HouseholdObject):
    """
    A sink faucet.
    """

    name_pattern = re.compile(r"^sink_faucet(?:_l|_r)?_(\d+)?$")
    rule = MatchRule(required={"sink", "faucet"}, forbidden={"knob"}, base_priority=5)


@dataclass(eq=False)
class SinkFaucetKnob(HouseholdObject):
    """
    A sink faucet knob.
    """

    name_pattern = re.compile(r"^sink_faucet_knob(?:_l|_r)?(?:_(\d+))?$")
    rule = MatchRule(required={"sink", "faucet", "knob"}, base_priority=10)


@dataclass(eq=False)
class Faucet(HouseholdObject):
    """
    A standalone faucet.
    """

    name_pattern = re.compile(r"^faucet(?:_tee)?_(\d+)?$")
    rule = MatchRule(required={"faucet"}, forbidden={"sink"})


@dataclass(eq=False)
class LightSwitch(HouseholdObject):
    """
    A light switch.
    """

    name_pattern = re.compile(r"^light_switch_\d+$")


@dataclass(eq=False)
class LightSwitchDial(HouseholdObject):
    """
    A light switch dial.
    """

    name_pattern = re.compile(r"^light_switch_dial(?:_[a-z]+)?_(\d+)$")


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

    name_pattern = re.compile(r"^robothor_(?:desk|floor)_lamp_(\w+)?$")


@dataclass(eq=False)
class Television(Electronics):
    """
    A television.
    """

    name_pattern = re.compile(r"^robothor_television_props_america$")


@dataclass(eq=False)
class Laptop(Electronics):
    """
    A laptop.
    """

    name_pattern = re.compile(r"^robothor_laptop_props_america(?:_lid)?$")


@dataclass(eq=False)
class Cellphone(Electronics):
    """
    A cellphone.
    """

    name_pattern = re.compile(r"^robothor_cellphone_blackberry$")


@dataclass(eq=False)
class AlarmClock(Electronics):
    """
    An alarm clock.
    """

    name_pattern = re.compile(
        r"^alarm_clock(?:_hand_(?:hour|minute|second))?(?:_button)?(?:_\d+)?$"
    )


@dataclass(eq=False)
class Remote(Electronics):
    """
    A remote control.
    """

    name_pattern = re.compile(r"^robothor_remote_coolux$")


# Other objects
@dataclass(eq=False)
class WallDecor(HouseholdObject):
    """
    Wall decorations.
    """

    name_pattern = re.compile(
        r"^robothor_wall_decor(?:_inset)?(?:_poster)?(?:_\d+_\d+)?$"
    )


@dataclass(eq=False)
class WallPanel(HouseholdObject):
    """
    A wall panel.
    """

    name_pattern = re.compile(r"^robothor_wall_panel(?:_\d+_\d+)?(?:_\d+)?$")


@dataclass(eq=False)
class Pillow(HouseholdObject):
    """
    A pillow.
    """

    name_pattern = re.compile(r"^robothor_pillow_(\w+)$")


@dataclass(eq=False)
class GarbageBin(HouseholdObject):
    """
    A garbage bin.
    """

    name_pattern = re.compile(r"^robothor_garbage_bin_ai2_1$")


@dataclass(eq=False)
class Houseplant(HouseholdObject):
    """
    A houseplant.
    """

    name_pattern = re.compile(r"^robothor_houseplant_\d+$")


@dataclass(eq=False)
class SprayBottle(HouseholdObject):
    """
    A spray bottle.
    """

    name_pattern = re.compile(r"^robothor_spray_bottle_kramig$")


@dataclass(eq=False)
class Vase(HouseholdObject):
    """
    A vase.
    """

    name_pattern = re.compile(r"^robothor_vase_stilren$")


@dataclass(eq=False)
class Book(HouseholdObject):
    """
    A book.
    """

    name_pattern = re.compile(r"^robothor_book(?:_front)?_(\d+)$")


@dataclass(eq=False)
class Candle(HouseholdObject):
    """
    A candle.
    """

    name_pattern = re.compile(r"^robothor_candle_glittrig_\d+$")


@dataclass(eq=False)
class SaltPepperShaker(HouseholdObject):
    """
    A salt and pepper shaker.
    """

    name_pattern = re.compile(r"^robothor_salt_pepper_shaker_bnyd$")


@dataclass(eq=False)
class Fork(HouseholdObject):
    """
    A fork.
    """

    name_pattern = re.compile(r"^robothor_fork_ai2_1$")


@dataclass(eq=False)
class ButterKnife(HouseholdObject):
    """
    A butter knife.
    """

    name_pattern = re.compile(r"^robothor_butter_knife_ai2_1$")


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
