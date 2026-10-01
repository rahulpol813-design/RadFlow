from sqlalchemy.orm import DeclarativeBase

"provide a unified Base class so all models share the same metadata registry:"
class Base(DeclarativeBase):
    pass


