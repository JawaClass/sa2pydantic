from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

PY_MODEL = type[BaseModel]
SA_MODEL = type[DeclarativeBase]