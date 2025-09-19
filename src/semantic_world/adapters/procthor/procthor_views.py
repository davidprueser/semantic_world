from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property

from typing_extensions import List, Self
from typing import ClassVar
import re

from ...world import World

# Reuse the common world/view primitives so ProcTHOR views integrate seamlessly.
from ...world_description.world_entity import View, Body, Region
from ...views.views import (
    Handle,
    Drawer,
    Door,
    Container,
    Furniture,
    SupportingSurface,
    Table,
)


# -----------------------------
# Base categories for household objects
# -----------------------------


@dataclass(eq=False)
class HouseholdObject(View):
    """A very general household object with a single body.

    Each subclass can declare regex patterns in name_pattern to identify whether a
    given prefixed name (from ProcTHOR/RoboTHOR) should be mapped to this view.
    Use HouseholdObject.matches_name(name) to test membership.
    """

    body: Body

    # Class-level regex patterns (strings) for name matching. Subclasses can override.
    name_pattern: ClassVar[tuple[str, ...]] = tuple()
    _compiled_name_pattern: ClassVar[tuple[re.Pattern, ...]] = tuple()

    @classmethod
    def _get_compiled_patterns(cls) -> tuple[re.Pattern, ...]:
        # Lazy-compile for each subclass
        if not cls._compiled_name_pattern:
            cls._compiled_name_pattern = tuple(
                re.compile(p) for p in getattr(cls, "name_pattern", tuple())
            )
        return cls._compiled_name_pattern

    @classmethod
    def matches_name(cls, name: str) -> bool:
        """Return True if the provided name matches any of the class patterns."""
        if not getattr(cls, "name_pattern", tuple()):
            return False
        return any(p.fullmatch(name) is not None for p in cls._get_compiled_patterns())

    @classmethod
    @abstractmethod
    def from_world(cls, world: World) -> Self:
        """
        Creates an instance of the class from a given `world` parameter.

        This abstract method must be implemented by any concrete subclass. It is used
        to generate an object of the class based on the provided `World` instance.

        :param world: The `World` instance used to create the object.
        :return: A class instance created using the `World` instance.
        """
        raise NotImplementedError


@dataclass(eq=False)
class Appliance(HouseholdObject):
    """Large or small powered appliances (e.g., Microwave, Toaster)."""

    ...


@dataclass(eq=False)
class Fixture(HouseholdObject):
    """Fixed home fixtures (e.g., Sink, Faucet, LightSwitch)."""

    ...


@dataclass(eq=False)
class Utensil(HouseholdObject):
    """Hand utensils and tools (e.g., Knife, Spoon, Spatula)."""

    ...


@dataclass(eq=False)
class Cookware(HouseholdObject):
    """Pots, pans, and similar cookware."""

    ...


@dataclass(eq=False)
class Dishware(HouseholdObject):
    """Dishes and drinkware (e.g., Bowl, Plate, Mug)."""

    ...


@dataclass(eq=False)
class ElectronicDevice(HouseholdObject):
    """Consumer electronics (e.g., Television, RemoteControl, Laptop)."""

    ...


@dataclass(eq=False)
class CleaningSupply(HouseholdObject):
    """Cleaning-related objects (e.g., SoapBottle, Sponge)."""

    ...


@dataclass(eq=False)
class Food(HouseholdObject):
    """Edible items (e.g., Apple, Bread, Tomato). Variants map to these base classes."""

    ...


# -----------------------------
# Concrete ProcTHOR-relevant object classes
# (Keep them general. Do not add subclasses for mere variants.)
# -----------------------------


# Fixtures
@dataclass(eq=False)
class Sink(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?sink(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Faucet(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:faucet|sink_faucet)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Knob(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:knob|sink_faucet_knob|light_switch_dial)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class LightSwitch(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?light_switch(?:$|_(?!dial).*)$",
    )
    ...


@dataclass(eq=False)
class Outlet(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?outlet(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Toilet(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?toilet(?!_paper)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Bathtub(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?bathtub(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Shower(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?shower(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Hanger(Fixture):  # e.g., ToiletPaperHanger
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:hanger|toilet_paper_hanger)(?:[_a-z0-9].*)?$",
    )
    ...


# Furniture and supporting surfaces
@dataclass(eq=False)
class Chair(Furniture):
    body: Body
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?chair(?:[_a-z0-9].*)?$",
    )


@dataclass(eq=False)
class Sofa(Furniture):
    body: Body
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?sofa(?:[_a-z0-9].*)?$",)


@dataclass(eq=False)
class Bed(Furniture):
    body: Body
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?bed(?:[_a-z0-9].*)?$",)


@dataclass(eq=False)
class Desk(Furniture):
    top: Body
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?desk(?:[_a-z0-9].*)?$",)


@dataclass(eq=False)
class Shelf(Furniture):
    shelves: List[Body] = field(default_factory=list, hash=False)
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?shelf(?:[_a-z0-9].*)?$",
    )


@dataclass(eq=False)
class Bookshelf(Shelf):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?bookshelf(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class CounterTop(SupportingSurface):
    region: Region
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:countertop|counter_top|counter)(?:[_a-z0-9].*)?$",
    )


# Appliances
@dataclass(eq=False)
class Microwave(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?microwave(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Oven(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?oven(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Stove(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?stove(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class StoveBurner(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:stove_)?burner(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class StoveKnob(Fixture):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?stove_knob(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Toaster(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?toaster(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class CoffeeMachine(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:coffee_machine|coffee_maker)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Blender(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?blender(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Kettle(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:kettle|tea_kettle)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Dishwasher(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?dishwasher(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class WashingMachine(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?washing_machine(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Dryer(Appliance):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?dryer(?:[_a-z0-9].*)?$",
    )
    ...


# Dishware / containers
@dataclass(eq=False)
class Bottle(Dishware):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:bottle|water_bottle|wine_bottle)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Bowl(Dishware):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?bowl(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Plate(Dishware):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?plate(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Cup(Dishware):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:cup|coffee_cup)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Mug(Dishware):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?mug(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Glass(Dishware):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:glass|cup_glass)(?:[_a-z0-9].*)?$",
    )
    ...


# Cookware
@dataclass(eq=False)
class Pot(Cookware):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?pot(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Pan(Cookware):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?pan(?:[_a-z0-9].*)?$",)
    ...


# Utensils / tools
@dataclass(eq=False)
class Knife(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?knife(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Fork(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?fork(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Spoon(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?spoon(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Spatula(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?spatula(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Ladle(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?ladle(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Tongs(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?tongs(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Brush(Utensil):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:brush|scrub_brush)(?:[_a-z0-9].*)?$",
    )
    ...  # e.g., ScrubBrush


# Electronics
@dataclass(eq=False)
class Television(ElectronicDevice):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:television|tv)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class RemoteControl(ElectronicDevice):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:remote|remote_control)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Laptop(ElectronicDevice):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?laptop(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Phone(ElectronicDevice):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:phone|cell_phone|smartphone)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Tablet(ElectronicDevice):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:tablet|ipad)(?:[_a-z0-9].*)?$",
    )
    ...


# Lighting
@dataclass(eq=False)
class Lamp(HouseholdObject):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?lamp(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class FloorLamp(Lamp):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?floor_lamp(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class DeskLamp(Lamp):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?desk_lamp(?:[_a-z0-9].*)?$",
    )
    ...


# Cleaning supplies and disposables
@dataclass(eq=False)
class SoapBottle(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?soap_bottle(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class SoapBar(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?soap_bar(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class SprayBottle(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?spray_bottle(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Sponge(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?sponge(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class TissueBox(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?tissue_box(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class PaperTowelRoll(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?paper_towel_roll(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class ToiletPaper(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?toilet_paper(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class GarbageCan(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:garbage_can|trash_can|waste_bin)(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class GarbageBag(CleaningSupply):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?(?:garbage_bag|trash_bag)(?:[_a-z0-9].*)?$",
    )
    ...


# Decorative and others
@dataclass(eq=False)
class Vase(HouseholdObject):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?vase(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Book(HouseholdObject):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?book(?:[_a-z0-9].*)?$",)
    ...


# Food examples (keep generic; variants map to these base classes)
@dataclass(eq=False)
class Apple(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?apple(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Banana(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?banana(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Bread(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?bread(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Tomato(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?tomato(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Potato(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?potato(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Carrot(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?carrot(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Onion(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?onion(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Garlic(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?garlic(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Lettuce(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?lettuce(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Egg(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?egg(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Cheese(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?cheese(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Butter(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?butter(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Milk(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?milk(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Sugar(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?sugar(?:[_a-z0-9].*)?$",
    )
    ...


@dataclass(eq=False)
class Salt(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (r"^(?:robothor_)?salt(?:[_a-z0-9].*)?$",)
    ...


@dataclass(eq=False)
class Pepper(Food):
    name_pattern: ClassVar[tuple[str, ...]] = (
        r"^(?:robothor_)?pepper(?:[_a-z0-9].*)?$",
    )
    ...


# -----------------------------
# Simple aliases for variant-heavy ProcTHOR names
# (No extra subclasses; just point variants to a general class.)
# -----------------------------

# Fixtures
LightSwitchDial = Knob  # e.g., light_switch_dial_X
FaucetKnob = Knob  # e.g., sink_faucet_knob_*

# Containers/bottles
WineBottle = Bottle  # e.g., wine_bottle_*

# Cleaning / bottles
DishSoap = SoapBottle  # generic alias if used

# Tomato slices and similar processed variants
TomatoSlice = Tomato
AppleSlice = Apple
BreadSlice = Bread

# Scrub brush naming
ScrubBrush = Brush

# Some common alternate names
CupGlass = Glass
CoffeeMaker = CoffeeMachine
TeaKettle = Kettle
