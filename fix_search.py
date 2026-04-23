import re

with open("src/docuflow/features/core/search.py", encoding="utf-8") as f:
    content = f.read()

# Add col import
content = content.replace("from sqlmodel import Session, select", "from sqlmodel import Session, select, col")

# Fix WorkItem.folder_name.ilike
content = re.sub(r"WorkItem\.folder_name\.ilike", "col(WorkItem.folder_name).ilike", content)
content = re.sub(r"WorkItem\.sidra_number\.ilike", "col(WorkItem.sidra_number).ilike", content)

# Fix PartLibrary.sku.ilike
content = re.sub(r"PartLibrary\.sku\.ilike", "col(PartLibrary.sku).ilike", content)

# Fix ProductionUnit.label_id.ilike
content = re.sub(r"ProductionUnit\.label_id\.ilike", "col(ProductionUnit.label_id).ilike", content)

with open("src/docuflow/features/core/search.py", "w", encoding="utf-8") as f:
    f.write(content)
