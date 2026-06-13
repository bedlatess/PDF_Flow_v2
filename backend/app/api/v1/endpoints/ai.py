"""
AI endpoints for PDF intelligence
Summarization, Q&A, and structured data extraction
"""
from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.models.user import User
from app.schemas.ai import (
    SummarizeRequest, SummarizeResponse,
    QuestionRequest, QuestionResponse,
    ExtractRequest, ExtractResponse,
    BatchAnalyzeRequest, BatchAnalyzeResponse
)
from app.api.v1.endpoints.auth import get_current_user
from app.services.ai_service import get_gemini_service
from app.services.feature_gate import can_use_pro_feature, require_feature_access
from app.utils.pdf_text_extractor import extract_text_from_pdf
import tempfile
import os

router = APIRouter(prefix="/ai", tags=["ai"])


# ============================================================================
# Dependency: Require Pro or Enterprise User
# ============================================================================

async def require_pro_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user has Pro or Enterprise subscription"""
    if not can_use_pro_feature(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pro or Enterprise subscription required for AI features"
        )
    return current_user


# ============================================================================
# PDF Summarization
# ============================================================================

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_pdf(
    file: UploadFile = File(...),
    length: str = "medium",
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI summary of PDF content

    **Requires**: Pro or Enterprise subscription

    **Parameters**:
    - `file`: PDF file to summarize
    - `length`: Summary length ('short', 'medium', 'long')

    **Returns**: Summary, key points, topics, and metadata
    """
    require_feature_access(db, "ai_analyzer", current_user)
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(tmp_path)

        if not pdf_text or len(pdf_text.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient text from PDF. Make sure the PDF contains text (not just images)."
            )

        # Get AI service
        ai_service = get_gemini_service()

        # Generate summary
        result = await ai_service.summarize_pdf(pdf_text, length)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI summarization failed: {result.get('error', 'Unknown error')}"
            )

        return SummarizeResponse(**result)

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================================
# Q&A
# ============================================================================

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    file: UploadFile = File(...),
    question: str = Form(..., min_length=5, max_length=500),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question about PDF content

    **Requires**: Pro or Enterprise subscription

    **Parameters**:
    - `file`: PDF file to analyze
    - `question`: Question to ask about the document

    **Returns**: Answer, confidence level, and relevant excerpts
    """
    require_feature_access(db, "ai_analyzer", current_user)
    request = QuestionRequest(question=question)
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(tmp_path)

        if not pdf_text or len(pdf_text.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from PDF"
            )

        # Get AI service
        ai_service = get_gemini_service()

        # Ask question
        result = await ai_service.ask_question(pdf_text, request.question)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI Q&A failed: {result.get('error', 'Unknown error')}"
            )

        return QuestionResponse(**result)

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================================
# Structured Data Extraction
# ============================================================================

@router.post("/extract", response_model=ExtractResponse)
async def extract_data(
    file: UploadFile = File(...),
    data_type: str = "general",
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db)
):
    """
    Extract structured data from PDF

    **Requires**: Pro or Enterprise subscription

    **Parameters**:
    - `file`: PDF file to extract from
    - `data_type`: Type of data to extract ('invoice', 'resume', 'contract', 'general')

    **Returns**: Structured data based on document type
    """
    require_feature_access(db, "ai_analyzer", current_user)
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Validate data type
    valid_types = ['invoice', 'resume', 'contract', 'general']
    if data_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data_type. Must be one of: {', '.join(valid_types)}"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(tmp_path)

        if not pdf_text or len(pdf_text.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient text from PDF"
            )

        # Get AI service
        ai_service = get_gemini_service()

        # Extract structured data
        result = await ai_service.extract_structured_data(pdf_text, data_type)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data extraction failed: {result.get('error', 'Unknown error')}"
            )

        return ExtractResponse(**result)

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================================
# Batch Analysis
# ============================================================================

@router.post("/batch-analyze", response_model=BatchAnalyzeResponse)
async def batch_analyze(
    file: UploadFile = File(...),
    operations: List[str] = Form(...),
    current_user: User = Depends(require_pro_user),
    db: Session = Depends(get_db)
):
    """
    Perform multiple AI operations in one request

    **Requires**: Pro or Enterprise subscription

    **Parameters**:
    - `file`: PDF file to analyze
    - `operations`: List of operations ('summarize', 'extract', 'classify')

    **Returns**: Results of all requested operations
    """
    require_feature_access(db, "ai_analyzer", current_user)
    request = BatchAnalyzeRequest(operations=operations)
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(tmp_path)

        if not pdf_text or len(pdf_text.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient text from PDF"
            )

        # Get AI service
        ai_service = get_gemini_service()

        # Perform batch analysis
        result = await ai_service.batch_analyze(pdf_text, request.operations)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch analysis failed: {result.get('error', 'Unknown error')}"
            )

        return BatchAnalyzeResponse(**result)

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
