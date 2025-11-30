"""
Chat API endpoints.
Main interface for the planning intelligence agent.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_rag_engine, rate_limit_dependency
from app.core.security import sanitize_input
from app.models.chat import ChatRequest, ChatResponse
from app.models.analytics import FeedbackRequest, FeedbackResponse
from app.services.rag.engine import RAGEngine
from app.services.supabase import supabase_service

router = APIRouter()


@router.post(
    "/query",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit_dependency)],
)
async def query(
    request: ChatRequest,
    rag_engine: RAGEngine = Depends(get_rag_engine),
) -> ChatResponse:
    """
    Submit a planning question and get an AI-generated response.

    This endpoint:
    1. Retrieves relevant planning documents
    2. Generates a cited response using GPT-4o
    3. Returns suggested follow-up questions

    **Example Request:**
    ```json
    {
        "message": "Can I add a rear extension in Hampstead?",
        "session_id": "optional-session-id",
        "borough": "Camden"
    }
    ```

    **Example Response:**
    ```json
    {
        "session_id": "session_abc123",
        "message": "In Hampstead, rear extensions are generally...",
        "citations": [...],
        "suggested_questions": [...],
        "detected_borough": "Camden"
    }
    ```
    """
    try:
        # Sanitize input
        request.message = sanitize_input(request.message)

        # Process through RAG pipeline
        response = await rag_engine.process_query(request)

        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your query. Please try again.",
        )


@router.post(
    "/query/stream",
    dependencies=[Depends(rate_limit_dependency)],
)
async def query_stream(
    request: ChatRequest,
    rag_engine: RAGEngine = Depends(get_rag_engine),
):
    """
    Submit a planning question and get a streaming response.

    Uses Server-Sent Events (SSE) to stream the response as it's generated.

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/query/stream');
    eventSource.onmessage = (event) => {
        console.log(event.data);
    };
    ```
    """
    try:
        request.message = sanitize_input(request.message)

        async def event_generator():
            try:
                async for chunk in rag_engine.process_streaming_query(request):
                    yield {"event": "message", "data": chunk}
                yield {"event": "done", "data": ""}
            except Exception as e:
                yield {"event": "error", "data": str(e)}

        return EventSourceResponse(event_generator())

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
)
async def submit_feedback(
    request: FeedbackRequest,
) -> FeedbackResponse:
    """
    Submit feedback for a query response.

    Feedback helps improve response quality.

    **Example Request:**
    ```json
    {
        "query_id": "uuid-of-query",
        "feedback": "positive",
        "comment": "Very helpful response!"
    }
    ```
    """
    try:
        await supabase_service.update_query_feedback(
            query_id=request.query_id,
            feedback=request.feedback,
            comment=request.comment,
        )

        return FeedbackResponse(
            success=True,
            message="Thank you for your feedback!",
        )

    except Exception as e:
        return FeedbackResponse(
            success=False,
            message="Failed to record feedback. Please try again.",
        )


@router.get("/boroughs")
async def get_boroughs():
    """
    Get list of supported boroughs.

    Returns the boroughs covered by the planning intelligence agent.
    """
    return {
        "boroughs": [
            {"name": "Camden", "description": "Includes Hampstead, Belsize Park, Primrose Hill"},
            {"name": "Barnet", "description": "Includes Finchley, Golders Green, Hendon"},
            {"name": "Westminster", "description": "Includes Marylebone, Mayfair, Fitzrovia"},
            {"name": "Brent", "description": "Includes Wembley, Willesden, Kilburn"},
            {"name": "Haringey", "description": "Includes Highgate, Crouch End, Muswell Hill"},
        ]
    }


@router.get("/topics")
async def get_topics():
    """
    Get list of common planning topics.

    Returns topics the agent can help with.
    """
    return {
        "topics": [
            {
                "name": "Extensions",
                "description": "Rear, side, and wrap-around extensions",
                "example_questions": [
                    "How far can I extend to the rear?",
                    "Do I need planning for a side extension?",
                ],
            },
            {
                "name": "Loft Conversions",
                "description": "Dormers, roof extensions, and mansard roofs",
                "example_questions": [
                    "Can I add a dormer on the front?",
                    "What are the rules for loft conversions?",
                ],
            },
            {
                "name": "Basements",
                "description": "Basement excavations and subterranean development",
                "example_questions": [
                    "Can I dig a basement under my garden?",
                    "What are the basement depth limits?",
                ],
            },
            {
                "name": "Conservation Areas",
                "description": "Rules for properties in conservation areas",
                "example_questions": [
                    "Is my property in a conservation area?",
                    "What restrictions apply in conservation areas?",
                ],
            },
            {
                "name": "Permitted Development",
                "description": "What you can do without planning permission",
                "example_questions": [
                    "What are my permitted development rights?",
                    "Has Article 4 removed my PD rights?",
                ],
            },
        ]
    }
