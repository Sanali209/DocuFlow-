import os
import uuid
from sqlalchemy.orm import Session
from typing import Generator, Dict, Any
from . import models, crud
from .gnc_parser import GNCParser
from .svg_generator import SVGGenerator

# Robust path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMBNAIL_DIR = os.path.join(BASE_DIR, "static", "uploads", "thumbnails")

def scan_library(db: Session) -> Generator[Dict[str, Any], None, None]:
    """
    Scan configured network paths for GNC files and import them as:
    1. Orders and Tasks (from michtav subfolders)
    2. Parts (from sidra and general michtav GNC files)
    
    Yields progress updates as dicts with keys: status, message, percent
    """
    # Get paths from settings (same keys as sync service)
    mihtav_setting = crud.get_setting(db, "sync_mihtav_path")
    sidra_setting = crud.get_setting(db, "sync_sidra_path")
    
    mihtav_path = mihtav_setting.value if mihtav_setting else None
    sidra_path = sidra_setting.value if sidra_setting else None
    
    # Check if paths are configured and not empty
    if (not mihtav_path or not mihtav_path.strip()) and (not sidra_path or not sidra_path.strip()):
        yield {"status": "error", "message": "No paths configured", "percent": 0}
        return
    
    parser = GNCParser()
    svg_gen = SVGGenerator()
    
    # Scan michtav for MAIL
    if mihtav_path and os.path.exists(mihtav_path):
        yield from _scan_directory_generic(db, mihtav_path, models.DocumentType.MAIL, parser, svg_gen)

    # Scan sidra for PLAN
    if sidra_path and os.path.exists(sidra_path):
        yield from _scan_directory_generic(db, sidra_path, models.DocumentType.PLAN, parser, svg_gen)
    
    yield {
        "status": "complete",
        "message": f"Scan complete.",
        "percent": 100
    }

def _scan_directory_generic(db: Session, root_path: str, doc_type: models.DocumentType, parser, svg_gen):
    """
    Generic scanner for immediate children of root_path.
    - Directory -> Document (Name=DirName). Scans immediate files inside as Tasks (Name=FileName).
    - File -> Document (Name=FileName). File is single Task (Name=FileName).
    """
    
    # Pre-calculate files to skip (deduplication) in the root path itself
    # But wait, logic says:
    # If child is Dir -> Document.
    # If child is File -> Document.
    
    # We iterate immediate children
    try:
        with os.scandir(root_path) as it:
            entries = list(it) 
    except OSError:
        return

    # Sort entries for consistent processing
    entries.sort(key=lambda e: e.name)
    
    # Filter out _801 duplicates at the ROOT level (for File->Document case)
    # Actually, deduplication is per "Scope".
    # Case 1: Child IS File. Scope is root_path.
    # Case 2: Child IS Dir. Scope is that Dir.
    
    # Let's handle File-as-Document deduplication
    root_files = [e for e in entries if e.is_file() and e.name.lower().endswith('.gnc')]
    base_files_root = set()
    suffixes = ['_801', 'to801', '_to801']
    
    for f in root_files:
        fname = f.name[:-4].lower()
        is_suffixed = False
        for s in suffixes:
            if fname.endswith(s):
                is_suffixed = True
                break
        if not is_suffixed:
            base_files_root.add(fname)
            
    for entry in entries:
        try:
            if entry.is_dir():
                # Directory -> Document logic
                dir_name = entry.name
                
                # Create/Get Document
                doc = _get_or_create_document(db, dir_name, doc_type, os.path.abspath(entry.path))
                
                # Scan immediate files in this directory
                try:
                    with os.scandir(entry.path) as sub_it:
                        sub_entries = list(sub_it)
                except OSError:
                    continue

                sub_files = [e for e in sub_entries if e.is_file() and e.name.lower().endswith('.gnc')]
                
                # Deduplication logic within this directory
                base_files_subdir = set()
                for f in sub_files:
                    fname = f.name[:-4].lower()
                    is_suffixed = False
                    for s in suffixes:
                        if fname.endswith(s):
                            is_suffixed = True
                            break
                    if not is_suffixed:
                        base_files_subdir.add(fname)

                # Process tasks
                task_created = False
                for sub_file in sub_files:
                    fname = sub_file.name[:-4].lower()
                    
                    # Dedupe check
                    skipped = False
                    for s in suffixes:
                        if fname.endswith(s):
                            potential_base = fname[:-len(s)]
                            if potential_base in base_files_subdir:
                                skipped = True
                                break
                    if skipped:
                        continue
                        
                    yield {
                        "status": "scanning",
                        "message": f"Processing task: {dir_name}/{sub_file.name}",
                        "percent": 50 # approximation
                    }
                    
                    _process_task(db, doc, sub_file.path, sub_file.name, parser, svg_gen)
                    task_created = True
                    
            elif entry.is_file() and entry.name.lower().endswith('.gnc'):
                # File -> Document logic
                fname = entry.name[:-4].lower()
                
                # Dedupe check at root level
                skipped = False
                for s in suffixes:
                    if fname.endswith(s):
                        potential_base = fname[:-len(s)]
                        if potential_base in base_files_root:
                            skipped = True
                            break
                if skipped:
                    continue

                doc_name = entry.name[:-4] # No extension
                yield {
                        "status": "scanning",
                        "message": f"Processing document: {doc_name}",
                        "percent": 50
                }
                
                doc = _get_or_create_document(db, doc_name, doc_type, os.path.abspath(entry.path))
                _process_task(db, doc, entry.path, entry.name, parser, svg_gen)

        except Exception as e:
             yield {"status": "error", "message": f"Error processing {entry.name}: {str(e)}", "percent": 0}

def _get_or_create_document(db: Session, name: str, type: models.DocumentType, description_path: str) -> models.Document:
    doc = db.query(models.Document).filter(
        models.Document.name == name,
        models.Document.type == type
    ).first()
    
    if not doc:
        doc = models.Document(
            name=name,
            type=type,
            status=models.DocumentStatus.UNREGISTERED,
            description=f"Path: {description_path}"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
    return doc

def _process_task(db: Session, doc: models.Document, file_path: str, filename: str, parser, svg_gen):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        sheet = parser.parse(content, filename=filename)
        
        # Determine Material
        material_name = sheet.material or "Unknown"
        material = db.query(models.Material).filter(models.Material.name == material_name).first()
        if not material:
            material = models.Material(name=material_name)
            db.add(material)
            db.commit()
            db.refresh(material)
            
        # Check/Create Task
        task = db.query(models.Task).filter(
            models.Task.document_id == doc.id,
            models.Task.gnc_file_path == file_path
        ).first()
        
        if not task:
            task = models.Task(
                document_id=doc.id,
                name=filename, # Task name is file name
                material_id=material.id,
                gnc_file_path=file_path,
                status=models.TaskStatus.PLANNED
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            
        # Parts Linking & Thumbnail generation
        
        # 1. Count parts in the sheet first
        part_counts = {}
        for p in sheet.parts:
            # Parse Name: Strip last group if it's a number
            raw_name = p.name or "Unknown"
            parts_split = raw_name.rsplit('-', 1)
            clean_name = raw_name
            if len(parts_split) > 1 and parts_split[1].isdigit():
                clean_name = parts_split[0]
            
            # Normalize part count key
            # We use the clean_name to identify the "Part", but we need to track specific GNC part objects for thumbnail generation?
            # Actually, all instances of the same "Part" (same name) should share the same definition in DB.
            # But they might be different geometries if the name is reused? 
            # Assuming name uniqueness for Part identity as per existing logic.
            
            if clean_name not in part_counts:
                part_counts[clean_name] = {
                    'count': 0,
                    'example_part': p, # Keep one for thumbnail gen
                    'reg_number': p.metadata.get('registration_number', clean_name)
                }
            part_counts[clean_name]['count'] += 1

        # 2. Update DB and Links
        for name, info in part_counts.items():
            count = info['count']
            p = info['example_part']
            reg_number = info['reg_number']
            
            # Find/Create Part
            db_part = db.query(models.Part).filter(models.Part.name == name).first()
            
            # Thumbnails
            os.makedirs(THUMBNAIL_DIR, exist_ok=True)
            thumbnail_filename = f"{reg_number}.svg"
            thumbnail_path = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
            width, height = svg_gen.generate_thumbnail(p, thumbnail_path)
            
            if db_part:
                db_part.width = width
                db_part.height = height
                db_part.gnc_file_path = file_path
                db_part.material_id = material.id
                db.commit()
            else:
                db_part = models.Part(
                    name=name,
                    registration_number=reg_number,
                    version="A",
                    material_id=material.id,
                    gnc_file_path=file_path,
                    width=width,
                    height=height
                )
                db.add(db_part)
                db.commit()
                db.refresh(db_part)
            
            # Manage Link (TaskPart)
            # Check if link exists
            task_part = db.query(models.TaskPart).filter(
                models.TaskPart.task_id == task.id,
                models.TaskPart.part_id == db_part.id
            ).first()

            if task_part:
                task_part.quantity = count
            else:
                task_part = models.TaskPart(
                    task_id=task.id,
                    part_id=db_part.id,
                    quantity=count
                )
                db.add(task_part)
            
            db.commit()
                
    except Exception as e:
        print(f"Error processing task {filename}: {e}")
