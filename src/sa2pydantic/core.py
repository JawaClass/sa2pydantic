from collections.abc import Callable
from typing import Any, ForwardRef, Optional, cast, get_args

from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo
from sqlalchemy import Column, inspect
from sqlalchemy.orm import DeclarativeBase, Relationship

from .registry import SA2PYDANTIC_REGISTRY
from .type_util import is_optional
from .types import PY_MODEL, SA_MODEL, LeadingUnderscoreStrategy

_SENTIANL_NONE = object()


def get_default(param: Any):
    if param is None:
        return _SENTIANL_NONE
    if hasattr(param, "arg"):
        arg = param.arg
        if arg is not None:
            return arg
        return None
    return _SENTIANL_NONE


def col2fieldinfo(
    c: Column,
    override_optional: bool = False,
    override_default_value: Any = _SENTIANL_NONE,
):
    assert isinstance(c, Column)
    python_type = c.type.python_type

    if override_optional:
        if not is_optional(python_type):
            python_type = cast("type", Optional[python_type])
    elif c.nullable:
        python_type = cast("type", Optional[python_type])

    field_kwargs: dict[str, Any] = {}

    if override_default_value != _SENTIANL_NONE:
        field_kwargs["default"] = override_default_value
    else:
        default_val = get_default(c.default)
        if default_val != _SENTIANL_NONE:
            field_kwargs["default"] = default_val

    field: FieldInfo = Field(**field_kwargs)

    return (python_type, field)


def relationship2fieldinfo(
    rel: Relationship,
    create_model_call: Callable[[SA_MODEL], PY_MODEL],
    override_optional: bool = False,
):
    assert isinstance(rel, Relationship)

    rel_model = rel.mapper.class_
    model: PY_MODEL = create_model_call(rel_model)

    default_value = [] if rel.uselist else None

    type_ = relationship_python_type(model, rel)

    if override_optional and not is_optional(type_):
        type_ = Optional[type_]

    return (type_, Field(default=default_value))


def relationship_python_type(model: PY_MODEL | ForwardRef, rel: Relationship):
    assert isinstance(rel, Relationship)
    assert isinstance(model, (type, ForwardRef)), (
        f"Pydantic Model Class expected. {model}"
    )
    if isinstance(model, type):
        assert issubclass(model, BaseModel), f"Pydantic Model Class expected. {model}"

    if rel.uselist:
        return list[model]
    if rel.local_remote_pairs:
        for pair in rel.local_remote_pairs:
            for c in pair:
                if c.foreign_keys and c.nullable:
                    return Optional[model]

    return model


class Sa2Pydantic:
    def __init__(
        self,
        sa: SA_MODEL,
        name_call: Callable[[SA_MODEL], str],
        exclude_rel: bool = False,
        exclude_foreignkeys: bool = False,
        exclude_fields: list[str] | None = None,
        exclude_primarykey: bool = False,
        override_optional: Callable[[Relationship | Column], bool] | bool | None = None,
        override_default_value: Callable[[Relationship | Column], Any]
        | Any
        | None = _SENTIANL_NONE,
        leading_underscore_strategy: LeadingUnderscoreStrategy = "pass",
    ):
        self.namespace: dict[str, PY_MODEL | ForwardRef] = {}
        self.sa = sa
        self.name_call = name_call
        self.exclude_rel = exclude_rel
        self.exclude_foreignkeys = exclude_foreignkeys
        self.exclude_fields = exclude_fields or []
        self.exclude_primarykey = exclude_primarykey
        self.override_optional = override_optional
        self.override_default_value = override_default_value
        self.leading_underscore_strategy = leading_underscore_strategy

    def process(self):
        model = self.sa2pydantic(self.sa)
        assert issubclass(model, BaseModel)

        assert all(issubclass(x, BaseModel) for x in self.namespace.values())

        self.model_rebuild_deep(model)
        return model

    def sa2pydantic(self, sa: SA_MODEL):  # noqa: C901
        assert issubclass(sa, DeclarativeBase), f"{sa} is no DeclarativeBase"
        model_name = self.name_call(sa)

        if sa in SA2PYDANTIC_REGISTRY and model_name in SA2PYDANTIC_REGISTRY[sa]:
            resolved = SA2PYDANTIC_REGISTRY[sa][model_name]
            self.namespace[model_name] = resolved
            return resolved
        SA2PYDANTIC_REGISTRY[sa][model_name] = ForwardRef(model_name)

        inspection = inspect(sa)

        def rename_field(name: str):
            if (
                self.leading_underscore_strategy == "remove_underscore"
                and name.startswith(
                    "_",
                )
            ):
                return name[1:]
            return name

        def keep_column(c: Column):
            if self.leading_underscore_strategy == "skip_field" and c.name.startswith(
                "_",
            ):
                return False
            if c.name in self.exclude_fields:
                return False
            if self.exclude_foreignkeys and len(c.foreign_keys):
                return False
            return not (self.exclude_primarykey and c.primary_key)

        column_fields = {
            rename_field(c.name): self.col2fieldinfo(c)
            for c in inspection.columns
            if keep_column(c)
        }

        if self.exclude_rel:
            relationship_fields = {}
        else:

            def keep_rel(rel: Relationship):
                if (
                    self.leading_underscore_strategy == "skip_field"
                    and rel.key.startswith("_")
                ):
                    return False
                return rel.key not in self.exclude_fields

            relationship_fields = {
                rename_field(r.key): self.relationship2fieldinfo(
                    cast("Relationship", r),
                    create_model_call=self.sa2pydantic,
                )
                for r in inspection.relationships
                if keep_rel(r)
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

    def relationship2fieldinfo(
        self,
        rel: Relationship,
        create_model_call: Callable[[SA_MODEL], PY_MODEL],
    ):

        override_optional = self.resolve_override_optional(rel)

        return relationship2fieldinfo(
            rel,
            create_model_call,
            override_optional=override_optional,
        )

    def col2fieldinfo(self, c: Column):

        override_optional = self.resolve_override_optional(c)

        override_default_value = _SENTIANL_NONE

        if self.override_default_value != _SENTIANL_NONE:
            if callable(self.override_default_value):
                override_default_value = self.override_default_value(c)
            else:
                override_default_value = self.override_default_value

        return col2fieldinfo(
            c,
            override_optional=override_optional,
            override_default_value=override_default_value,
        )

    def model_rebuild_deep(
        self,
        model: type[BaseModel],
        seen: set[type[BaseModel]] | None = None,
    ):

        seen = seen or set()

        if model in seen:
            return
        model.model_rebuild(_types_namespace=self.namespace)
        seen.add(model)
        for info in model.model_fields.values():
            for a in get_args(info.annotation):
                if not issubclass(a, BaseModel):
                    continue
                self.model_rebuild_deep(a, seen)
