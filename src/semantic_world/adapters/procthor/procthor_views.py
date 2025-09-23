from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from functools import cached_property

from typing_extensions import List, Self
from typing import ClassVar, Optional
import re


from ...world import World

# Reuse the common world/view primitives so ProcTHOR views integrate seamlessly.
from ...world_description.world_entity import View, Body, Region
import re
from abc import ABC
from dataclasses import dataclass


@dataclass(eq=False)
class HouseholdObject(View, ABC):
    """
    Abstract base class for all household objects. Each view refers to a single Body.
    """

    body: Body
    name_pattern: ClassVar[Optional[re.Pattern]] = field(init=False, default=None)

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


@dataclass(eq=False)
class SoapBottle(Bottle):
    """
    A soap bottle.
    """

    name_pattern = re.compile(r"^soap_bottle(_volume)?_(\d+)?$")


@dataclass(eq=False)
class WineBottle(Bottle):
    """
    A wine bottle.
    """

    name_pattern = re.compile(r"^wine_bottle(_volume)?(_cork)?_(\d+)?$")


@dataclass(eq=False)
class Cup(Container):
    """
    A cup.
    """

    name_pattern = re.compile(r"^cup(?:_volume)?(?:_\d+)?$")


@dataclass(eq=False)
class Mug(Container):
    """
    A mug.
    """

    name_pattern = re.compile(r"^mug(?:_liquid_volume)?(?:_ai2)?(?:_\d+)?$")


@dataclass(eq=False)
class Pan(HouseholdObject):
    """
    A pan.
    """

    name_pattern = re.compile(r"^pan_(\d+)$")


@dataclass(eq=False)
class PanLid(HouseholdObject):
    """
    A pan lid.
    """

    name_pattern = re.compile(r"^pan_lid_(\d+)$")


@dataclass(eq=False)
class Pot(HouseholdObject):
    """
    A pot.
    """

    name_pattern = re.compile(r"^pot(?:_liquid_volume)?(?:_volume)?_(\d+)$")


@dataclass(eq=False)
class PotLid(HouseholdObject):
    """
    A pot lid.
    """

    name_pattern = re.compile(r"^pot_lid_(\d+)$")


@dataclass(eq=False)
class Plate(HouseholdObject):
    """
    A plate.
    """

    name_pattern = re.compile(r"^robothor_plate_ai2$")


@dataclass(eq=False)
class Bowl(HouseholdObject):
    """
    A bowl.
    """

    name_pattern = re.compile(r"^robothor_bowl_ai2$")


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


@dataclass(eq=False)
class Lettuce(Produce):
    """
    Lettuce.
    """

    name_pattern = re.compile(r"^lettuce_[a-z]\d+_(?:slice_\d+)?$")


@dataclass(eq=False)
class Apple(Produce):
    """
    An apple.
    """

    name_pattern = re.compile(r"^apple(?:_slice)?[ab]\d+$")


@dataclass(eq=False)
class Bread(HouseholdObject):
    """
    Bread.
    """

    name_pattern = re.compile(r"^bread[123]_[abc]_(?:slice_\d+)?_mesh$")


@dataclass(eq=False)
class FriedEgg(HouseholdObject):
    """
    A fried egg.
    """

    name_pattern = re.compile(r"^fried_egg_\d+$")


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


@dataclass(eq=False)
class DiningTable(Table):
    """
    A dining table.
    """

    name_pattern = re.compile(r"^robothor_dining_table_(\w+)$")


@dataclass(eq=False)
class SideTable(Table):
    """
    A side table.
    """

    name_pattern = re.compile(
        r"^(?:ps_)?robothor_side_table_(\w+)(?:_drawer_\d+)?(?:_lid)?$"
    )


@dataclass(eq=False)
class Desk(Table):
    """
    A desk.
    """

    name_pattern = re.compile(r"^(?:ps_)?robothor_desk_(\w+)(?:_drawer_\d+)?$")


@dataclass(eq=False)
class Chair(Furniture):
    """
    Abstract class for chairs.
    """

    name_pattern = re.compile(r"^robothor_chair_(\w+)$")


@dataclass(eq=False)
class OfficeChair(Chair):
    """
    An office chair.
    """

    name_pattern = re.compile(r"^robothor_office_chair_(\w+)$")


@dataclass(eq=False)
class Armchair(Chair):
    """
    An armchair.
    """

    name_pattern = re.compile(r"^robothor_armchair_(\w+)$")


@dataclass(eq=False)
class ShelvingUnit(Furniture):
    """
    A shelving unit.
    """

    name_pattern = re.compile(
        r"^(?:ps_)?robothor_shelving_unit_kallax_(\w+)(?:_drawer_\d+)?$"
    )


@dataclass(eq=False)
class Dresser(Furniture):
    """
    A dresser.
    """

    name_pattern = re.compile(
        r"^robothor_dresser_(\w+)(?:_container)?(?:_drawer_\d+)?(?:_handle)?$"
    )


@dataclass(eq=False)
class Bed(Furniture):
    """
    A bed.
    """

    name_pattern = re.compile(
        r"^robothor_bed_(\w+)(?:_day)?(?:_drawer_\d+)?(?:_bedsheet)?(?:_mattress)?$"
    )


@dataclass(eq=False)
class Sofa(Furniture):
    """
    A sofa.
    """

    name_pattern = re.compile(r"^robothor_sofa_(\w+)$")


@dataclass(eq=False)
class ToiletPaperHanger(HouseholdObject):
    """
    A toilet paper hanger.
    """

    name_pattern = re.compile(r"^toilet_paper_hanger_(\d+)$")


@dataclass(eq=False)
class Sink(HouseholdObject):
    """
    A sink.
    """

    name_pattern = re.compile(r"^sink_\d+$")


@dataclass(eq=False)
class SinkFaucet(HouseholdObject):
    """
    A sink faucet.
    """

    name_pattern = re.compile(r"^sink_faucet(?:_l|_r)?_(\d+)?$")


@dataclass(eq=False)
class SinkFaucetKnob(HouseholdObject):
    """
    A sink faucet knob.
    """

    name_pattern = re.compile(r"^sink_faucet_knob(?:_l|_r)?(?:_(\d+))?$")


@dataclass(eq=False)
class Faucet(HouseholdObject):
    """
    A standalone faucet.
    """

    name_pattern = re.compile(r"^faucet(?:_tee)?_(\d+)?$")


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
