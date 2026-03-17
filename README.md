# Convert Sqlalchmey ORM Classes to Pydantic models

### An Sqlalchemy ORM Model

```python
class Pokemon(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    poke_type: Mapped[str] = mapped_column(String(20))

    trainer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trainer.id"), nullable=True)

    evolution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pokemon.id"))

    evolution: Mapped[Optional["Pokemon"]] = relationship()
    owner: Mapped[Optional["Trainer"]] = relationship(back_populates="pokemons")
    items: Mapped[List[PokemonHasItem]] = relationship(back_populates="pokemon")
```

### Usage

```python
from sa2pydantic import sa2pydantic

# Create an Pydantic Create Model for Post Method
PokemonCreate = sa2pydantic(Pokemon,
    name_call=lambda sa: f"{sa.__name__.title()}Create",
    exclude_primarykey=True,
    exclude_rel=True,
    )
# <class 'sa2pydantic.core.PokemonCreate'>
# species: default=PydanticUndefined, annotation=<class 'str'>
# level: default=1, annotation=<class 'int'>
# poke_type: default=PydanticUndefined, annotation=<class 'str'>

```

```python
# Create an Pydantic Output Model for Get Method
PokemonOut = sa2pydantic(Pokemon,
    name_call=lambda sa: f"{sa.__name__.title()}Out")

# <class 'sa2pydantic.core.PokemonOut'>
# id: default=PydanticUndefined, annotation=<class 'int'>
# species: default=PydanticUndefined, annotation=<class 'str'>
# level: default=1, annotation=<class 'int'>
# poke_type: default=PydanticUndefined, annotation=<class 'str'>
# trainer_id: default=PydanticUndefined, annotation=typing.Optional[int]
# evolution_id: default=PydanticUndefined, annotation=typing.Optional[int]
# evolution: default=None, annotation=typing.Optional[sa2pydantic.core.PokemonOut]
# owner: default=None, annotation=typing.Optional[sa2pydantic.core.TrainerOut]
# items: default=[], annotation=list[sa2pydantic.core.PokemonhasitemOut]

```

```python
# Create an Pydantic Output Model with all fields as optional with default value
PokemonOutOptional: PY_MODEL = sa2pydantic(Pokemon,
                                   name_call=lambda sa:  f"{sa.__name__.title()}OutOptional",
                                   override_optional=True,
                                   override_default_value=None)

# <class 'sa2pydantic.core.PokemonOutOptional'>
# id: default=None, annotation=typing.Optional[int]
# species: default=None, annotation=typing.Optional[str]
# level: default=None, annotation=typing.Optional[int]
# poke_type: default=None, annotation=typing.Optional[str]
# trainer_id: default=None, annotation=typing.Optional[int]
# evolution_id: default=None, annotation=typing.Optional[int]
# evolution: default=None, annotation=typing.Optional[sa2pydantic.core.PokemonOutOptional]
# owner: default=None, annotation=typing.Optional[sa2pydantic.core.TrainerOutOptional]
# items: default=[], annotation=typing.Optional[list[sa2pydantic.core.PokemonhasitemOutOptional]]

```
