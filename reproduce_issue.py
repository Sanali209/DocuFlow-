from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List
from datetime import datetime

class BaseEntity(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

class Project(BaseEntity, table=True):
    name: str = Field(unique=True, index=True)

engine = create_engine("sqlite:///:memory:", echo=True)
SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    print("Adding project 1...")
    p1 = Project(name="Project 1")
    session.add(p1)
    session.flush()
    print(f"Project 1 ID: {p1.id}")

with Session(engine) as session:
    print("Adding project 2...")
    p2 = Project(name="Project 2")
    session.add(p2)
    session.flush()
    print(f"Project 2 ID: {p2.id}")
