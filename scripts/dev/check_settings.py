#!/usr/bin/env python3
"""Check NodeSetting entries in database."""

import sys

sys.path.insert(0, "src")

from sqlalchemy import create_engine
from sqlmodel import Session, select

from docuflow.domain.entities.identity import NodeSetting

# Connect to database
engine = create_engine("sqlite:///node_01.db")

with Session(engine) as session:
    settings = session.exec(select(NodeSetting)).all()

    print("=== NodeSetting entries ===")
    if not settings:
        print("No settings found!")
    else:
        for st in settings:
            print(f"node_id={st.node_id}, module={st.module}, key={st.key}, value={st.value}")
