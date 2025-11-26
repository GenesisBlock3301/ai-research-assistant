import logging
import shutil
import tempfile
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db, User, Document
from app.services import IngestionService
from app.schemas import DocumentRead
from app.utils import get_current_user


logger = logging.getLogger(__name__)

document_router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit


@document_router.post("/upload", response_model=DocumentRead)
def upload_pdf(
        file: UploadFile = File(...),
        title: str = "",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid file type. Only PDF allowed.")
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large. Max 10 MB allowed.")

        ingestion_service = IngestionService(db)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        owner_id = current_user.id
        doc = ingestion_service.ingest_pdf(tmp_file_path, title or file.filename, owner_id)
        return doc
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@document_router.get("/list", response_model=List[DocumentRead], status_code=status.HTTP_200_OK)
def document_lists(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        document_list = (
            db.query(Document)
            .filter(Document.owner_id == current_user.id)
            .order_by(Document.created_at.desc())
            .all()
        )
        return document_list

    except Exception as e:
        logger.error(f"Error while listing documents for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving your documents."
        )