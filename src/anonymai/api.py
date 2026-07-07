from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anonymai.facade import find_pii, scrub, unscrub
from anonymai.models import PIIEntity, PIIType, ScrubResult, ScrubStrategy

app = FastAPI(title="anonymAI")


class TextRequest(BaseModel):
    text: str


class ScrubRequest(BaseModel):
    text: str
    strategy: ScrubStrategy = ScrubStrategy.MOCK
    exclude_pii: list[PIIType] = []


class UnscrubRequest(BaseModel):
    text: str
    mapping: dict[str, str]


@app.post("/pii", response_model=list[PIIEntity])
def find_pii_endpoint(req: TextRequest) -> list[PIIEntity]:
    return find_pii(req.text)


@app.post("/scrub", response_model=ScrubResult)
def scrub_endpoint(req: ScrubRequest) -> ScrubResult:
    return scrub(req.text, strategy=req.strategy, exclude_pii=req.exclude_pii)


@app.post("/unscrub")
def unscrub_endpoint(req: UnscrubRequest) -> dict[str, str]:
    result = ScrubResult(scrubbed_text=req.text, mapping=req.mapping)
    return {"text": unscrub(req.text, result)}


_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
