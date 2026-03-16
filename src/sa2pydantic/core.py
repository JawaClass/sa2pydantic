from typing import Any, Callable, ForwardRef, Optional, cast
from sqlalchemy import inspect, Column
from sqlalchemy.orm import DeclarativeBase
from pydantic import create_model, Field, BaseModel
from pydantic.fields import FieldInfo
from sqlalchemy.orm import Relationship
from .registry import SA2PYDANTIC_REGISTRY
from .types import PY_MODEL, SA_MODEL


def get_default(param: Any):
    if param is None:
        return None
    if hasattr(param, "arg"):
        arg = param.arg
        if arg is not None:
            return arg
    return None

def col2fieldinfo(c: Column): 
    assert isinstance(c, Column)
    python_type = c.type.python_type 
    type_: type[Any] = cast(type, python_type if not c.nullable else Optional[python_type])
    field: FieldInfo = Field(default=get_default(c.default))
    return (type_, field, )

def relationship2fieldinfo(rel: Relationship, create_model_call: Callable[[SA_MODEL], PY_MODEL]): 
    assert isinstance(rel, Relationship)
    
    rel_model = rel.mapper.class_
    model: PY_MODEL = create_model_call(rel_model)

    default_value = [] if rel.uselist else None # type:ignore 

    type_ = relationship_python_type(model, rel)

    return (type_, Field(default=default_value))


def relationship_python_type(model: PY_MODEL | ForwardRef, rel: Relationship):
    assert isinstance(rel, Relationship)
    assert isinstance(model, (type, ForwardRef, )), f"Pydantic Model Class expected. {model}"
    if isinstance(model, type):
        assert issubclass(model, BaseModel), f"Pydantic Model Class expected. {model}"

    if rel.uselist:
        return list[model] # type:ignore
    if rel.local_remote_pairs:
        for pair in rel.local_remote_pairs:
            for c in pair:
                if c.foreign_keys and c.nullable:
                    return Optional[model]

    return model

def sa2pydantic(sa: SA_MODEL, 
                name_call: Callable[[SA_MODEL], str],
                exclude_rel: bool = False,
                exclude_foreignkeys: bool = False,
                exclude_fields: list[str] | None = None,
                exclude_primarykey: bool = False,
                ):
    assert issubclass(sa, DeclarativeBase), f"{sa} is no DeclarativeBase"
    model_name = name_call(sa)

    if sa in SA2PYDANTIC_REGISTRY and model_name in SA2PYDANTIC_REGISTRY[sa]:
        resolved = SA2PYDANTIC_REGISTRY[sa][model_name] 
        return resolved
    else:
        SA2PYDANTIC_REGISTRY[sa][model_name] = ForwardRef(model_name)

    exclude_fields = exclude_fields or []

    inspection = inspect(sa)

    def keep_column(c: Column):
        if c.name in exclude_fields:
            return False
        if exclude_foreignkeys:
            if len(c.foreign_keys):
                return False
        if exclude_primarykey:
            if c.primary_key:
                return False
        return True

    column_fields = {
        c.name: col2fieldinfo(c) 
        for c in inspection.columns if keep_column(c)
        }

    if exclude_rel:
        relationship_fields = {}
    else:   
        relationship_fields = {
            r.key: relationship2fieldinfo(
               cast(Relationship, r),
                create_model_call=lambda rel: sa2pydantic(rel, name_call)
                ) 
            for r in inspection.relationships if r.key not in exclude_fields
            }

    model = create_model(model_name, **column_fields, **relationship_fields)
    assert issubclass(model, BaseModel)
    SA2PYDANTIC_REGISTRY[sa][model_name] = model
    return model
