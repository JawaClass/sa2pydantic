from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Integer

class Base(DeclarativeBase):
    pass

class Trainer(Base):
    __tablename__ = "trainer"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(30))

    pokemons: Mapped[List["Pokemon"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Trainer(id={self.id!r}, name={self.name!r})"

class Item(Base):
    __tablename__ = "item"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)

class PokemonHasItem(Base):
    __tablename__ = "pokemon_has_item"
    id: Mapped[int] = mapped_column(primary_key=True)
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"))
    pokemon = relationship("Pokemon", back_populates="items")


class Pokemon(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(primary_key=True)
    species: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    poke_type: Mapped[str] = mapped_column(String(20))

    trainer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trainer.id"), nullable=True)

    evolution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pokemon.id"))#, nullable=True)

    evolution: Mapped[Optional["Pokemon"]] = relationship() #foreign_keys=[evolution_id])
    owner: Mapped[Optional["Trainer"]] = relationship(back_populates="pokemons")
    items: Mapped[List[PokemonHasItem]] = relationship(back_populates="pokemon")