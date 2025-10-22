import itertools
import os
from io import BytesIO, StringIO
from pathlib import Path
import tqdm
from ormatic.dao import to_dao
from ormatic.utils import recursive_subclasses, drop_database
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import prior

from semantic_world.adapters.procthor.procthor_parser import ProcTHORParser
from semantic_world.adapters.procthor.procthor_views import (
    ProcthorResolver,
    HouseholdObject,
)
from semantic_world.orm.ormatic_interface import *
from semantic_world.reasoning.predicates import InsideOf


def parse_procthor_worlds_and_calculate_containment_ratio():
    semantic_world_database_uri = os.environ.get("SEMANTIC_WORLD_DATABASE_URI")
    semantic_world_engine = create_engine(semantic_world_database_uri, echo=False)
    semantic_world_session = Session(semantic_world_engine)

    procthor_experiments_database_uri = os.environ.get(
        "PROCTHOR_EXPERIMENTS_DATABASE_URI"
    )
    procthor_experiments_engine = create_engine(
        procthor_experiments_database_uri, echo=False
    )
    drop_database(procthor_experiments_engine)
    Base.metadata.create_all(procthor_experiments_engine)
    procthor_experiments_session = Session(procthor_experiments_engine)

    dataset = prior.load_dataset("procthor-10k")

    # Iterate through all JSON files in the directory
    for index, house in enumerate(
        tqdm.tqdm(dataset["train"], desc="Parsing Procthor worlds")
    ):
        parser = ProcTHORParser(f"house_{index}", house, semantic_world_session)
        world = parser.parse()

        # resolve views
        resolver = ProcthorResolver(*[recursive_subclasses(HouseholdObject)])
        for body in world.bodies:
            resolved = resolver.resolve(body.name.name)
            if resolved:
                world.add_view(resolved(body=body), exists_ok=True)

        memo = {}
        daos = []

        world_dao = to_dao(world, memo=memo)
        procthor_experiments_session.add(world_dao)

        for body, other in itertools.product(world.bodies, world.bodies):
            if body != other:
                is_inside = InsideOf(body, other)
                if is_inside() > 0.0:
                    dao = to_dao(is_inside, memo=memo)
                    daos.append(dao)

        procthor_experiments_session.add_all(daos)
        procthor_experiments_session.commit()


if __name__ == "__main__":
    parse_procthor_worlds_and_calculate_containment_ratio()
