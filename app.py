# app.py (Render-ready, Python 3.10+ compatible)
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os, re, spacy

# Optional API key protection (set env API_KEY to enable)
API_KEY = os.getenv("API_KEY")

MODEL_NAME = os.getenv("SPACY_MODEL", "nl_core_news_sm")
try:
    nlp = spacy.load(MODEL_NAME)
except OSError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "spacy", "download", MODEL_NAME], check=True)
    nlp = spacy.load(MODEL_NAME)

app = FastAPI(title="spaCy Anonymizer (NL)")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{6,}\d")
DEFAULT_LABELS = {"PERSON", "ORG", "GPE", "LOC", "DATE", "TIME", "MONEY", "CARDINAL"}

class AnonRequest(BaseModel):
    text: str
    labels: Optional[List[str]] = None
    mask_style: str = "label"      # "label" | "stars" | "token"
    keep_length: bool = False

def mask_for(label: str, length: int, style: str, keep_length: bool):
    if style == "stars" or keep_length:
        return "*" * length
    if style == "token":
        return "[REDACTED]"
    return f"[{label}]"

def require_key(x_api_key: Optional[str]):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/anonymize")
def anonymize(req: AnonRequest, x_api_key: Optional[str] = Header(default=None)):
    require_key(x_api_key)

    doc = nlp(req.text)
    targets = set(req.labels) if req.labels else DEFAULT_LABELS

    spans = []
    # Regex first → priority over NER overlaps
    for m in EMAIL_RE.finditer(req.text):
        spans.append((m.start(), m.end(), "EMAIL"))
    for m in PHONE_RE.finditer(req.text):
        spans.append((m.start(), m.end(), "PHONE"))

    for ent in doc.ents:
        if ent.label_ in targets:
            spans.append((ent.start_char, ent.end_char, ent.label_))

    spans.sort(key=lambda x: (x[0], -(x[1]-x[0])))
    cleaned = []
    last = 0
    taken = []
    for s, e, l in spans:
        if s < last:
            continue
        cleaned.append(req.text[last:s])
        cleaned.append(mask_for(l, e - s, req.mask_style, req.keep_length))
        last = e
        taken.append({"start": s, "end": e, "label": l, "text": req.text[s:e]})
    cleaned.append(req.text[last:])

    return {"text": "".join(cleaned), "entities": taken}
