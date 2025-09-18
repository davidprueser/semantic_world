from dataclasses import dataclass, field

from random_events.interval import closed
from random_events.product_algebra import SimpleEvent

from .factories import ViewFactory
from .views import Handle
from ..datastructures.prefixed_name import PrefixedName
from ..datastructures.variables import SpatialVariables
from ..spatial_types import TransformationMatrix
from ..world import World
from ..world_description.connections import FixedConnection
from ..world_description.geometry import Scale
from ..world_description.shape_collection import BoundingBoxCollection
from ..world_description.world_entity import View, Body


@dataclass(eq=False)
class Cuttlery(View): ...


@dataclass(eq=False)
class Fork(Cuttlery):
    tip: Body
    handle: Handle


@dataclass
class ForkFactory(ViewFactory[Fork]):

    scale: Scale = field(default_factory=Scale)

    def _create(self, world: World) -> World:
        fork_handle_body = Body(name=PrefixedName("fork_handle"))
        fork_handle = SimpleEvent(
            {
                SpatialVariables.x.value: closed(
                    -self.scale.x * 1 / 3, self.scale.x * 1 / 3
                ),
                SpatialVariables.y.value: closed(-self.scale.y / 5, self.scale.y / 5),
                SpatialVariables.z.value: closed(-self.scale.z / 2, self.scale.z / 2),
            }
        ).as_composite_set()
        fork_handle_body.collision = BoundingBoxCollection.from_event(
            fork_handle_body, fork_handle
        ).as_shapes()

        fork_tip_body = Body(name=PrefixedName("fork_tip"))
        fork_tip = SimpleEvent(
            {
                SpatialVariables.x.value: closed(0.0, self.scale.x / 3),
                SpatialVariables.y.value: closed(-self.scale.y / 2, self.scale.y / 2),
                SpatialVariables.z.value: closed(-self.scale.z / 2, self.scale.z / 2),
            }
        ).as_composite_set()
        fork_tip_holes = SimpleEvent(
            {
                SpatialVariables.x.value: closed(self.scale.x / 6, self.scale.x / 3),
                SpatialVariables.y.value: (
                    closed(self.scale.y * -4 / 10, self.scale.y * -3 / 10)
                    | closed(self.scale.y * -1.0 / 10, self.scale.y * 1.5 / 10)
                    | closed(self.scale.y * 3 / 10, self.scale.y * 4 / 10)
                ),
                SpatialVariables.z.value: closed(-self.scale.z / 2, self.scale.z / 2),
            }
        ).as_composite_set()

        fork_tip_body.collision = BoundingBoxCollection.from_event(
            fork_tip_body, fork_tip - fork_tip_holes
        ).as_shapes()

        with world.modify_world():
            world.add_body(fork_handle_body)
            world.add_body(fork_tip_body)

            handle_T_tip = FixedConnection(
                parent=fork_handle_body,
                child=fork_tip_body,
                origin_expression=TransformationMatrix.from_xyz_rpy(
                    x=self.scale.x * 1 / 3, reference_frame=fork_handle_body
                ),
            )
            world.add_connection(handle_T_tip)

        print(world.bodies)
        return world
