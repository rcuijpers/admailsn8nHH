# Deploy to Render (Docker)

Dit project draait je spaCy-anonymizer als **Web Service** op Render, met optionele API-key bescherming.

## Bestanden
- `app.py` – FastAPI-app (met header `X-Api-Key` ondersteuning)
- `requirements.txt` – versies compatibel met spaCy 3.2.x (FastAPI 0.95.x, Pydantic 1.10.x)
- `Dockerfile` – Python 3.10 slim; pre-download NL model
- `render.yaml` – Render blueprint (Web Service, health check, env vars)

## Deploy-stappen
1. Maak een nieuwe GitHub repo en commit deze vier bestanden.
2. Ga naar Render → **New** → **Blueprint** → kies je repo met `render.yaml`.
   - Of: **New** → **Web Service** → **Build from Dockerfile** (werkt ook).
3. Laat plan op **Free** (of kies hoger).
4. Wacht tot build klaar is; Render toont dan de URL, bv. `https://spacy-anonymizer.onrender.com`.
5. Test: `GET /health` → `{"status":"ok"}`

### Authenticatie
- In `render.yaml` wordt automatisch een `API_KEY` aangemaakt.
- Stuur in elke request de header: `X-Api-Key: <waarde-uit-Render>`
  - In Render: service → **Environment** → zie de waarde van `API_KEY`.

### n8n configuratie
HTTP Request node:
- Method: `POST`
- URL: `https://<jouw-render-host>/anonymize`
- Headers:
  - `Content-Type: application/json`
  - `X-Api-Key: <Render API_KEY>`
- Body (JSON):
```json
{
  "text": "Hoi, ik ben Jan Jansen. Bel 06-12345678 of mail jan@example.com.",
  "mask_style": "label",
  "keep_length": false
}
```

### Lokale test (zonder Render)
```bash
docker build -t spacy-anonymizer .
docker run -e PORT=10000 -p 10000:10000 spacy-anonymizer
# Open: http://localhost:10000/health
```

### Notities
- Render gebruikt env var `$PORT`; de container luistert daarop.
- `spacy==3.2.6` + `fastapi==0.95.2` + `pydantic==1.10.13` zijn compatibel.
- Ander model? Zet `SPACY_MODEL=nl_core_news_md` (kan build langer maken).
