from typing import Any, Callable, ForwardRef, Literal, Optional, Set, cast, get_args
from sqlalchemy import inspect, Column
from sqlalchemy.orm import DeclarativeBase
from pydantic import create_model, Field, BaseModel
from pydantic.fields import FieldInfo
from sqlalchemy.orm import Relationship
from .registry import SA2PYDANTIC_REGISTRY
from .types import PY_MODEL, SA_MODEL
from .type_util import is_optional 

_SENTIANL_NONE = object()

def get_default(param: Any):
    if param is None:
        return _SENTIANL_NONE
    if hasattr(param, "arg"):
        arg = param.arg
        if arg is not None:
            return arg
        else:
            return None
    return _SENTIANL_NONE


def col2fieldinfo(c: Column, 
                  override_optional: bool = False, 
                  override_default_value: Any = _SENTIANL_NONE): 
    assert isinstance(c, Column)
    python_type = c.type.python_type 

    if override_optional:
        if not is_optional(python_type):
            python_type = cast(type, Optional[python_type])
    else:
        if c.nullable:
            python_type = cast(type, Optional[python_type])

    field_kwargs: dict[str, Any] = {}

    if override_default_value != _SENTIANL_NONE:
        field_kwargs["default"] = override_default_value
    else:
        default_val = get_default(c.default)
        if default_val != _SENTIANL_NONE:
            field_kwargs["default"] = default_val

    field: FieldInfo = Field(**field_kwargs)

    return (python_type, field, )

def relationship2fieldinfo(rel: Relationship,
                           create_model_call: Callable[[SA_MODEL], PY_MODEL],
                           override_optional: bool = False): 
    assert isinstance(rel, Relationship)
    
    rel_model = rel.mapper.class_
    model: PY_MODEL = create_model_call(rel_model)

    default_value = [] if rel.uselist else None # type:ignore 

    type_ = relationship_python_type(model, rel)

    if override_optional and not is_optional(type_):
        type_ = Optional[type_]

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


OverrideOptionalType = Literal[""]


class Sa2Pydantic:
    
    def __init__(self,
                sa: SA_MODEL, 
                name_call: Callable[[SA_MODEL], str],
                exclude_rel: bool = False,
                exclude_foreignkeys: bool = False,
                exclude_fields: list[str] | None = None,
                exclude_primarykey: bool = False,
                override_optional: Callable[[Relationship | Column], bool] | bool | None = None,
                override_default_value: Callable[[Relationship | Column], Any] | Any | None = _SENTIANL_NONE,
                 ):
        self.namespace: dict[str, PY_MODEL | ForwardRef] = {}
        self.sa = sa
        self.name_call = name_call
        self.exclude_rel = exclude_rel
        self.exclude_foreignkeys = exclude_foreignkeys
        self.exclude_fields = exclude_fields or []
        self.exclude_primarykey = exclude_primarykey
        self.override_optional= override_optional
        self.override_default_value = override_default_value

    def process(self):
        model = self.sa2pydantic(self.sa)
        assert issubclass(model, BaseModel)

        assert all(issubclass(x,BaseModel) for x in self.namespace.values())

        self.model_rebuild_deep(model)
        return model

    def sa2pydantic(self, sa: SA_MODEL):
        assert issubclass(sa, DeclarativeBase), f"{sa} is no DeclarativeBase"
        model_name = self.name_call(sa)

        if sa in SA2PYDANTIC_REGISTRY and model_name in SA2PYDANTIC_REGISTRY[sa]:
            resolved = SA2PYDANTIC_REGISTRY[sa][model_name] 
            self.namespace[model_name] = resolved
            return resolved
        else:
            SA2PYDANTIC_REGISTRY[sa][model_name] = ForwardRef(model_name)

        inspection = inspect(sa)

        def keep_column(c: Column):
            if c.name in self.exclude_fields:
                return False
            if self.exclude_foreignkeys:
                if len(c.foreign_keys):
                    return False
            if self.exclude_primarykey:
                if c.primary_key:
                    return False
            return True

        column_fields = {
            c.name: self.col2fieldinfo(c) 
            for c in inspection.columns if keep_column(c)
            }

        if self.exclude_rel:
            relationship_fields = {}
        else:   
            relationship_fields = {
                r.key: self.relationship2fieldinfo(
                cast(Relationship, r),
                    create_model_call=lambda rel: self.sa2pydantic(rel)
                    ) 
                for r in inspection.relationships if r.key not in self.exclude_fields
                }

        model = create_model(model_name, **column_fields, **relationship_fields)
        assert issubclass(model, BaseModel)
        SA2PYDANTIC_REGISTRY[sa][model_name] = model
        self.namespace[model_name] = model
        return model

    def resolve_override_optional(self, p: Column | Relationship):
        override_optional = False
        if self.override_optional is not None:
            if callable(self.override_optional):
                override_optional = self.override_optional(p)
            elif isinstance(self.override_optional, bool):
                override_optional = self.override_optional
        return override_optional

    def relationship2fieldinfo(self, rel: Relationship, create_model_call: Callable[[SA_MODEL], PY_MODEL]): 

        override_optional = self.resolve_override_optional(rel)

        return relationship2fieldinfo(rel, create_model_call, override_optional=override_optional)

    def col2fieldinfo(self, c: Column):
        
        override_optional = self.resolve_override_optional(c)

        
        override_default_value = _SENTIANL_NONE

        if self.override_default_value != _SENTIANL_NONE:
            if callable(self.override_default_value):
                override_default_value = self.override_default_value(c)
            else:
                override_default_value = self.override_default_value
                

        return col2fieldinfo(c, override_optional=override_optional, override_default_value=override_default_value)


    def model_rebuild_deep(self, model: type[BaseModel], seen: Set[type[BaseModel]] | None = None):

        seen = seen or set()

        if model in seen:
            return
        model.model_rebuild(_types_namespace=self.namespace)
        seen.add(model)
        for field, info in model.model_fields.items():
            for a in get_args(info.annotation):
                if not issubclass(a, BaseModel):
                    continue
                self.model_rebuild_deep(a,  seen) 

