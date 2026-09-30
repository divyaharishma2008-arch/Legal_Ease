# LegalEase — AI-Powered Legal Document Generator

LegalEase follows the project specification: Streamlit frontend, FastAPI
backend, Gemini-powered generation, editable preview, and TXT/DOCX/PDF export.

## 1. Project structure

```text
LegalEase/
├── main.py
├── routes.py
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile
├── README.md
├── ai_core/
│   ├── __init__.py
│   └── gemini_generator.py
├── utils/
│   ├── __init__.py
│   └── exporters.py
├── assets/
│   └── logo.png
└── tests/
    └── test_api.py
```

## 2. VS Code setup

Open the `LegalEase` folder in VS Code.

Open **Terminal → New Terminal**.

Create a virtual environment:

### Windows
```powershell
py -m venv .venv
.venv\Scripts\activate
```

If `py` does not work:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Upgrade pip:
```powershell
python -m pip install --upgrade pip
```

Install dependencies:
```powershell
pip install -r requirements.txt
```

## 3. Configure Gemini

Copy `.env.example` and rename the copy to:

```text
.env
```

Put your Gemini API key into:

```text
GEMINI_API_KEY=your_real_key_here
```

For real AI generation:

```text
DEMO_MODE=false
```

The specification names `gemini-1.5-pro`. The model is configurable because
Google model availability can change. If your API account does not provide
that model, change `GEMINI_MODEL` to a model currently available to your key.

## 4. Test without an API key

For a first local test, use:

```text
DEMO_MODE=true
```

This lets you verify the FastAPI endpoint, Streamlit UI, editing, and all
three download formats without consuming an API request.

## 5. Run the backend

Keep the first VS Code terminal open:

```powershell
uvicorn main:app --reload
```

You should see the server at:

```text
http://127.0.0.1:8000
```

Test:

```text
http://127.0.0.1:8000/health
```

FastAPI's interactive API page is:

```text
http://127.0.0.1:8000/docs
```

## 6. Run the Streamlit frontend

Open a **second** VS Code terminal.

Activate the environment again if necessary:

```powershell
.venv\Scripts\activate
```

Run:

```powershell
streamlit run app.py
```

Streamlit will show a local URL, normally:

```text
http://localhost:8501
```

Open that URL in Chrome.

## 7. Test the application

Use example values:

Document Type:
```text
Freelance Work Contract
```

Parties:
```text
Jane Doe (Service Provider), TechNova Inc. (Client)
```

Terms:
```text
Payment within 30 days; Confidentiality must be maintained; Either party may terminate with 15 days notice
```

Effective Date:
```text
10/04/2025
```

Click **Generate Document**.

Then verify:

1. Generated text appears in the preview.
2. Text can be edited.
3. TXT downloads successfully.
4. DOCX opens in Microsoft Word.
5. PDF opens normally.
6. Logo/footer appear in DOCX/PDF.

## 8. API test

With the backend running, open:

```text
http://127.0.0.1:8000/docs
```

Choose `POST /generate`, click **Try it out**, and use:

```json
{
  "document_type": "Freelance Work Contract",
  "parties": "Jane Doe (Service Provider), TechNova Inc. (Client)",
  "terms": "Payment within 30 days; Confidentiality must be maintained; Either party may terminate with 15 days notice",
  "dates": "10/04/2025"
}
```

## 9. Automated tests

Run:

```powershell
pytest -q
```

The tests use demo mode so they do not require a Gemini API key.

## 10. Important notes

- Do not put your real Gemini API key directly into Python files.
- Do not commit `.env` to Git.
- The generated output is an AI-generated legal draft, not legal advice.
- Review the document for jurisdiction-specific requirements before signing.
- The frontend sends requests to FastAPI; FastAPI sends generation requests to Gemini.
- DOCX and PDF are generated locally after the editable text is received.
