from sqlalchemy import DateTime, ForeignKey, Date, func, UniqueConstraint
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date


class Department(Base):
    __tablename__ = "departaments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] 
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("departaments.id",
                                                             ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )
    
    __table_args__ = (
        UniqueConstraint("parent_id", "name", name="uq_parent_name"),
    )
    
    children = relationship(
        "Department",
        cascade="all, delete",
        passive_deletes=True
    )

    employees = relationship(
        "Employee",
        cascade="all, delete",
        passive_deletes=True
    )

class Employee(Base):
    __tablename__ = "employeers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departaments.id",
                                                          ondelete="CASCADE"))
    full_name: Mapped[str]
    position: Mapped[str]
    hired_at: Mapped[date | None]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
        )