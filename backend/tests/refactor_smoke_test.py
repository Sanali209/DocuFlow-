import sys
import os
from sqlalchemy.orm import Session

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.infrastructure.database.models import Base, DocumentDB
from src.infrastructure.database.repositories import SQLDocumentRepository
from src.application.services.document_service import DocumentService
from src.domain.models import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock Database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_refactor_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_backend_refactor():
    print("--- Starting Backend Refactor Smoke Test ---")
    
    # 1. Setup DB
    print("1. Setting up test database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 2. Setup Service
        print("2. Initializing Repository and Service...")
        repo = SQLDocumentRepository(db)
        service = DocumentService(repo)
        
        # 3. Create a Document
        print("3. Testing Document Creation...")
        new_doc = Document(name="Refactor Test Doc", description="Verifying Clean Architecture")
        created_doc = service.create_document(new_doc)
        print(f"Created Document: {created_doc.name} (ID: {created_doc.id})")
        assert created_doc.id is not None
        assert created_doc.name == "Refactor Test Doc"
        
        # 4. List Documents
        print("4. Testing Document Listing...")
        docs = service.list_documents()
        print(f"Found {len(docs)} documents.")
        assert len(docs) == 1
        
        # 5. Get Document
        print("5. Testing Get Document...")
        fetched_doc = service.get_document(created_doc.id)
        assert fetched_doc.name == "Refactor Test Doc"
        print("Fetched Document matches.")
        
        # 6. Delete Document
        print("6. Testing Document Deletion...")
        success = service.delete_document(created_doc.id)
        assert success is True
        assert len(service.list_documents()) == 0
        print("Deletion successful.")
        
        print("\n[SUCCESS] Backend Refactor Smoke Test passed!")
        
    except AssertionError as e:
        print(f"\n[FAILURE] Test assertion failed.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
        if os.path.exists("./test_refactor_app.db"):
            os.remove("./test_refactor_app.db")

if __name__ == "__main__":
    test_backend_refactor()
