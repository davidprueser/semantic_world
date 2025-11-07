import itertools
import logging
import os

import prior
import tqdm
from krrood.entity_query_language.symbol_graph import SymbolGraph
from krrood.ormatic.dao import to_dao, ToDAOState
from krrood.utils import recursive_subclasses
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from semantic_digital_twin.adapters.procthor.procthor_parser import ProcTHORParser
from semantic_digital_twin.adapters.procthor.procthor_semantic_annotations import (
    ProcthorResolver,
    HouseholdObject,
)
from semantic_digital_twin.reasoning.predicates import InsideOf
from semantic_digital_twin.orm.ormatic_interface import *


def parse_procthor_worlds_and_calculate_containment_ratio():
    semantic_world_database_uri = os.environ.get("SEMANTIC_DIGITAL_TWIN_DATABASE_URI")
    semantic_world_engine = create_engine(semantic_world_database_uri, echo=False)
    semantic_world_session = Session(semantic_world_engine)

    procthor_experiments_database_uri = os.environ.get(
        "PROCTHOR_EXPERIMENTS_DATABASE_URI"
    )
    procthor_experiments_engine = create_engine(
        procthor_experiments_database_uri, echo=False
    )
    # drop_database(procthor_experiments_engine)
    # Base.metadata.create_all(procthor_experiments_engine)
    procthor_experiments_session = Session(procthor_experiments_engine)

    dataset = prior.load_dataset("procthor-10k")

    # Iterate through all JSON files in the directory
    for index, house in enumerate(
        tqdm.tqdm(dataset["train"], desc="Parsing Procthor worlds")
    ):
        if index < 8718:
            continue
        try:
            parser = ProcTHORParser(f"house_{index}", house, semantic_world_session)
            world = parser.parse()
        except Exception as e:
            logging.error(f"Error parsing house {index}: {e}")
            continue
        # resolve views
        resolver = ProcthorResolver(*[recursive_subclasses(HouseholdObject)])
        for body in world.bodies:
            resolved = resolver.resolve(body.name.name)
            if resolved:
                with world.modify_world():
                    world.add_semantic_annotation(
                        resolved(body=body), skip_duplicates=True
                    )

        state = ToDAOState()
        daos = []

        world_dao = to_dao(world, state=state)
        procthor_experiments_session.add(world_dao)

        for kse, other in itertools.product(
            world.kinematic_structure_entities, world.kinematic_structure_entities
        ):
            if kse != other:
                is_inside = InsideOf(kse, other)
                if is_inside() > 0.0:
                    dao = to_dao(is_inside, state=state)
                    daos.append(dao)

        procthor_experiments_session.add_all(daos)
        procthor_experiments_session.commit()
        procthor_experiments_session.expunge_all()
        semantic_world_session.expunge_all()
        SymbolGraph().clear()


if __name__ == "__main__":
    parse_procthor_worlds_and_calculate_containment_ratio()
