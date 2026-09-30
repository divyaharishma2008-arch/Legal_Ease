from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ai_core.gemini_generator import GeminiDocumentGenerator

router = APIRouter()

# Created once at import time and shared by all requests.
generator = GeminiDocumentGenerator()


class DocumentRequest(BaseModel):
    """Request body for POST /generate. All fields are required strings."""

    document_type: str = Field(..., min_length=2, max_length=120)   # e.g. "Rental Agreement"
    parties: str = Field(..., min_length=2, max_length=4000)        # People / organisations involved
    terms: str = Field(..., min_length=2, max_length=8000)          # Key terms and conditions
    dates: str = Field(..., min_length=2, max_length=200)           # Relevant dates / duration

    @field_validator("document_type", "parties", "terms", "dates")
    @classmethod
    def clean_input(cls, value: str) -> str:
        """Trim whitespace and reject values that are empty after trimming."""
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value


@router.post("/generate")
def generate_document(request: DocumentRequest):
    """
    Generate a legal document from the supplied details.

    Args:
        request (DocumentRequest): document_type, parties, terms and dates.

    Returns:
        dict: {"success": True, "document_type": str, "content": str}

    Raises:
        HTTPException 400: The generator rejected the input (ValueError).
        HTTPException 503: The AI service is unavailable or not configured
                           (RuntimeError).
        HTTPException 500: Any other unexpected failure.
    """
    try:
        text = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            dates=request.dates,
        )
        return {
            "success": True,
            "document_type": request.document_type,
            "content": text,
        }
    except ValueError as exc:            # Bad input -> client error
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:          # AI service problem -> unavailable
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:             # Anything else -> server error
        raise HTTPException(
            status_code=500,
            detail=f"Document generation failed: {exc}",
        ) from exc
