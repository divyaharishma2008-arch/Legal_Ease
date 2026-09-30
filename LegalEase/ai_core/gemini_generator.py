import os
from typing import Optional

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:  # Helpful message if dependencies were not installed.
    genai = None

load_dotenv()


class GeminiDocumentGenerator:
    """
    Gemini-backed legal document generator.

    The PDF specification names Gemini 1.5 Pro. Because model availability can
    change, the model is configurable through GEMINI_MODEL in .env.
    """

    def __init__(self, model: Optional[str] = None):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro").strip()
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

        if not self.demo_mode and not self.api_key:
            self.client = None
        elif genai is not None and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        dates: str,
    ) -> str:
        if self.demo_mode:
            return self._demo_document(document_type, parties, terms, dates)

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Add it to .env, "
                "or set DEMO_MODE=true for local UI/API testing."
            )

        if self.client is None:
            raise RuntimeError(
                "The Gemini SDK is unavailable. Run: pip install -r requirements.txt"
            )

        prompt = self._build_prompt(document_type, parties, terms, dates)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Gemini request failed. Check GEMINI_API_KEY and GEMINI_MODEL. "
                f"Provider error: {exc}"
            ) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty document.")

        return text.strip()

    @staticmethod
    def _build_prompt(
        document_type: str,
        parties: str,
        terms: str,
        dates: str,
    ) -> str:
        return f"""
You are a legal-document drafting assistant.

Create a structured draft for the requested document using ONLY the facts
provided by the user. Do not invent names, dates, addresses, money amounts,
jurisdiction, statutes, registration numbers, or other material facts.

DOCUMENT TYPE:
{document_type}

PARTIES:
{parties}

TERMS AND CONDITIONS:
{terms}

EFFECTIVE DATE:
{dates}

Return a professional, editable draft with:
1. A clear title.
2. Parties and effective date.
3. Recitals/background when appropriate.
4. Clearly numbered sections and clauses.
5. The supplied terms incorporated into appropriate sections.
6. Signature blocks for relevant parties.
7. A short "Important Notice" at the end saying this is an AI-generated
   draft and should be reviewed by a qualified legal professional.

Do not use markdown tables. Use plain text headings and numbered clauses so
the output can be exported cleanly to TXT, DOCX, and PDF.

Do not claim that the document is legally valid in a particular jurisdiction
unless the user explicitly supplied that jurisdiction and the statement is
supported by the supplied information.
""".strip()

    @staticmethod
    def _demo_document(document_type: str, parties: str, terms: str, dates: str) -> str:
        term_items = [x.strip() for x in terms.split(";") if x.strip()]
        terms_block = "\n".join(
            f"{i}. {item}" for i, item in enumerate(term_items, start=1)
        ) or "1. No specific terms supplied."

        return f"""{document_type.upper()}

DRAFT DOCUMENT

1. PARTIES
{parties}

2. EFFECTIVE DATE
{dates}

3. PURPOSE
This draft records the general agreement described by the parties for the
requested document type: {document_type}.

4. TERMS AND CONDITIONS
{terms_block}

5. GENERAL PROVISIONS
The parties should review this draft and add any required jurisdiction,
notices, governing-law, dispute-resolution, payment, confidentiality,
termination, or other provisions before use.

6. SIGNATURES

Party 1: ______________________________
Name: __________________________________
Date: __________________________________

Party 2: ______________________________
Name: __________________________________
Date: __________________________________

IMPORTANT NOTICE
This is a demonstration/AI-generated draft. It is not legal advice and should
be reviewed by a qualified legal professional before signing or relying on it.
"""
