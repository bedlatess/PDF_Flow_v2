"""
AI service for PDF intelligence using Google Gemini
Provides summarization, Q&A, and structured data extraction
"""
import os
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.core.config import settings

try:
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - imported in app runtime
    Session = Any  # type: ignore

try:
    from app.domains.service_provider.config_store import get_service_provider_runtime_config
except ImportError:  # pragma: no cover - keeps direct module import resilient in partial envs
    get_service_provider_runtime_config = None  # type: ignore


DEFAULT_GEMINI_MODEL = "gemini-1.5-pro"
DEFAULT_GEMINI_TIMEOUT_SECONDS = 60


class GeminiService:
    """Service for interacting with Google Gemini AI"""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        api_base_url: str | None = None,
        timeout_seconds: int | None = None,
        source: str = "env",
    ):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")

        resolved_api_key = (api_key or getattr(settings, 'GEMINI_API_KEY', None) or "").strip()
        if not resolved_api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        configure_kwargs: dict[str, Any] = {"api_key": resolved_api_key}
        if api_base_url:
            configure_kwargs["client_options"] = {"api_endpoint": api_base_url}
        genai.configure(**configure_kwargs)
        self.model_name = (model or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
        self.timeout_seconds = int(timeout_seconds or DEFAULT_GEMINI_TIMEOUT_SECONDS)
        self.source = source
        self.model = genai.GenerativeModel(self.model_name)

    async def summarize_pdf(
        self,
        pdf_text: str,
        summary_length: str = 'medium'
    ) -> Dict[str, Any]:
        """
        Generate a summary of PDF content

        Args:
            pdf_text: Extracted text from PDF
            summary_length: 'short' (2-3 sentences), 'medium' (1 paragraph), 'long' (multiple paragraphs)

        Returns:
            Dict with summary, key points, and metadata
        """
        length_prompts = {
            'short': '2-3 sentences',
            'medium': 'one paragraph (4-6 sentences)',
            'long': 'multiple paragraphs (detailed)'
        }

        prompt = f"""
Summarize the following document in {length_prompts.get(summary_length, 'one paragraph')}.
Then extract 3-5 key points as bullet points.

Document:
{pdf_text[:10000]}  # Limit to first 10k chars to avoid token limits

Respond in JSON format:
{{
    "summary": "your summary here",
    "key_points": ["point 1", "point 2", ...],
    "word_count": estimated_word_count_of_original,
    "topics": ["topic1", "topic2", ...]
}}
"""

        try:
            response = self.model.generate_content(
                prompt,
                request_options={"timeout": self.timeout_seconds},
            )
            result_text = response.text

            # Parse JSON response
            # Remove markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]

            result = json.loads(result_text.strip())

            return {
                'success': True,
                'summary': result.get('summary', ''),
                'key_points': result.get('key_points', []),
                'word_count': result.get('word_count', 0),
                'topics': result.get('topics', []),
                'summary_length': summary_length,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }

    async def ask_question(
        self,
        pdf_text: str,
        question: str,
        context_limit: int = 8000
    ) -> Dict[str, Any]:
        """
        Answer a question about the PDF content

        Args:
            pdf_text: Extracted text from PDF
            question: User's question
            context_limit: Maximum chars of PDF text to use as context

        Returns:
            Dict with answer and confidence
        """
        # Limit context to avoid token limits
        context = pdf_text[:context_limit]

        prompt = f"""
Based on the following document, answer the question. If the answer is not in the document, say "I cannot answer this based on the provided document."

Document:
{context}

Question: {question}

Respond in JSON format:
{{
    "answer": "your detailed answer here",
    "confidence": "high/medium/low",
    "relevant_excerpts": ["excerpt 1", "excerpt 2"],
    "found_in_document": true/false
}}
"""

        try:
            response = self.model.generate_content(
                prompt,
                request_options={"timeout": self.timeout_seconds},
            )
            result_text = response.text

            # Parse JSON response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]

            result = json.loads(result_text.strip())

            return {
                'success': True,
                'question': question,
                'answer': result.get('answer', ''),
                'confidence': result.get('confidence', 'low'),
                'relevant_excerpts': result.get('relevant_excerpts', []),
                'found_in_document': result.get('found_in_document', False),
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }

    async def extract_structured_data(
        self,
        pdf_text: str,
        data_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        Extract structured data from PDF

        Args:
            pdf_text: Extracted text from PDF
            data_type: Type of data to extract ('invoice', 'resume', 'contract', 'general')

        Returns:
            Dict with structured data
        """
        type_prompts = {
            'invoice': """
Extract invoice information:
- Invoice number
- Date
- Vendor name and address
- Customer name and address
- Line items (description, quantity, price)
- Subtotal, tax, total
- Payment terms
""",
            'resume': """
Extract resume information:
- Name
- Contact information
- Education (schools, degrees, years)
- Work experience (company, position, dates, responsibilities)
- Skills
- Certifications
""",
            'contract': """
Extract contract information:
- Contract title
- Parties involved
- Effective date and term
- Key obligations
- Payment terms
- Termination clauses
""",
            'general': """
Extract key structured information from the document including:
- Document type
- Main entities (people, organizations, locations)
- Dates
- Numerical data
- Key terms and definitions
"""
        }

        extraction_prompt = type_prompts.get(data_type, type_prompts['general'])

        prompt = f"""
Analyze the following document and extract structured data.

{extraction_prompt}

Document:
{pdf_text[:10000]}

Respond in JSON format with the extracted data. Use null for missing fields.
"""

        try:
            response = self.model.generate_content(
                prompt,
                request_options={"timeout": self.timeout_seconds},
            )
            result_text = response.text

            # Parse JSON response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]

            result = json.loads(result_text.strip())

            return {
                'success': True,
                'data_type': data_type,
                'extracted_data': result,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'data_type': data_type,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }

    async def batch_analyze(
        self,
        pdf_text: str,
        operations: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform multiple AI operations in one call

        Args:
            pdf_text: Extracted text from PDF
            operations: List of operations to perform ['summarize', 'extract', 'classify']

        Returns:
            Dict with results of all operations
        """
        if operations is None:
            operations = ['summarize', 'extract']

        results = {}

        if 'summarize' in operations:
            results['summary'] = await self.summarize_pdf(pdf_text, 'medium')

        if 'extract' in operations:
            results['structured_data'] = await self.extract_structured_data(pdf_text, 'general')

        if 'classify' in operations:
            results['classification'] = await self._classify_document(pdf_text)

        return {
            'success': True,
            'operations': operations,
            'results': results,
            'generated_at': datetime.utcnow().isoformat()
        }

    async def _classify_document(self, pdf_text: str) -> Dict[str, Any]:
        """Internal method to classify document type"""
        prompt = f"""
Classify the following document into one of these categories:
- invoice
- receipt
- contract
- resume
- report
- letter
- form
- manual
- other

Also provide confidence level (high/medium/low) and reasoning.

Document:
{pdf_text[:2000]}

Respond in JSON format:
{{
    "category": "category_name",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation"
}}
"""

        try:
            response = self.model.generate_content(
                prompt,
                request_options={"timeout": self.timeout_seconds},
            )
            result_text = response.text

            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]

            result = json.loads(result_text.strip())
            return {
                'success': True,
                **result
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance. The key includes runtime config so admin changes take
# effect without a backend restart.
_gemini_service: Optional[GeminiService] = None
_gemini_service_cache_key: Optional[tuple[str, str, str, int, str]] = None


def _gemini_runtime_from_db(db: Session | None) -> dict[str, Any] | None:
    if db is None or get_service_provider_runtime_config is None:
        return None
    runtime = get_service_provider_runtime_config(db, "ai", "google_gemini")
    if not runtime:
        return None
    public_config = runtime.get("public_config") or {}
    secrets = runtime.get("secrets") or {}
    api_key = str(secrets.get("api_key") or "").strip()
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "api_base_url": str(public_config.get("api_base_url") or "").strip() or None,
        "model": str(public_config.get("model") or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL,
        "timeout_seconds": int(public_config.get("timeout_seconds") or DEFAULT_GEMINI_TIMEOUT_SECONDS),
        "source": "db",
    }


def get_gemini_service(db: Session | None = None) -> GeminiService:
    """Get or create Gemini service singleton"""
    global _gemini_service, _gemini_service_cache_key
    runtime = _gemini_runtime_from_db(db) or {
        "api_key": getattr(settings, "GEMINI_API_KEY", None),
        "api_base_url": None,
        "model": DEFAULT_GEMINI_MODEL,
        "timeout_seconds": DEFAULT_GEMINI_TIMEOUT_SECONDS,
        "source": "env",
    }
    cache_key = (
        str(runtime.get("api_key") or ""),
        str(runtime.get("api_base_url") or ""),
        str(runtime.get("model") or DEFAULT_GEMINI_MODEL),
        int(runtime.get("timeout_seconds") or DEFAULT_GEMINI_TIMEOUT_SECONDS),
        str(runtime.get("source") or "env"),
    )
    if _gemini_service is None or _gemini_service_cache_key != cache_key:
        _gemini_service = GeminiService(**runtime)
        _gemini_service_cache_key = cache_key
    return _gemini_service
