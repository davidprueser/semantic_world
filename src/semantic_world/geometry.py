from __future__ import annotations

import itertools
import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional, List, Iterator, TYPE_CHECKING

import numpy as np
from numpy import ndarray
from trimesh import Trimesh
from typing_extensions import Self

import trimesh
from random_events.interval import SimpleInterval, Bound
from random_events.product_algebra import SimpleEvent, Event

from .prefixed_name import PrefixedName
from .spatial_types import TransformationMatrix, Point3
from .spatial_types.spatial_types import Expression
from .types import NpMatrix4x4
from .utils import IDGenerator
from .variables import SpatialVariables
import trimesh.exchange.stl

if TYPE_CHECKING:
    from .world_entity import Body

id_generator = IDGenerator()

@dataclass
class Color:
    """
    Dataclass for storing rgba_color as an RGBA value.
    The values are stored as floats between 0 and 1.
    The default rgba_color is white.
    """
    R: float = 1
    """
    Red value of the color.
    """

    G: float = 1
    """
    Green value of the color.
    """

    B: float = 1
    """
    Blue value of the color.
    """

    A: float = 1
    """
    Opacity of the color.
    """

@dataclass
class Scale:
    """
    Dataclass for storing the scale of geometric objects.
    """

    x: float = 1.
    """
    The scale in the x direction.
    """

    y: float = 1.
    """
    The scale in the y direction.
    """

    z: float = 1.
    """
    The scale in the z direction.
    """

@dataclass
class Shape(ABC):
    """
    Base class for all shapes in the world.
    """
    origin: TransformationMatrix = field(default_factory=TransformationMatrix)

    def as_bounding_box(self, reference_frame: Optional[Body]) -> BoundingBox:
        """
        Returns the bounding box of the box.
        """

        origin_frame = self.origin.reference_frame
        origin_T_self = self.origin

        if not reference_frame:
            reference_frame = self.origin.reference_frame

        reference_frame_world = reference_frame._world or origin_frame._world

        if reference_frame_world is not None:
            reference_T_origin: TransformationMatrix = reference_frame_world.compute_forward_kinematics(reference_frame,
                                                                                                        origin_frame)
        else:
            reference_T_origin: TransformationMatrix = TransformationMatrix()

        reference_T_self: TransformationMatrix = reference_T_origin @ origin_T_self

        # Get all 8 corners of the BB in link-local space
        list_self_T_corner = [
            TransformationMatrix.from_point_rotation_matrix(self_P_corner)
            for self_P_corner
            in self._local_bounding_box().get_points()
        ] # shape (8, 3)

        list_reference_T_corner = [reference_T_self @ self_T_corner for self_T_corner in list_self_T_corner]

        list_reference_P_corner = [reference_T_corner.to_position().to_np()[:3] for reference_T_corner in list_reference_T_corner]

        # Compute world-space bounding box from transformed corners
        min_corner = np.min(list_reference_P_corner, axis=0)
        max_corner = np.max(list_reference_P_corner, axis=0)

        world_bb = BoundingBox.from_min_max(Point3.from_iterable(min_corner), Point3.from_iterable(max_corner))

        return world_bb

    @abstractmethod
    def _local_bounding_box(self) -> BoundingBox:
        """
        Returns the local bounding box of the shape.
        This method should be implemented by subclasses.
        """
        ...

    @property
    def mesh(self) -> trimesh.Trimesh:
        """
        The mesh object of the shape.
        This should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the mesh property.")

@dataclass
class Mesh(Shape):
    """
    A mesh shape.
    """

    filename: str = ""
    """
    Filename of the mesh.
    """

    scale: Scale = field(default_factory=Scale)
    """
    Scale of the mesh.
    """

    @cached_property
    def mesh(self) -> trimesh.Trimesh:
        """
        The mesh object.
        """
        mesh = trimesh.load_mesh(self.filename)
        return mesh

    def _local_bounding_box(self) -> BoundingBox:
        """
        Returns the local bounding box of the mesh.
        The bounding box is axis-aligned and centered at the origin.
        """
        return BoundingBox.from_mesh(self.mesh)

@dataclass
class TriangleMesh(Shape):

    mesh: Optional[Trimesh] = None
    """
    The loaded mesh object.
    """

    scale: Scale = field(default_factory=Scale)
    """
    Scale of the mesh.
    """

    @cached_property
    def file(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        with open(f.name, "w") as fd:
            fd.write(trimesh.exchange.stl.export_stl_ascii(self.mesh))
        return f

    def _local_bounding_box(self) -> BoundingBox:
        """
        Returns the bounding box of the mesh.
        """
        return BoundingBox.from_mesh(self.mesh)


@dataclass
class Primitive(Shape, ABC):
    """
    A primitive shape.
    """
    color: Color = field(default_factory=Color)


@dataclass
class Sphere(Primitive):
    """
    A sphere shape.
    """

    radius: float = 0.5
    """
    Radius of the sphere.
    """

    @property
    def mesh(self) -> trimesh.Trimesh:
        """
        Returns a trimesh object representing the sphere.
        """
        return trimesh.creation.icosphere(subdivisions=2, radius=self.radius)

    def _local_bounding_box(self) -> BoundingBox:
        """
        Returns the bounding box of the sphere.
        """
        return BoundingBox(-self.radius, -self.radius, -self.radius,
                           self.radius, self.radius, self.radius)


@dataclass
class Cylinder(Primitive):
    """
    A cylinder shape.
    """
    width: float = 0.5
    height: float = 0.5

    @property
    def mesh(self) -> trimesh.Trimesh:
        """
        Returns a trimesh object representing the cylinder.
        """
        return trimesh.creation.cylinder(radius=self.width / 2, height=self.height, sections=16)

    def _local_bounding_box(self) -> BoundingBox:
        """
        Returns the bounding box of the cylinder.
        The bounding box is axis-aligned and centered at the origin.
        """
        half_width = self.width / 2
        half_height = self.height / 2
        return BoundingBox(-half_width, -half_width, -half_height,
                           half_width, half_width, half_height)


@dataclass
class Box(Primitive):
    """
    A box shape. Pivot point is at the center of the box.
    """
    scale: Scale = field(default_factory=Scale)

    @property
    def mesh(self) -> trimesh.Trimesh:
        """
        Returns a trimesh object representing the box.
        The box is centered at the origin and has the specified scale.
        """
        return trimesh.creation.box(extents=(self.scale.x, self.scale.y, self.scale.z))

    def _local_bounding_box(self) -> BoundingBox:
        """
        Returns the local bounding box of the box.
        The bounding box is axis-aligned and centered at the origin.
        """
        half_x = self.scale.x / 2
        half_y = self.scale.y / 2
        half_z = self.scale.z / 2
        return BoundingBox(-half_x, -half_y, -half_z,
                           half_x, half_y, half_z)


@dataclass
class BoundingBox:
    min_x: float
    """
    The minimum x-coordinate of the bounding box.
    """

    min_y: float
    """
    The minimum y-coordinate of the bounding box.
    """

    min_z: float
    """
    The minimum z-coordinate of the bounding box.
    """

    max_x: float
    """
    The maximum x-coordinate of the bounding box.
    """

    max_y: float
    """
    The maximum y-coordinate of the bounding box.
    """

    max_z: float
    """
    The maximum z-coordinate of the bounding box.
    """

    def __hash__(self):
        # The hash should be this since comparing those via hash is checking if those are the same and not just equal
        return hash((self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z))

    @property
    def x_interval(self) -> SimpleInterval:
        """
        :return: The x interval of the bounding box.
        """
        return SimpleInterval(self.min_x, self.max_x, Bound.CLOSED, Bound.CLOSED)

    @property
    def y_interval(self) -> SimpleInterval:
        """
        :return: The y interval of the bounding box.
        """
        return SimpleInterval(self.min_y, self.max_y, Bound.CLOSED, Bound.CLOSED)

    @property
    def z_interval(self) -> SimpleInterval:
        """
        :return: The z interval of the bounding box.
        """
        return SimpleInterval(self.min_z, self.max_z, Bound.CLOSED, Bound.CLOSED)

    @property
    def scale(self) -> Scale:
        """
        :return: The scale of the bounding box.
        """
        return Scale(self.depth, self.width, self.height)

    @property
    def depth(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_z - self.min_z

    @property
    def width(self) -> float:
        return self.max_y - self.min_y

    @property
    def simple_event(self) -> SimpleEvent:
        """
        :return: The bounding box as a random event.
        """
        return SimpleEvent({SpatialVariables.x.value: self.x_interval,
                            SpatialVariables.y.value: self.y_interval,
                            SpatialVariables.z.value: self.z_interval})

    def bloat(self, x_amount: float = 0., y_amount: float = 0, z_amount: float = 0) -> BoundingBox:
        """
        Enlarges the bounding box by a given amount in all dimensions.

        :param x_amount: The amount to adjust minimum and maximum x-coordinates
        :param y_amount: The amount to adjust minimum and maximum y-coordinates
        :param z_amount: The amount to adjust minimum and maximum z-coordinates
        :return: New enlarged bounding box
        """
        return self.__class__(self.min_x - x_amount, self.min_y - y_amount, self.min_z - z_amount,
                              self.max_x + x_amount, self.max_y + y_amount, self.max_z + z_amount)

    def contains(self, point: Point3) -> bool:
        """
        Check if the bounding box contains a point.
        """
        x, y, z = (point.x.to_np(), point.y.to_np(), point.z.to_np()) if isinstance(point.z, Expression) else (point.x, point.y, point.z)

        return self.simple_event.contains((x, y, z))

    def as_collection(self) -> BoundingBoxCollection:
        """
        Convert the bounding box to a collection of bounding boxes.

        :return: The bounding box as a collection
        """
        return BoundingBoxCollection([self])

    @classmethod
    def from_simple_event(cls, simple_event: SimpleEvent):
        """
        Create a list of bounding boxes from a simple random event.

        :param simple_event: The random event.
        :return: The list of bounding boxes.
        """
        result = []
        for x, y, z in itertools.product(simple_event[SpatialVariables.x.value].simple_sets,
                                         simple_event[SpatialVariables.y.value].simple_sets,
                                         simple_event[SpatialVariables.z.value].simple_sets):
            result.append(cls(x.lower, y.lower, z.lower, x.upper, y.upper, z.upper))
        return result

    def intersection_with(self, other: BoundingBox) -> Optional[BoundingBox]:
        """
        Compute the intersection of two bounding boxes.

        :param other: The other bounding box.
        :return: The intersection of the two bounding boxes or None if they do not intersect.
        """
        result = self.simple_event.intersection_with(other.simple_event)
        if result.is_empty():
            return None
        return self.__class__.from_simple_event(result)[0]

    def enlarge(self, min_x: float = 0., min_y: float = 0, min_z: float = 0,
                max_x: float = 0., max_y: float = 0., max_z: float = 0.):
        """
        Enlarge the axis-aligned bounding box by a given amount in-place.
        :param min_x: The amount to enlarge the minimum x-coordinate
        :param min_y: The amount to enlarge the minimum y-coordinate
        :param min_z: The amount to enlarge the minimum z-coordinate
        :param max_x: The amount to enlarge the maximum x-coordinate
        :param max_y: The amount to enlarge the maximum y-coordinate
        :param max_z: The amount to enlarge the maximum z-coordinate
        """
        self.min_x -= min_x
        self.min_y -= min_y
        self.min_z -= min_z
        self.max_x += max_x
        self.max_y += max_y
        self.max_z += max_z

    def enlarge_all(self, amount: float):
        """
        Enlarge the axis-aligned bounding box in all dimensions by a given amount in-place.

        :param amount: The amount to enlarge the bounding box
        """
        self.enlarge(amount, amount, amount,
                     amount, amount, amount)

    @classmethod
    def from_mesh(cls, mesh: trimesh.Trimesh) -> Self:
        """
        Create a bounding box from a trimesh object.
        :param mesh: The trimesh object.
        :return: The bounding box.
        """
        bounds = mesh.bounds
        return cls(bounds[0][0], bounds[0][1], bounds[0][2],
                   bounds[1][0], bounds[1][1], bounds[1][2])

    def get_points(self) -> List[Point3]:
        """
        Get the 8 corners of the bounding box as Point3 objects.

        :return: A list of Point3 objects representing the corners of the bounding box.
        """
        return [Point3(x, y, z)
                for x in (self.min_x, self.max_x)
                for y in (self.min_y, self.max_y)
                for z in (self.min_z, self.max_z)]

    @classmethod
    def from_min_max(cls, min_point: Point3, max_point: Point3) -> Self:
        """
        Set the axis-aligned bounding box from a minimum and maximum point.

        :param min_point: The minimum point
        :param max_point: The maximum point
        """
        return cls(*min_point.to_np()[:3], *max_point.to_np()[:3])

    def as_shape(self, reference_frame: Optional[Body] = None) -> Box:
        scale = Scale(x=self.max_x - self.min_x,
                      y=self.max_y - self.min_y,
                      z=self.max_z - self.min_z)
        x = (self.max_x + self.min_x) / 2
        y = (self.max_y + self.min_y) / 2
        z = (self.max_z + self.min_z) / 2
        origin = TransformationMatrix.from_xyz_rpy(x, y, z, 0, 0, 0, reference_frame)
        return Box(origin=origin, scale=scale)


@dataclass
class BoundingBoxCollection:
    """
    Dataclass for storing a collection of bounding boxes.
    """

    bounding_boxes: List[BoundingBox] = field(default_factory=list)

    def __iter__(self) -> Iterator[BoundingBox]:
        return iter(self.bounding_boxes)

    @property
    def event(self) -> Event:
        """
        :return: The bounding boxes as a random event.
        """
        return Event(*[box.simple_event for box in self.bounding_boxes])

    def merge(self, other: BoundingBoxCollection) -> BoundingBoxCollection:
        """
        Merge another bounding box collection into this one.

        :param other: The other bounding box collection.
        :return: The merged bounding box collection.
        """
        return BoundingBoxCollection(self.bounding_boxes + other.bounding_boxes)

    def bloat(self, x_amount: float = 0., y_amount: float = 0, z_amount: float = 0) -> BoundingBoxCollection:
        """
        Enlarges all bounding boxes in the collection by a given amount in all dimensions.

        :param x_amount: The amount to adjust the x-coordinates
        :param y_amount: The amount to adjust the y-coordinates
        :param z_amount: The amount to adjust the z-coordinates

        :return: The enlarged bounding box collection
        """
        return BoundingBoxCollection([box.bloat(x_amount, y_amount, z_amount) for box in self.bounding_boxes])

    @classmethod
    def from_simple_event(cls, simple_event: SimpleEvent, keep_surface: bool = False) -> BoundingBoxCollection:
        """
        Create a list of bounding boxes from a simple random event.

        :param simple_event: The random event.
        :param keep_surface: Whether to keep events that are infinitely thin
        :return: The list of bounding boxes.
        """
        result = []
        for x, y, z in itertools.product(simple_event[SpatialVariables.x.value].simple_sets,
                                         simple_event[SpatialVariables.y.value].simple_sets,
                                         simple_event[SpatialVariables.z.value].simple_sets):

            bb = BoundingBox(x.lower, y.lower, z.lower, x.upper, y.upper, z.upper)
            if not keep_surface and (bb.depth == 0 or bb.height == 0 or bb.width == 0):
                continue
            result.append(bb)
        return BoundingBoxCollection(result)

    @classmethod
    def from_event(cls, event: Event) -> Self:
        """
        Create a list of bounding boxes from a random event.

        :param event: The random event.
        :return: The list of bounding boxes.
        """
        return cls([box for simple_event in event.simple_sets for box in cls.from_simple_event(simple_event)])

    @classmethod
    def from_shapes(cls, shapes: List[Shape]) -> Self:
        """
        Create a bounding box collection from a list of shapes.

        :param shapes: The list of shapes.
        :return: The bounding box collection.
        """
        if not shapes:
            return cls([])
        if shapes:
            reference_frame = shapes[0].origin.reference_frame
            return cls([shape.as_bounding_box(reference_frame) for shape in shapes])

    def as_shapes(self, reference_frame: Optional[Body] = None) -> List[Box]:
        return [box.as_shape(reference_frame) for box in self.bounding_boxes]