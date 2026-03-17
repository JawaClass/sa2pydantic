from typing import Optional

import pytest
from pydantic import BaseModel, ValidationError

from sa2pydantic import sa2pydantic
from sa2pydantic.registry import SA2PYDANTIC_REGISTRY
from sa2pydantic.type_util import get_optional_inner, is_optional

from .conf import MyUser, Pokemon, Trainer


@pytest.fixture(autouse=True)
def clear_registry():
    SA2PYDANTIC_REGISTRY.clear()


def test_sa2pydantic():
    PokemonCreate = sa2pydantic(
        Pokemon,
        name_call=lambda sa: f"{sa.__name__.title()}Create",
    )
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
    PokemonCreate = sa2pydantic(
        Pokemon,
        name_call=lambda sa: f"{sa.__name__.title()}Create",
        exclude_fields="id",
    )
    assert issubclass(PokemonCreate, BaseModel)
    assert PokemonCreate.__name__ == "PokemonCreate"
    fields = PokemonCreate.model_fields
    assert "id" not in fields
    assert "level" in fields


def test_pk_excluded():
    PokemonCreate = sa2pydantic(
        Pokemon,
        name_call=lambda sa: f"{sa.__name__.title()}Create",
        exclude_primarykey=True,
    )
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
    assert is_optional(owner)
    TrainerOut = SA2PYDANTIC_REGISTRY[Trainer]["TrainerOut"]

    assert get_optional_inner(owner) is TrainerOut

    trainer_fields = TrainerOut.model_fields

    assert trainer_fields["name"].annotation is str
    assert trainer_fields["region"].annotation == str | None
    assert trainer_fields["pokemons"].annotation == list[PokemonOut], (
        f"{trainer_fields['pokemons'].annotation} not {list[PokemonOut]}"
    )


def test_relationship_self_referenced():
    PokemonOut = sa2pydantic(Pokemon, name_call=lambda sa: f"{sa.__name__.title()}Out")
    assert issubclass(PokemonOut, BaseModel)
    assert PokemonOut.__name__ == "PokemonOut"
    fields = PokemonOut.model_fields
    evolution = fields["evolution"].annotation
    assert is_optional(evolution)
    evolution_inner_type = get_optional_inner(evolution)
    assert evolution_inner_type is PokemonOut


def test_raise_required_args_missing():
    PokemonCreate = sa2pydantic(
        Pokemon,
        name_call=lambda sa: f"{sa.__name__.title()}Create",
        exclude_fields="id",
    )
    assert issubclass(PokemonCreate, BaseModel)
    assert PokemonCreate.__name__ == "PokemonCreate"
    err: None | ValidationError = None
    try:
        PokemonCreate()
    except ValidationError as e:
        err = e
    assert err and err.error_count() == 4

    err = None
    try:
        PokemonCreate(species="Bird")
    except ValidationError as e:
        err = e
    assert err and err.error_count() == 3

    err = None
    try:
        PokemonCreate(species="Bird", poke_type="...")
    except ValidationError as e:
        err = e
    assert err and err.error_count() == 2

    err = None
    try:
        PokemonCreate(species="Bird", poke_type="...", trainer_id=1, evolution_id=1)
    except ValidationError as e:
        err = e
    assert err is None


def test_relationship_optional_override():
    PokemonOut = sa2pydantic(
        Pokemon,
        name_call=lambda sa: f"{sa.__name__.title()}Out",
        override_optional=True,
        override_default_value=None,
    )
    assert issubclass(PokemonOut, BaseModel)
    assert PokemonOut.__name__ == "PokemonOut"
    fields = PokemonOut.model_fields

    for info in fields.values():
        assert is_optional(info.annotation)
        assert not info.is_required()

    # should not raise ValidationError
    PokemonOut()


def test_underscore_remove():
    MyUserOut = sa2pydantic(
        MyUser,
        name_call=lambda sa: f"{sa.__name__.title()}Out",
        leading_underscore_strategy="remove_underscore",
    )

    assert "underscore" in MyUserOut.model_fields


def test_underscore_skip():
    MyUserOut = sa2pydantic(
        MyUser,
        name_call=lambda sa: f"{sa.__name__.title()}Out",
        leading_underscore_strategy="skip_field",
    )

    assert "underscore" not in MyUserOut.model_fields
    assert "_underscore" not in MyUserOut.model_fields
