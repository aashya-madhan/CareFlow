from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic can detect them
from app.models.user import User          # noqa: F401, E402
from app.models.appointment import Appointment  # noqa: F401, E402
from app.models.department import Department    # noqa: F401, E402
from app.models.doctor import Doctor            # noqa: F401, E402
from app.models.patient import Patient          # noqa: F401, E402
