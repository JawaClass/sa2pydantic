from typing import List, Optional, get_args
from sa2pydantic import sa2pydantic
from .conf import Pokemon, Trainer
from pydantic import BaseModel
import pytest
from sa2pydantic.registry import SA2PYDANTIC_REGISTRY

@pytest.fixture(autouse=True)
def clear_registry():
    SA2PYDANTIC_REGISTRY.clear()


def is_optional(type_: type):
    args = get_args(type_)
    return type(None) in args

def get_optional_inner(type_: type):
    assert is_optional(type_)
    args = [a for a in get_args(type_) if a is not type(None)]
    assert len(args) == 1
    return args[0]

def test_sa2pydantic():
    PokemonCreate = sa2pydantic(Pokemon, name_call=lambda sa: f"{sa.__name__.title()}Create")
    assert issubclass(PokemonCreate, BaseModel)
    assert PokemonCreate.__name__ == "PokemonCreate"
    fields = PokemonCreate.model_fields
    assert fields["level"].annotation is int

    assert fields["trainer_id"].annotation == int | None
    assert fields["trainer_id"].annotation == Optional[int]


    assert is_optional(fields["evolution"].annotation)
    assert is_optional(fields["evolution_id"].annotation)
    assert fields["level"].default == 1

def test_id_excluded():
    PokemonCreate = sa2pydantic(Pokemon, name_call=lambda sa: f"{sa.__name__.title()}Create", exclude_fields="id")
    assert issubclass(PokemonCreate, BaseModel)
    assert PokemonCreate.__name__ == "PokemonCreate"
    fields = PokemonCreate.model_fields
    assert "id" not in fields
    assert "level" in fields


def test_pk_excluded():
    PokemonCreate = sa2pydantic(Pokemon, name_call=lambda sa: f"{sa.__name__.title()}Create", exclude_primarykey=True)
    assert issubclass(PokemonCreate, BaseModel)
    assert PokemonCreate.__name__ == "PokemonCreate"
    fields = PokemonCreate.model_fields
    assert "id" not in fields, f"id was in{fields.keys()}"


def test_relationship():
    PokemonOut = sa2pydantic(Pokemon, name_call=lambda sa: f"{sa.__name__.title()}Out")
    assert issubclass(PokemonOut, BaseModel)
    assert PokemonOut.__name__ == "PokemonOut"
    fields = PokemonOut.model_fields
    owner = fields["owner"].annotation
    print("OWNER", owner)
    assert is_optional(owner)
    TrainerOut = SA2PYDANTIC_REGISTRY[Trainer]["TrainerOut"]

    assert get_optional_inner(owner) is TrainerOut

    trainer_fields = TrainerOut.model_fields

    assert trainer_fields["name"].annotation is str
    assert trainer_fields["region"].annotation == str | None
    assert trainer_fields["pokemons"].annotation == list[PokemonOut], f"{trainer_fields['pokemons'].annotation} not {List[PokemonOut]}"

def test_relationship_self_referenced():
    PokemonOut = sa2pydantic(Pokemon, name_call=lambda sa: f"{sa.__name__.title()}Out")
    assert issubclass(PokemonOut, BaseModel)
    assert PokemonOut.__name__ == "PokemonOut"
    fields = PokemonOut.model_fields
    evolution = fields["evolution"].annotation
    assert is_optional(evolution)
    evolution_inner_type = get_optional_inner(evolution)
    assert evolution_inner_type is PokemonOut