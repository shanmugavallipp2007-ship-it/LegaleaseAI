from fastapi import APIRouter, HTTPException

from ai_core.gemini_generator import (
    GeminiDocumentGenerator
)

from backend.config import get_settings

from backend.schemas import (
    DocumentRequest,
    DocumentResponse
)


router = APIRouter(tags=["documents"])


@router.post(
    "/generate",
    response_model=DocumentResponse
)
def generate_legal_document(
    request: DocumentRequest
) -> DocumentResponse:

    settings = get_settings()

    generator = GeminiDocumentGenerator(
        settings
    )

    try:
        result = generator.generate_document(
            request.document_type,
            request.parties,
            request.terms,
            request.dates
        )

    except RuntimeError as exc:

        message = str(exc)

        if "GEMINI_API_KEY" in message:
            status_code = 503
        else:
            status_code = 502

        raise HTTPException(
            status_code=status_code,
            detail=message
        ) from exc

    return DocumentResponse(
        document=result.text,
        model=result.model,
        demo_mode=result.demo_mode
    )