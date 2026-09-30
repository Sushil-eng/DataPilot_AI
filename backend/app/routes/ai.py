"""
AI routes — POST /api/ai/analyze

Receives a natural-language prompt, runs it through the LLM service,
and returns a validated, structured analysis plan with a dynamic
dataset schema.
"""

import logging
from fastapi import APIRouter, HTTPException

from ..ai.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalyzeResponseData,
    build_dynamic_schema,
)
from ..ai.llm_service import (
    LLMService,
    LLMConfigError,
    LLMAPIError,
    LLMParsingError,
    LLMValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_prompt(request: AnalyzeRequest):
    """
    Analyse a user's natural-language data request and return a
    structured AI data-collection plan with a dynamic dataset schema.

    This does NOT perform any web scraping or real data collection.
    It only produces the plan and schema.
    """
    try:
        service = LLMService()
        result = await service.analyze(request.prompt)

        # Build the dynamic schema from the AI output
        dynamic_schema = build_dynamic_schema(result)

        response_data = AnalyzeResponseData(
            requirements=result,
            dynamic_schema=dynamic_schema,
            filters=result.filters,
        )

        return AnalyzeResponse(success=True, data=response_data)

    except LLMConfigError as exc:
        logger.error("LLM config error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    except LLMAPIError as exc:
        logger.error("LLM API error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    except LLMParsingError as exc:
        logger.error("LLM parsing error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    except LLMValidationError as exc:
        logger.error("LLM validation error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    except Exception as exc:
        logger.exception("Unexpected error in /api/ai/analyze")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {type(exc).__name__}",
        )
