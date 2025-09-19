from dataclasses import dataclass, field
from typing import List, Optional

from semantic_world.world_description.world_entity import View
# Reuse existing core views where applicable
from semantic_world.views.views import (
    Container as BaseContainer,
    Handle as BaseHandle,
    Drawer as BaseDrawer,
    Dresser as BaseDresser,
    Table as BaseTable,
)

# -------------------------------
# Base classes
# -------------------------------
# Removed duplicate local View definition to avoid shadowing the imported View.
# The imported View provides custom hash/equality semantics; subclasses should use eq=False.

# -------------------------------
# Fixtures
# -------------------------------
@dataclass(eq=False)
class FaucetKnob(View):
    side: Optional[str] = None  # left / right

@dataclass(eq=False)
class Faucet(View):
    knobs: List[FaucetKnob] = field(default_factory=list)

@dataclass(eq=False)
class Sink(View):
    faucet: Optional[Faucet] = None

@dataclass(eq=False)
class LightSwitchDial(View):
    variant: Optional[str] = None  # a/b/c/d

@dataclass(eq=False)
class LightSwitch(View):
    dials: List[LightSwitchDial] = field(default_factory=list)

@dataclass(eq=False)
class ToiletPaperHanger(View):
    pass

# -------------------------------
# Containers
# -------------------------------
# Extracted common container superclass to avoid duplication of volume/liquid_volume fields.
# Refactor: Reuse core Container, add only additional optional fields here.
@dataclass(eq=False)
class Container(BaseContainer):
    volume: Optional["Volume"] = None
    liquid_volume: Optional["Volume"] = None

@dataclass(eq=False)
class Volume(View):
    capacity: Optional[float] = None  # could be ml

@dataclass(eq=False)
class Cap(View):
    shape: Optional[str] = None  # square / circle

@dataclass(eq=False)
class Bottle(Container):
    cap: Optional[Cap] = None
    # volume and (optional) liquid_volume inherited from Container

@dataclass(eq=False)
class SoapBottle(Bottle):
    pass

@dataclass(eq=False)
class WineBottle(Bottle):
    cork: Optional[View] = None

@dataclass(eq=False)
class Cup(Container):
    # uses 'volume' from Container
    pass

@dataclass(eq=False)
class Mug(Container):
    # typically uses 'liquid_volume' from Container
    pass

@dataclass(eq=False)
class Bowl(Container):
    # uses 'volume' from Container
    pass

@dataclass(eq=False)
class Plate(View):
    pass

@dataclass(eq=False)
class Pot(Container):
    lids: List["PotLid"] = field(default_factory=list)

# Extracted a common Lid superclass to unify lid-like entities.
@dataclass(eq=False)
class Lid(View):
    pass

@dataclass(eq=False)
class PotLid(Lid):
    pass

@dataclass(eq=False)
class Pan(View):
    lids: List["PanLid"] = field(default_factory=list)

@dataclass(eq=False)
class PanLid(Lid):
    pass

# -------------------------------
# Appliances
# -------------------------------
@dataclass(eq=False)
class OvenDrawer(View): pass
@dataclass(eq=False)
class OvenDoor(View): pass
@dataclass(eq=False)
class Oven(View):
    drawer: Optional[OvenDrawer] = None
    door: Optional[OvenDoor] = None

@dataclass(eq=False)
class ToasterLever(View): pass
@dataclass(eq=False)
class Toaster(View):
    levers: List[ToasterLever] = field(default_factory=list)

@dataclass(eq=False)
class Kettle(Container):
    # uses 'volume' and optionally 'liquid_volume' from Container
    lid: Optional[View] = None

@dataclass(eq=False)
class Refrigerator(View):
    body: Optional[View] = None
    main_door: Optional[View] = None
    freezer_door: Optional[View] = None
    drawers: List[View] = field(default_factory=list)

# -------------------------------
# Food
# -------------------------------
@dataclass(eq=False)
class Slice(View): pass
@dataclass(eq=False)
class Mesh(View): pass

@dataclass(eq=False)
class Fruit(View):
    slices: List[Slice] = field(default_factory=list)
    mesh: Optional[Mesh] = None

@dataclass(eq=False)
class Apple(Fruit): pass
@dataclass(eq=False)
class Tomato(Fruit): pass

@dataclass(eq=False)
class Vegetable(View):
    slices: List[Slice] = field(default_factory=list)

@dataclass(eq=False)
class Lettuce(Vegetable): pass
@dataclass(eq=False)
class Potato(Vegetable): pass

@dataclass(eq=False)
class EggShell(View): pass
@dataclass(eq=False)
class Egg(View):
    shells: List[EggShell] = field(default_factory=list)

@dataclass(eq=False)
class FriedEgg(Egg): pass
@dataclass(eq=False)
class Omelette(Egg): pass

@dataclass(eq=False)
class BreadSlice(View): pass
@dataclass(eq=False)
class Bread(View):
    slices: List[BreadSlice] = field(default_factory=list)

@dataclass(eq=False)
class WhiteBread(Bread): pass
@dataclass(eq=False)
class GrainBread(Bread): pass
@dataclass(eq=False)
class HoneyBread(Bread): pass
@dataclass(eq=False)
class LoafBread(Bread): pass
@dataclass(eq=False)
class BumpyBread(Bread): pass

# -------------------------------
# Furniture
# -------------------------------
# Refactor: Reuse core Handle/Drawer/Dresser types for compatibility with the rest of the system.
# They inherit core semantics (e.g., required fields) while keeping local type names.
# ... existing code ...
@dataclass(eq=False)
class Handle(BaseHandle):
    pass

@dataclass(eq=False)
class Drawer(BaseDrawer):
    pass

@dataclass(eq=False)
class Dresser(BaseDresser):
    # Optionally keep handles list if used elsewhere; not required by the base Dresser.
    handles: List[Handle] = field(default_factory=list)
# ... existing code ...

@dataclass(eq=False)
class Bed(View):
    mattress: Optional[View] = None
    bedsheet: Optional[View] = None
    drawers: List[Drawer] = field(default_factory=list)

# Refactor: Reuse core Table for specializations to avoid redefining it.
# Subclasses still require a valid 'top' Body when instantiated, as per the core Table API.
@dataclass(eq=False)
class Table(BaseTable): pass
@dataclass(eq=False)
class CoffeeTable(Table): pass
@dataclass(eq=False)
class DiningTable(Table): pass
@dataclass(eq=False)
class SideTable(Table): pass
@dataclass(eq=False)
class Desk(Table): pass

@dataclass(eq=False)
class Seating(View): pass
@dataclass(eq=False)
class Chair(Seating): pass
@dataclass(eq=False)
class Armchair(Seating): pass
@dataclass(eq=False)
class Sofa(Seating): pass
@dataclass(eq=False)
class OfficeChair(Seating): pass
@dataclass(eq=False)
class Ottoman(Seating): pass

@dataclass(eq=False)
class ShelvingUnit(View): pass
@dataclass(eq=False)
class TVStand(View): pass
@dataclass(eq=False)
class WallPanel(View): pass
@dataclass(eq=False)
class WallDecor(View): pass

# -------------------------------
# Accessories
# -------------------------------
@dataclass(eq=False)
class Book(View): pass
@dataclass(eq=False)
class Poster(View): pass
@dataclass(eq=False)
class Pen(View): pass
@dataclass(eq=False)
class Candle(View): pass
@dataclass(eq=False)
class Knife(View): pass
@dataclass(eq=False)
class Fork(View): pass
@dataclass(eq=False)
class Racquet(View): pass
@dataclass(eq=False)
class Laptop(View): pass
@dataclass(eq=False)
class Remote(View): pass
@dataclass(eq=False)
class Vase(View): pass
@dataclass(eq=False)
class AlarmClock(View): pass
@dataclass(eq=False)
class Lamp(View): pass
@dataclass(eq=False)
class HousePlant(View): pass

# -------------------------------
# Misc
# -------------------------------
@dataclass(eq=False)
class Drone(View):
    body: Optional[View] = None
    box: Optional[View] = None

@dataclass(eq=False)
class Prop(View): pass