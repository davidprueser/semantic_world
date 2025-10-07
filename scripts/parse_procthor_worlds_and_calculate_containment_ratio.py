import os
from pathlib import Path
import tqdm
from ormatic.dao import to_dao
from ormatic.utils import recursive_subclasses, drop_database
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from semantic_world.adapters.procthor.procthor_parser import ProcTHORParser
from semantic_world.adapters.procthor.procthor_views import ProcthorResolver, HouseholdObject
from semantic_world.reasoning.predicates import InsideOf


def parse_procthor_worlds_and_calculate_containment_ratio():
    database_uri = os.environ.get("SEMANTIC_WORLD_DATABASE_URI")
    engine = create_engine(database_uri, echo=False)
    session = Session(engine)

    json_directory = "../resources/procthor_json"

    # Iterate through all JSON files in the directory
    for json_file in Path(json_directory).glob("*.json"):
        parser = ProcTHORParser(str(json_file), session)
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
        session.add(world_dao)

        pbar = tqdm.tqdm(world.bodies)
        containments = 0
        pbar.set_postfix({"containments": containments})
        for body in pbar:
            for other in world.bodies:
                if body != other:
                    is_inside = InsideOf(body, other)
                    if is_inside() > 0.:
                        containments += 1
                        dao = to_dao(is_inside, memo=memo)
                        daos.append(dao)
                        pbar.set_postfix({"containments": containments})

        session.add_all(daos)
        session.commit()


if __name__ == "__main__":
    parse_procthor_worlds_and_calculate_containment_ratio()