from sa2pydantic import sa2pydantic
from sa2pydantic.core import PY_MODEL
from .orm import Pokemon, Trainer
from pydantic import BaseModel

PokemonCreate: PY_MODEL = sa2pydantic(Pokemon, 
                                      exclude_fields=["id"],
                                      exclude_rel=True,
                                      exclude_foreignkeys=True,
                                      name_call=lambda sa: f"{sa.__name__.title()}Create")

PokemonOut: PY_MODEL = sa2pydantic(Pokemon,
                                   name_call=lambda sa:  f"{sa.__name__.title()}Out")



TrainerCreate: PY_MODEL = sa2pydantic(Trainer, 
                                      exclude_fields=["id"],
                                      exclude_rel=True,
                                      name_call=lambda sa: f"{sa.__name__.title()}Create")


TrainerOut: PY_MODEL = sa2pydantic(Trainer,
                                   name_call=lambda sa:  f"{sa.__name__.title()}Out")


PokemonOutOptional: PY_MODEL = sa2pydantic(Pokemon,
                                   name_call=lambda sa:  f"{sa.__name__.title()}OutOptional", 
                                   override_optional=True,
                                   override_default_value=None)


def describe_model(model: type[BaseModel]):
    print("Describe", model)
    for f, i  in model.model_fields.items():
        print(f'field {f}: default={i.default}, annotation={i.annotation}')

describe_model(PokemonCreate)
describe_model(PokemonOut)
describe_model(TrainerCreate)
describe_model(TrainerOut)
describe_model(TrainerOut)
describe_model(PokemonOutOptional)
