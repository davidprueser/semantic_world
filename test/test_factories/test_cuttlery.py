from semantic_world.adapters.viz_marker import VizMarkerPublisher
from semantic_world.datastructures.prefixed_name import PrefixedName
from semantic_world.testing import rclpy_node
from semantic_world.views.cuttlery import ForkFactory
from semantic_world.world import World


def test_fork_factory(rclpy_node):
    world = ForkFactory(name=PrefixedName("fork")).create()
    viz = VizMarkerPublisher(world=world, node=rclpy_node)
    viz.notify()
