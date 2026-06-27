from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api")


@router.post("/analyze")
async def analyze(
    repository: UploadFile = File(...),
    bug_report: str = Form(...),
    error_log: str = Form("")
):

    if not repository.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Repository must be a ZIP file."
        )

    result = AnalysisService.analyze(
        await repository.read(),
        bug_report,
        error_log
    )

    return result