from fastapi import FastAPI
from pydantic import BaseModel
import spacy
import re

app = FastAPI()

MODEL_NAME = "nl_core_news_lg"
nlp = spacy.load(MODEL_NAME)

class AnonymizeRequest(BaseModel):
    text: str
    mask_style: str = "label"
    keep_length: bool = False
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
