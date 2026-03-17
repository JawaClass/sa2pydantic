from typing import get_args

def is_optional(type_: type):
    args = get_args(type_)
    return type(None) in args

def get_optional_inner(type_: type):
    assert is_optional(type_)
    args = [a for a in get_args(type_) if a is not type(None)]
    assert len(args) == 1
    return args[0]