from collections.abc import Callable
from typing import Any

from sqlalchemy import Column
from sqlalchemy.orm import Relationship

from sa2pydantic.types import LeadingUnderscoreStrategy

from .core import _SENTIANL_NONE, SA_MODEL, Sa2Pydantic


def sa2pydantic(
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
    processor = Sa2Pydantic(
        sa=sa,
        name_call=name_call,
        exclude_rel=exclude_rel,
        exclude_foreignkeys=exclude_foreignkeys,
        exclude_fields=exclude_fields,
        exclude_primarykey=exclude_primarykey,
        override_optional=override_optional,
        override_default_value=override_default_value,
        leading_underscore_strategy=leading_underscore_strategy,
    )

    return processor.process()


__all__ = ["sa2pydantic"]
