from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

PY_MODEL = type[BaseModel]
SA_MODEL = type[DeclarativeBase]

LeadingUnderscoreStrategy = Literal["remove_underscore", "skip_field", "pass"]
