"""FastAPI application for the SpendGuard Phase 1 baseline."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from spendguard.agent import AgentConfigurationError, AgentExecutionError, OpenAIAnalyzer
from spendguard.models import AnalysisResult, AnalyzeRequest


class Analyzer(Protocol):
    """Minimal analyzer interface for the API boundary."""

    async def analyze(self, question: str) -> AnalysisResult: ...


STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.analyzer = OpenAIAnalyzer()
    yield


app = FastAPI(title="SpendGuard", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    """Serve the Phase 1 UI."""

    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/analyze", response_model=AnalysisResult)
async def analyze(payload: AnalyzeRequest, request: Request) -> AnalysisResult:
    """Analyze a natural-language question with the configured single agent."""

    analyzer: Analyzer = request.app.state.analyzer
    try:
        return await analyzer.analyze(payload.question)
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AgentExecutionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
