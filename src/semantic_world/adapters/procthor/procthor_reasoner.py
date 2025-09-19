# -------------------------------
# Queries that build ProcTHOR views from bodies by name
# -------------------------------
import re
from typing import Dict

from semantic_world.datastructures.prefixed_name import PrefixedName
from semantic_world.world import World
from semantic_world.world_description.world_entity import Body

from .procthor_views import *


def _find_bodies(world: World, pattern: str) -> List[Body]:
    """
    Helper: return all bodies whose unprefixed name matches the regex pattern.
    """
    rx = re.compile(pattern)
    return [b for b in world.bodies if rx.fullmatch(b.name.name)]


def _find_body(world: World, name: str) -> Optional[Body]:
    """
    Helper: get a body by exact unprefixed name (no regex).
    """
    for b in world.bodies:
        if b.name.name == name:
            return b
    return None


def _group_by_index(bodies: List[Body], suffix_pattern: str) -> Dict[str, Body]:
    """
    Helper: map index string (captured group 'idx') to body for bodies whose name matches the provided
    suffix_pattern regex with a named group (?P<idx>...).
    """
    rx = re.compile(suffix_pattern)
    out: Dict[str, Body] = {}
    for b in bodies:
        m = rx.fullmatch(b.name.name)
        if m:
            out[m.group("idx")] = b
    return out


def _add_view(world: World, view: View) -> None:
    """
    Add view to world with exists_ok=True.
    """
    world.add_view(view, exists_ok=True)


def build_procthor_views(world: World) -> None:
    """
    Scan world.bodies and create ProcTHOR-specific views by name conventions.

    Rules are based on the provided name lists. Each rule:
    - finds relevant bodies by regex
    - associates related parts by shared numeric indices
    - creates the corresponding View instances
    - adds them to world via world.add_view(..., exists_ok=True)
    """

    # 1) Soap bottles with volume
    # Names like: soap_bottle_1, soap_bottle_volume_1
    bottles = _group_by_index(
        _find_bodies(world, r"soap_bottle_\d+"), r"soap_bottle_(?P<idx>\d+)"
    )
    bottle_vols = _group_by_index(
        _find_bodies(world, r"soap_bottle_volume_\d+"),
        r"soap_bottle_volume_(?P<idx>\d+)",
    )
    for idx, body in bottles.items():
        vol = (
            Volume(name=PrefixedName(f"soap_bottle_volume_{idx}"))
            if idx in bottle_vols
            else None
        )
        _add_view(world, SoapBottle(name=body.name, body=body, volume=vol))

    # 2) Bowls with volume
    bowls = _group_by_index(_find_bodies(world, r"bowl_\d+"), r"bowl_(?P<idx>\d+)")
    bowl_vols = _group_by_index(
        _find_bodies(world, r"bowl_volume_\d+"), r"bowl_volume_(?P<idx>\d+)"
    )
    for idx, body in bowls.items():
        vol = (
            Volume(name=PrefixedName(f"bowl_volume_{idx}"))
            if idx in bowl_vols
            else None
        )
        _add_view(world, Bowl(name=body.name, body=body, volume=vol))

    # 3) Cups with volume
    cups = _group_by_index(_find_bodies(world, r"cup_\d+"), r"cup_(?P<idx>\d+)")
    cup_vols = _group_by_index(
        _find_bodies(world, r"cup_volume_\d+"), r"cup_volume_(?P<idx>\d+)"
    )
    for idx, body in cups.items():
        vol = (
            Volume(name=PrefixedName(f"cup_volume_{idx}")) if idx in cup_vols else None
        )
        _add_view(world, Cup(name=body.name, body=body, volume=vol))

    # 4) Mugs with liquid_volume
    mugs = _group_by_index(_find_bodies(world, r"mug_\d+"), r"mug_(?P<idx>\d+)")
    mug_liqs = _group_by_index(
        _find_bodies(world, r"mug_liquid_volume_\d+"), r"mug_liquid_volume_(?P<idx>\d+)"
    )
    for idx, body in mugs.items():
        lvol = (
            Volume(name=PrefixedName(f"mug_liquid_volume_{idx}"))
            if idx in mug_liqs
            else None
        )
        _add_view(world, Mug(name=body.name, body=body, liquid_volume=lvol))

    # 5) Kettles with volume and lid
    kettles = _group_by_index(
        _find_bodies(world, r"kettle_\d+"), r"kettle_(?P<idx>\d+)"
    )
    kettle_vols = _group_by_index(
        _find_bodies(world, r"kettle_volume_\d+"), r"kettle_volume_(?P<idx>\d+)"
    )
    kettle_lids = _group_by_index(
        _find_bodies(world, r"kettle_lid_\d+"), r"kettle_lid_(?P<idx>\d+)"
    )
    for idx, body in kettles.items():
        vol = (
            Volume(name=PrefixedName(f"kettle_volume_{idx}"))
            if idx in kettle_vols
            else None
        )
        lid_body = kettle_lids.get(idx)
        lid_view = View(name=lid_body.name, body=lid_body) if lid_body else None
        _add_view(world, Kettle(name=body.name, body=body, volume=vol, lid=lid_view))

    # 6) Pans with lids
    pans = _group_by_index(_find_bodies(world, r"pan_\d+"), r"pan_(?P<idx>\d+)")
    pan_lids = _group_by_index(
        _find_bodies(world, r"pan_lid_\d+"), r"pan_lid_(?P<idx>\d+)"
    )
    for idx, body in pans.items():
        lids: List[PanLid] = []
        if idx in pan_lids:
            lid_b = pan_lids[idx]
            lids.append(PanLid(name=lid_b.name))
        _add_view(world, Pan(name=body.name, body=body, lids=lids))

    # 7) Pots with lids and optional volumes
    pots = _group_by_index(_find_bodies(world, r"pot_\d+"), r"pot_(?P<idx>\d+)")
    pot_lids = _group_by_index(
        _find_bodies(world, r"pot_lid_\d+"), r"pot_lid_(?P<idx>\d+)"
    )
    pot_vols = _group_by_index(
        _find_bodies(world, r"pot_volume_\d+"), r"pot_volume_(?P<idx>\d+)"
    )
    pot_liqs = _group_by_index(
        _find_bodies(world, r"pot_liquid_volume_\d+"), r"pot_liquid_volume_(?P<idx>\d+)"
    )
    for idx, body in pots.items():
        lids: List[PotLid] = []
        if idx in pot_lids:
            lids.append(PotLid(name=pot_lids[idx].name))
        vol = (
            Volume(name=PrefixedName(f"pot_volume_{idx}")) if idx in pot_vols else None
        )
        lvol = (
            Volume(name=PrefixedName(f"pot_liquid_volume_{idx}"))
            if idx in pot_liqs
            else None
        )
        _add_view(
            world,
            Pot(name=body.name, body=body, lids=lids, volume=vol, liquid_volume=lvol),
        )

    # 8) Plates
    for body in _find_bodies(world, r"plate_\d+"):
        _add_view(world, Plate(name=body.name, body=body))

    # 9) Toaster with levers
    # Supports toaster_lever_N and toaster_lever1_N / toaster_lever2_N
    toasters = _group_by_index(
        _find_bodies(world, r"toaster_\d+"), r"toaster_(?P<idx>\d+)"
    )
    lever_a = _group_by_index(
        _find_bodies(world, r"toaster_lever_\d+"), r"toaster_lever_(?P<idx>\d+)"
    )
    lever1 = _group_by_index(
        _find_bodies(world, r"toaster_lever1_\d+"), r"toaster_lever1_(?P<idx>\d+)"
    )
    lever2 = _group_by_index(
        _find_bodies(world, r"toaster_lever2_\d+"), r"toaster_lever2_(?P<idx>\d+)"
    )
    for idx, body in toasters.items():
        levers: List[ToasterLever] = []
        for src in (lever_a, lever1, lever2):
            if idx in src:
                levers.append(ToasterLever(name=src[idx].name, body=src[idx]))
        _add_view(world, Toaster(name=body.name, body=body, levers=levers))

    # 10) Eggs with shells
    eggs = _group_by_index(_find_bodies(world, r"egg_\d+"), r"egg_(?P<idx>\d+)")
    shells_by_idx: Dict[str, List[Body]] = {}
    for b in _find_bodies(world, r"egg_\d+_shell_\d+"):
        m = re.fullmatch(r"egg_(?P<idx>\d+)_shell_\d+", b.name.name)
        if m:
            shells_by_idx.setdefault(m.group("idx"), []).append(b)
    for idx, body in eggs.items():
        shells = [EggShell(name=s.name, body=s) for s in shells_by_idx.get(idx, [])]
        _add_view(world, Egg(name=body.name, body=body, shells=shells))

    # 11) Tomatoes with slices and mesh
    # tomato_[a-c]\d+_slice_\d+ and tomato_[a-c]\d+_mesh
    tomatoes = {}
    for b in world.bodies:
        if re.fullmatch(r"tomato_[abc]\d+", b.name.name):
            tomatoes[b.name.name] = b
    tomato_slices: Dict[str, List[Body]] = {}
    tomato_mesh: Dict[str, Body] = {}
    for b in world.bodies:
        m = re.fullmatch(r"(tomato_[abc]\d+)_slice_\d+", b.name.name)
        if m:
            tomato_slices.setdefault(m.group(1), []).append(b)
        m2 = re.fullmatch(r"(tomato_[abc]\d+)_mesh", b.name.name)
        if m2:
            tomato_mesh[m2.group(1)] = b
    for key, body in tomatoes.items():
        slices = [
            Slice(name=s.name, body=s)
            for s in sorted(tomato_slices.get(key, []), key=lambda x: x.name.name)
        ]
        mesh_view = (
            Mesh(name=tomato_mesh[key].name, body=tomato_mesh[key])
            if key in tomato_mesh
            else None
        )
        _add_view(
            world, Tomato(name=body.name, body=body, slices=slices, mesh=mesh_view)
        )

    # 12) Lettuce (grouped similarly by families a/b/c; treat base body + its slices)
    lettuce_bases: Dict[str, Body] = {}
    lettuce_slices: Dict[str, List[Body]] = {}
    for b in world.bodies:
        if re.fullmatch(r"lettuce_[abc]\d+", b.name.name):
            lettuce_bases[b.name.name] = b
        m = re.fullmatch(r"(lettuce_[abc]\d+)_slice_\d+", b.name.name)
        if m:
            lettuce_slices.setdefault(m.group(1), []).append(b)
    for key, body in lettuce_bases.items():
        slices = [
            Slice(name=s.name, body=s)
            for s in sorted(lettuce_slices.get(key, []), key=lambda x: x.name.name)
        ]
        _add_view(world, Lettuce(name=body.name, body=body, slices=slices))

    # 13) Potatoes
    potatoes: Dict[str, Body] = {}
    potato_slices: Dict[str, List[Body]] = {}
    for b in world.bodies:
        if re.fullmatch(r"potato_[abc]\d+", b.name.name):
            potatoes[b.name.name] = b
        m = re.fullmatch(r"(potato_[abc]\d+)_slice_\d+", b.name.name)
        if m:
            potato_slices.setdefault(m.group(1), []).append(b)
    for key, body in potatoes.items():
        slices = [
            Slice(name=s.name, body=s)
            for s in sorted(potato_slices.get(key, []), key=lambda x: x.name.name)
        ]
        _add_view(world, Potato(name=body.name, body=body, slices=slices))

    # 14) Sinks with faucets and knobs
    # Patterns include various variants such as:
    # - sink_1
    # - sink_faucet_1 / sink_faucet_l_6 / sink_faucet_r_6
    # - sink_faucet_knob_1 or sink_faucet_knob_l_# / sink_faucet_knob_r_#
    sinks = _group_by_index(_find_bodies(world, r"sink_\d+"), r"sink_(?P<idx>\d+)")
    # Faucet variants keyed by idx
    faucet_any = {}
    for b in world.bodies:
        for pat in [r"sink_faucet_(?P<idx>\d+)", r"sink_faucet_[lr]_(?P<idx>\d+)"]:
            m = re.fullmatch(pat, b.name.name)
            if m:
                faucet_any.setdefault(m.group("idx"), []).append(b)
    # Knob variants keyed by idx
    knobs_by_idx: Dict[str, List[FaucetKnob]] = {}
    for b in world.bodies:
        m = re.fullmatch(r"sink_faucet_knob_(?P<idx>\d+)", b.name.name)
        if m:
            knobs_by_idx.setdefault(m.group("idx"), []).append(
                FaucetKnob(name=b.name, body=b)
            )
        m = re.fullmatch(r"sink_faucet_knob_(?P<side>[lr])_(?P<idx>\d+)", b.name.name)
        if m:
            knobs_by_idx.setdefault(m.group("idx"), []).append(
                FaucetKnob(
                    name=b.name,
                    body=b,
                    side=("left" if m.group("side") == "l" else "right"),
                )
            )
        m = re.fullmatch(
            r"sink_faucet_[lr]_knob_(?P<side>[lr])_(?P<idx>\d+)", b.name.name
        )
        if m:
            knobs_by_idx.setdefault(m.group("idx"), []).append(
                FaucetKnob(
                    name=b.name,
                    body=b,
                    side=("left" if m.group("side") == "l" else "right"),
                )
            )
    for idx, body in sinks.items():
        f_bodies = faucet_any.get(idx, [])
        faucet_view = None
        if f_bodies:
            faucet_view = Faucet(
                name=f_bodies[0].name,
                body=f_bodies[0],
                knobs=sorted(knobs_by_idx.get(idx, []), key=lambda k: k.name.name),
            )
            _add_view(world, faucet_view)
        _add_view(world, Sink(name=body.name, body=body, faucet=faucet_view))

    # 15) Light switches with dials
    switches = _group_by_index(
        _find_bodies(world, r"light_switch_\d+"), r"light_switch_(?P<idx>\d+)"
    )
    dials_by_idx: Dict[str, List[LightSwitchDial]] = {}
    for b in world.bodies:
        m = re.fullmatch(r"light_switch_dial_(?P<idx>\d+)", b.name.name)
        if m:
            dials_by_idx.setdefault(m.group("idx"), []).append(
                LightSwitchDial(name=b.name, body=b)
            )
        m = re.fullmatch(
            r"light_switch_dial_(?P<variant>[a-d]{1,2}|[ab]{2})_(?P<idx>\d+)",
            b.name.name,
        )
        if m:
            dials_by_idx.setdefault(m.group("idx"), []).append(
                LightSwitchDial(name=b.name, body=b, variant=m.group("variant"))
            )
    for idx, body in switches.items():
        dials = sorted(dials_by_idx.get(idx, []), key=lambda d: d.name.name)
        _add_view(world, LightSwitch(name=body.name, body=body, dials=dials))

    # 16) Toilet paper hanger
    for body in _find_bodies(world, r"toilet_paper_hanger_\d+"):
        _add_view(world, ToiletPaperHanger(name=body.name, body=body))

    # 17) Simple refrigerators (ruifridge_* set)
    # ruifridge_body, ruifridge_maindoor, ruifridge_freezerdoor, ruifridge_drawer1, ruifridge_drawer2
    ruibody = _find_body(world, "ruifridge_body")
    if ruibody:
        main_door = _find_body(world, "ruifridge_maindoor")
        freezer_door = _find_body(world, "ruifridge_freezerdoor")
        drawers = [
            b for b in world.bodies if re.fullmatch(r"ruifridge_drawer\d+", b.name.name)
        ]
        _add_view(
            world,
            Refrigerator(
                name=ruibody.name,
                body=ruibody,
                main_door=(
                    View(name=main_door.name, body=main_door) if main_door else None
                ),
                freezer_door=(
                    View(name=freezer_door.name, body=freezer_door)
                    if freezer_door
                    else None
                ),
                drawers=[
                    View(name=d.name, body=d)
                    for d in sorted(drawers, key=lambda x: x.name.name)
                ],
            ),
        )

    # 18) Drone (drone_body, drone_box)
    drone_body = _find_body(world, "drone_body")
    drone_box = _find_body(world, "drone_box")
    if drone_body:
        _add_view(
            world,
            Drone(
                name=drone_body.name,
                body=drone_body,
                box=View(name=drone_box.name, body=drone_box) if drone_box else None,
            ),
        )

    # 19) Simple bottles (generic bottle_1 + bottle_volume_1 + optional liquid caps)
    bottles_generic = _group_by_index(
        _find_bodies(world, r"bottle_\d+"), r"bottle_(?P<idx>\d+)"
    )
    bottles_generic_vol = _group_by_index(
        _find_bodies(world, r"bottle_volume_\d+"), r"bottle_volume_(?P<idx>\d+)"
    )
    for idx, body in bottles_generic.items():
        vol = (
            Volume(name=PrefixedName(f"bottle_volume_{idx}"))
            if idx in bottles_generic_vol
            else None
        )
        _add_view(world, Bottle(name=body.name, body=body, volume=vol))

    # 20) Wine bottles with cork and volume (wine_bottle_1, wine_bottle_volume_1, wine_bottle_cork_1)
    wine_bottles = _group_by_index(
        _find_bodies(world, r"wine_bottle_\d+"), r"wine_bottle_(?P<idx>\d+)"
    )
    wine_vols = _group_by_index(
        _find_bodies(world, r"wine_bottle_volume_\d+"),
        r"wine_bottle_volume_(?P<idx>\d+)",
    )
    wine_corks = _group_by_index(
        _find_bodies(world, r"wine_bottle_cork_\d+"), r"wine_bottle_cork_(?P<idx>\d+)"
    )
    for idx, body in wine_bottles.items():
        vol = (
            Volume(name=PrefixedName(f"wine_bottle_volume_{idx}"))
            if idx in wine_vols
            else None
        )
        cork_body = wine_corks.get(idx)
        cork_view = View(name=cork_body.name, body=cork_body) if cork_body else None
        _add_view(
            world, WineBottle(name=body.name, body=body, volume=vol, cork=cork_view)
        )
