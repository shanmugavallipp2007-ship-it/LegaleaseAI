from __future__ import annotations

from dataclasses import dataclass

from google import genai
from google.genai import types

from backend.config import Settings


SYSTEM_INSTRUCTION = """
You are LegalEase, an AI assistant that drafts
professional legal-document templates.

Create clear, structured and editable legal
document drafts based only on the information
provided by the user.

Do not invent missing facts.

When information is missing, use placeholders
such as [NAME], [DATE], [AMOUNT], [ADDRESS],
[PHONE NUMBER], or [EMAIL].

Use professional legal-document formatting.

Include suitable headings, clauses and
signature sections.

Do not claim that the generated document is
legal advice.

The generated document must be treated as a
draft and reviewed by a qualified legal
professional before use.
""".strip()


@dataclass
class GenerationResult:
    text: str
    model: str
    demo_mode: bool


class GeminiDocumentGenerator:

    def __init__(
        self,
        settings: Settings
    ):

        self.settings = settings
        self.client = None

        if (
            not settings.demo_mode
            and settings.gemini_api_key
        ):
            self.client = genai.Client(
                api_key=settings.gemini_api_key
            )

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        dates: str
    ) -> GenerationResult:

        if self.settings.demo_mode:

            return GenerationResult(
                text=self._demo_document(
                    document_type,
                    parties,
                    terms,
                    dates
                ),
                model="demo",
                demo_mode=True
            )

        if not self.settings.gemini_api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add it to .env or enable "
                "DEMO_MODE=true."
            )

        if self.client is None:

            self.client = genai.Client(
                api_key=self.settings.gemini_api_key
            )

        prompt = f"""
Document type:
{document_type}

Parties:
{parties}

Terms and conditions:
{terms}

Effective date / dates:
{dates}

Draft the requested legal document now.
""".strip()

        try:

            response = (
                self.client.models.generate_content(
                    model=self.settings.gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            SYSTEM_INSTRUCTION
                        ),
                        max_output_tokens=12000
                    )
                )
            )

        except Exception as exc:

            raise RuntimeError(
                f"Gemini generation failed: {exc}"
            ) from exc

        text = getattr(
            response,
            "text",
            None
        )

        if not text or not text.strip():

            raise RuntimeError(
                "Gemini returned an empty document."
            )

        return GenerationResult(
            text=self.clean_model_output(text),
            model=self.settings.gemini_model,
            demo_mode=False
        )

    @staticmethod
    def clean_model_output(
        text: str
    ) -> str:

        text = text.replace(
            "```text",
            ""
        )

        text = text.replace(
            "```markdown",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        return text.replace(
            "\r\n",
            "\n"
        ).strip()

    @staticmethod
    def _demo_document(
        document_type: str,
        parties: str,
        terms: str,
        dates: str
    ) -> str:

        return f"""
{document_type.upper()}

EFFECTIVE DATE
{dates}


PARTIES
{parties}


PURPOSE

This document records the terms and
conditions agreed between the parties.


AGREED TERMS

{terms}


REPRESENTATIONS

Each party confirms that the information
provided for this draft is accurate to the
best of their knowledge.


TERM AND TERMINATION

This agreement begins on the effective
date stated above and continues according
to the agreed terms.


GOVERNING LAW

[INSERT APPLICABLE STATE / COUNTRY]


ENTIRE AGREEMENT

This document contains the terms supplied
for this draft and may be amended only by
written agreement of the parties.


SIGNATURES


Party 1

Signature: __________________________

Name: [NAME]

Date: ______________________________


Party 2

Signature: __________________________

Name: [NAME]

Date: ______________________________


DISCLAIMER

This document is an AI-generated draft
for informational and document-preparation
purposes. It is not legal advice and
should be reviewed by a qualified legal
professional before use.
""".strip()