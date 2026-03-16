from .core import sa2pydantic as impl, SA_MODEL
from typing import Callable
from pydantic import BaseModel
from typing import get_args, Any, Set


def sa2pydantic(sa: SA_MODEL, 
                name_call: Callable[[SA_MODEL], str],
                exclude_rel: bool = False,
                exclude_foreignkeys: bool = False,
                exclude_fields: list[str] | None = None,
                exclude_primarykey: bool = False,
                ):
                def _run():
                    return impl(
                        sa=sa,
                        name_call=name_call,
                        exclude_rel=exclude_rel,
                        exclude_foreignkeys=exclude_foreignkeys,
                        exclude_fields=exclude_fields,
                        exclude_primarykey=exclude_primarykey
                )
                model = _run()
                from .core import SA2PYDANTIC_REGISTRY
                namespace = {}
                for sa in SA2PYDANTIC_REGISTRY:
                    for name, type_ in SA2PYDANTIC_REGISTRY[sa].items():
                            namespace[name] = type_
                model_rebuild_deep(model, namespace)
                return model


def model_rebuild_deep(model: type[BaseModel], namespace: dict[str, Any], seen: Set[type[BaseModel]] | None = None):

    seen = seen or set()

    if model in seen:
           return
    model.model_rebuild(_types_namespace=namespace)
    seen.add(model)
    for field, info in model.model_fields.items():
           args = get_args(info.annotation)
           for a in args:
                if not issubclass(a, BaseModel):
                    continue
                model_rebuild_deep(a, namespace, seen) 

__all__ = ["sa2pydantic"]