from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional

from entity_query_language import symbol
from probabilistic_model.probabilistic_circuit.rx.helper import uniform_measure_of_event
from random_events.interval import SimpleInterval
from typing_extensions import List
from ..datastructures.prefixed_name import PrefixedName
from ..utils import VisualizeTrimesh
from ..world_description.shape_collection import BoundingBoxCollection, ShapeCollection
from ..spatial_types import Point3
from ..datastructures.variables import SpatialVariables
from ..world_description.world_entity import View, Body, Region
import numpy as np


@symbol
@dataclass(eq=False)
class Container(View):
    body: Body


@dataclass(eq=False)
class Fridge(View):
    """
    A view representing a fridge that has a door and a body.
    """

    body: Body
    doors: List[Door] = field(default_factory=list)


@dataclass(eq=False)
class Table(View):
    """
    A view that represents a table.
    """

    body: Body
    """
    The body that represents the table's top surface.
    """

    table_top_surface: Optional[TableTopSurface] = None
    """
    The table's top surface.
    """

    def points_on_table(self, amount: int = 100) -> List[Point3]:
        """
        Get points that are on the table.

        :amount: The number of points to return.
        :returns: A list of points that are on the table.
        """
        area_of_table = BoundingBoxCollection.from_shapes(self.body.collision)
        event = area_of_table.event
        p = uniform_measure_of_event(event)
        p = p.marginal(SpatialVariables.xy)
        samples = p.sample(amount)
        z_coordinate = np.full(
            (amount, 1), max([b.max_z for b in area_of_table]) + 0.01
        )
        samples = np.concatenate((samples, z_coordinate), axis=1)
        return [Point3(*s, reference_frame=self.body) for s in samples]


@dataclass(eq=False)
class Room(View):
    """
    A view that represents a closed area with a specific purpose
    """

    floor: FloorSurface
    """
    The room's floor.
    """


@dataclass(eq=False)
class Wall(View):
    body: Body
    """
    The body that represents the wall.
    """

    doors: List[Door] = field(default_factory=list)
    """
    The doors that are possibly in the wall.
    """


@symbol
@dataclass(eq=False)
class Handle(View):
    body: Body
    """
    The body that the handle is attached to.
    """


################################


@dataclass(eq=False)
class Components(View): ...


@dataclass(eq=False)
class Furniture(View): ...


#################### subclasses von Components


@dataclass(eq=False)
class EntryWay(Components):
    body: Body


@dataclass(eq=False)
class Door(EntryWay):
    handle: Handle


@dataclass(eq=False)
class DoubleDoor(EntryWay):
    doors: List[Door] = field(default_factory=list, hash=False)


@symbol
@dataclass(eq=False)
class Drawer(Components):
    container: Container
    handle: Handle

    @cached_property
    def drawer_surface(self):
        """
        Create a region that represents the drawer's surface.
        """
        mesh = self.container.body.collision.combined_mesh
        upward_threshold = 0.99
        height_tolerance = 0.005
        clearance_threshold = 0.5

        # --- Find upward-facing faces ---
        normals = mesh.face_normals
        upward_mask = normals[:, 2] > upward_threshold

        face_centers = mesh.triangles_center
        z_values = face_centers[:, 2]

        # --- Find the lowest upward-facing surface ---
        if not upward_mask.any():
            raise ValueError("No upward-facing faces found.")

        lowest_surface = np.min(z_values[upward_mask])

        low = lowest_surface - height_tolerance
        high = lowest_surface + height_tolerance
        acceptable_height = SimpleInterval(low, high)

        # Select faces that are both upward and near the lowest surface
        in_tolerance_mask = np.array(
            [acceptable_height.contains(value) for value in z_values]
        )
        candidate_mask = upward_mask & in_tolerance_mask

        if not candidate_mask.any():
            raise ValueError("No upward-facing faces within height tolerance.")

        # --- Check vertical clearance using ray casting ---
        face_centers = face_centers[candidate_mask]
        ray_origins = face_centers + np.array([0, 0, 0.01])  # small upward offset
        ray_dirs = np.tile([0, 0, 1], (len(ray_origins), 1))

        locations, index_ray, _ = mesh.ray.intersects_location(
            ray_origins=ray_origins, ray_directions=ray_dirs
        )

        # Compute distances to intersections (if any)
        distances = np.full(len(ray_origins), np.inf)
        distances[index_ray] = np.linalg.norm(
            locations - ray_origins[index_ray], axis=1
        )

        # Filter faces with enough space above
        clear_mask = (distances > clearance_threshold) | np.isinf(distances)

        # --- Apply clearance mask back to the full mesh ---
        final_mask = np.zeros(len(mesh.faces), dtype=bool)
        candidate_indices = np.nonzero(candidate_mask)[0]
        final_mask[candidate_indices[clear_mask]] = True

        if not final_mask.any():
            raise ValueError("No candidate faces with sufficient clearance found.")

        # --- Build the submesh and region ---
        candidates = mesh.submesh([final_mask], append=True)

        points_3d = [
            Point3(x, y, z, reference_frame=self.container.body)
            for x, y, z in candidates.vertices
        ]

        drawer_surface_region = Region.from_3d_points(
            name=PrefixedName(f"{self.name.name}_surface_region"),
            points_3d=points_3d,
            reference_frame=self.container.body,
        )

        return drawer_surface_region


############################### subclasses to Furniture
@dataclass(eq=False)
class Cupboard(Furniture): ...


@dataclass(eq=False)
class Dresser(Furniture):
    container: Container
    drawers: List[Drawer] = field(default_factory=list, hash=False)
    doors: List[Door] = field(default_factory=list, hash=False)


############################### subclasses to Cupboard
@dataclass(eq=False)
class Cabinet(Cupboard):
    container: Container
    drawers: list[Drawer] = field(default_factory=list, hash=False)


@dataclass(eq=False)
class Wardrobe(Cupboard):
    doors: List[Door] = field(default_factory=list)


############################### supporting surfaces


@dataclass(eq=False)
class SupportingSurface(View):
    """
    A view that represents a supporting surface.
    """

    region: Region
    """
    The region that represents the supporting surface.
    """


@dataclass(eq=False)
class TableTopSurface(SupportingSurface): ...


@dataclass(eq=False)
class SofaSurface(SupportingSurface): ...


@dataclass(eq=False)
class FloorSurface(SupportingSurface): ...


@dataclass(eq=False)
class DrawerSurface(SupportingSurface): ...
