import os
from datetime import date

from src.domain.interfaces import IDocumentRepository
from src.domain.models import Document, Tag


class DocumentService:
    def __init__(self, doc_repo: IDocumentRepository):
        self.doc_repo = doc_repo

    def get_document(self, document_id: int) -> Document | None:
        # business logic can go here (e.g. tracking, permission check)
        return self.doc_repo.get_by_id(document_id)

    def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        type: str = None,
        status: str = None,
        tag: str = None,
        assignee: str = None,
        material_id: int = None,
        part_search: str = None,
        sort_by: str = "registration_date",
        sort_order: str = "desc",
        start_date: date = None,
        end_date: date = None,
        date_field: str = "registration_date",
    ) -> list[Document]:
        return self.doc_repo.list(
            skip=skip,
            limit=limit,
            search=search,
            type=type,
            status=status,
            tag=tag,
            assignee=assignee,
            material_id=material_id,
            part_search=part_search,
            sort_by=sort_by,
            sort_order=sort_order,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field,
        )

    def create_document(self, document: Document) -> Document:
        # business logic: validation, default values, side effects
        return self.doc_repo.add(document)

    def update_document(self, document: Document) -> Document:
        return self.doc_repo.update(document)

    def delete_document(self, document_id: int) -> bool:
        return self.doc_repo.delete(document_id)

    def create_order(self, name: str, items: list[dict]) -> Document:
        return self.doc_repo.create_order(name, items)

    def save_as_new_order(self, data: dict) -> Document:
        import uuid

        from src.infrastructure.graphics.gnc_generator import GNCGenerator
        from src.infrastructure.parsers.gnc_parser import GNCSheet

        # 1. Prepare storage
        order_uid = str(uuid.uuid4())
        output_dir = f"static/orders/{order_uid}"
        os.makedirs(output_dir, exist_ok=True)

        generator = GNCGenerator()
        sheets_processing = []

        # 2. Generate Files
        for i, sheet_wrapper in enumerate(data.get("sheets", [])):
            # Wrapper has {name, data: sheet_obj}
            sheet_data = sheet_wrapper.get("data", {})
            sheet_name = sheet_wrapper.get("name", f"Sheet {i + 1}")

            # Convert dict to GNCSheet object
            try:
                sheet_obj = GNCSheet.model_validate(sheet_data)
            except Exception as e:
                print(f"Error parsing sheet {sheet_name}: {e}")
                continue

            # Generate GNC content
            content = generator.generate(sheet_obj)

            # Save to disk
            filename = f"{sheet_name}.GNC"  # User requested .GNC
            # Sanitize filename?
            safe_filename = "".join(
                [c for c in filename if c.isalpha() or c.isdigit() or c in " ._-"]
            )
            file_path = os.path.join(output_dir, safe_filename)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            sheets_processing.append(
                {
                    "name": sheet_name,
                    "file_path": file_path,
                    "sheet_data": sheet_data,  # Keep original data if needed?
                }
            )

        # 3. Call Repository
        data["sheets_processing"] = sheets_processing
        return self.doc_repo.save_as_new_order(data)

    def list_tags(self) -> list[Tag]:
        return self.doc_repo.list_tags()

    def get_dashboard_stats(self) -> dict:
        return self.doc_repo.get_dashboard_stats()

    def delete_attachment(self, attachment_id: int) -> bool:
        return self.doc_repo.delete_attachment(attachment_id)

    def get_document_zip(self, document_id: int):
        import uuid

        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            return None

        # Collect all file paths (Attachments + Tasks)
        files_to_zip = []

        if doc.attachments:
            for att in doc.attachments:
                if os.path.exists(att.file_path):
                    files_to_zip.append(att.file_path)

        # Check tasks for GNC files not in attachments (redundancy)
        if doc.tasks:
            for task in doc.tasks:
                if task.gnc_file_path and os.path.exists(task.gnc_file_path):
                    if task.gnc_file_path not in files_to_zip:
                        files_to_zip.append(task.gnc_file_path)

        if not files_to_zip:
            return None

        # Determine common folder or create temp
        # For our new orders, they are in static/orders/{uuid}/
        # Check if all files are in the same directory
        first_dir = os.path.dirname(files_to_zip[0])
        all_same_dir = all(os.path.dirname(f) == first_dir for f in files_to_zip)

        from src.infrastructure.zip_util import create_folder_zip

        if all_same_dir:
            return create_folder_zip(first_dir)
        else:
            # Create a temp directory structure
            import shutil
            import tempfile

            temp_dir = tempfile.mkdtemp()
            try:
                for src_path in files_to_zip:
                    fname = os.path.basename(src_path)
                    dst_path = os.path.join(temp_dir, fname)
                    # Handle duplicate filenames
                    if os.path.exists(dst_path):
                        base, ext = os.path.splitext(fname)
                        dst_path = os.path.join(temp_dir, f"{base}_{uuid.uuid4().hex[:4]}{ext}")

                    shutil.copy2(src_path, dst_path)

                try:
                    return create_folder_zip(temp_dir)
                except Exception as e:
                    print(f"Failed to create zip from temp dir: {e}")
                    return None
            finally:
                # Cleanup handled by OS/garbage eventually, but good to explicit.
                # create_folder_zip returns BytesIO, so we can delete temp_dir
                shutil.rmtree(temp_dir, ignore_errors=True)
