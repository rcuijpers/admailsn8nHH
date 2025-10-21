<<<<<<< HEAD
from fastapi import FastAPI
from pydantic import BaseModel
import spacy
import re

app = FastAPI()

MODEL_NAME = "nl_core_news_lg"
nlp = spacy.load(MODEL_NAME)
=======
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os, re, spacy

API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("SPACY_MODEL", "nl_core_news_sm")

# Model is installed at build time via requirements.txt
nlp = spacy.load(MODEL_NAME)

app = FastAPI(title="spaCy Anonymizer (NL)")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{6,}\d")
DEFAULT_LABELS = {"PERSON", "ORG", "GPE", "LOC", "DATE", "TIME", "MONEY", "CARDINAL"}
>>>>>>> parent of 4832bff (add filtering by api call)

class AnonRequest(BaseModel):
    text: str
    labels: Optional[List[str]] = None
    mask_style: str = "label"
    keep_length: bool = False
<<<<<<< HEAD
    skip_labels: list[str] = []

@app.get("/")
def root():
    return {"message": "SpaCy Anonymizer API running 🚀"}

@app.post("/anonymize")
async def anonymize(request: AnonymizeRequest):
    text = request.text
    mask_style = request.mask_style
    keep_length = request.keep_length
    skip_labels = set(request.skip_labels)

    doc = nlp(text)

    # Extra herkenning: straatnamen (straat, laan, weg, plein, dreef)
    street_pattern = re.compile(r"\b[A-Z][a-z]+(?:straat|laan|weg|plein|dreef)\b")
    extra_entities = [
        {"start": m.start(), "end": m.end(), "label": "STREET", "text": m.group(0)}
        for m in street_pattern.finditer(text)
    ]

    # Combineer SpaCy + regex entiteiten
    entities = [
        {"start": ent.start_char, "end": ent.end_char, "label": ent.label_, "text": ent.text}
        for ent in doc.ents
        if ent.label_ not in skip_labels
    ] + extra_entities

    # Sorteer op startpositie
    entities.sort(key=lambda e: e["start"])

    # Tekst anonimiseren
    anonymized_text = text
    offset = 0
    for ent in entities:
        if ent["label"] in skip_labels:
            continue

        start, end = ent["start"] + offset, ent["end"] + offset
        original = ent["text"]

        if mask_style == "stars":
            replacement = "*" * len(original) if keep_length else "*****"
        else:
            replacement = f"[{ent['label']}]"
            if keep_length:
                pad = max(0, len(original) - len(replacement))
                replacement += " " * pad

        anonymized_text = anonymized_text[:start] + replacement + anonymized_text[end:]
        offset += len(replacement) - len(original)

    return {"text": anonymized_text, "entities": entities}
=======

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
>>>>>>> parent of 4832bff (add filtering by api call)
