from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
import os
import subprocess
import sys

MODEL_NAME = "nl_core_news_sm"

app = FastAPI(title="SpaCy Anonymizer")

# Model laden (of downloaden indien nodig)
try:
    nlp = spacy.load(MODEL_NAME)
except OSError:
    subprocess.run([sys.executable, "-m", "spacy", "download", MODEL_NAME], check=True)
    nlp = spacy.load(MODEL_NAME)


class AnonymizeRequest(BaseModel):
    text: str
    mask_style: str = "label"
    keep_length: bool = False
    skip_labels: list[str] = []  # nieuw veld, optioneel


@app.post("/anonymize")
async def anonymize(req: AnonymizeRequest):
    if not req.text:
        raise HTTPException(status_code=400, detail="Text is required.")

    doc = nlp(req.text)
    text = req.text
    entities = []

    for ent in doc.ents:
        if ent.label_ in req.skip_labels:
            continue  # overslaan wat is opgegeven in de request

        replacement = f"[{ent.label_}]" if req.mask_style == "label" else "*" * len(ent.text)
        if req.keep_length and req.mask_style == "label":
            replacement = replacement.ljust(len(ent.text))
        text = text.replace(ent.text, replacement)
        entities.append({
            "start": ent.start_char,
            "end": ent.end_char,
            "label": ent.label_,
            "text": ent.text
        })

    return {"text": text, "entities": entities}


@app.get("/health")
async def health():
    return {"status": "ok"}
