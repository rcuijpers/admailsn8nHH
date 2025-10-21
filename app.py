from fastapi import FastAPI, Request
from pydantic import BaseModel
import spacy
import re
import os
import subprocess

app = FastAPI()

MODEL_NAME = "nl_core_news_lg"

# Download het model als het nog niet aanwezig is
try:
    nlp = spacy.load(MODEL_NAME)
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", MODEL_NAME], check=True)
    nlp = spacy.load(MODEL_NAME)


class AnonymizeRequest(BaseModel):
    text: str
    mask_style: str = "label"        # "label" of "stars"
    keep_length: bool = False
    skip_labels: list[str] = []      # lijst met labels om over te slaan


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

    # Extra entiteiten detecteren via regex (straatnamen, laan, weg, plein)
    extra_entities = []
    street_pattern = re.compile(r"\b[A-Z][a-z]+(?:straat|laan|weg|plein)\b")
    for match in street_pattern.finditer(text):
        extra_entities.append({
            "start": match.start(),
            "end": match.end(),
            "label": "STREET",
            "text": match.group(0)
        })

    # Combineer originele SpaCy entiteiten met regex-gevonden straten
    entities = [
        {"start": ent.start_char, "end": ent.end_char, "label": ent.label_, "text": ent.text}
        for ent in doc.ents
        if ent.label_ not in skip_labels
    ] + extra_entities

    # Sorteer entiteiten op startpositie (voor consistentie)
    entities.sort(key=lambda e: e["start"])

    anonymized_text = text
    offset = 0
    for ent in entities:
        start, end = ent["start"] + offset, ent["end"] + offset
        original = ent["text"]

        # Skip als ent.label_ staat in skip_labels
        if ent["label"] in skip_labels:
            continue

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
