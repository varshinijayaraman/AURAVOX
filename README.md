# AURA VOX — Voice Identity & Secure Document Workspace

A multi-page Flask web application with a moving animated robot assistant, multilingual voice challenges, account registration and sign-in, a personal dashboard, charts, event history, profile information, and a per-user document vault.

## Included structure

```text
AuraVox_Frontend/
├── app.py
├── requirements.txt
├── README.md
├── instance/                 # SQLite database created on first run
├── uploads/
│   ├── documents/            # User-specific document uploads
│   ├── voice_profiles/       # Enrolled audio samples
│   └── staged/               # Temporary recorded samples
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── analytics.html
│   ├── history.html
│   ├── documents.html
│   └── document_verify.html
└── static/
    ├── style.css
    ├── app.js
    └── auravox-logo.png
```

## Run in VS Code (Windows PowerShell)

1. Extract the ZIP file.
2. Open VS Code → **File → Open Folder** → select `AuraVox_Frontend`.
3. Open **Terminal → New Terminal**.
4. Run these commands one at a time:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this once in the same terminal, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

5. Open `http://127.0.0.1:5000` in Chrome or Edge. The browser microphone works on localhost; allow microphone access when prompted.
6. Create a profile with a unique email, password (at least 8 characters), a 4–8 digit PIN, and preferred language. Record three samples before submitting.
7. Sign in with the same email, PIN, and preferred language; record a fresh voice sample.
8. Open the dashboard, review the charts/history, upload a document in the vault, and try the document voice step.

## Language challenges

The language menu contains more than 100 languages. Common languages include curated native-script phrases. Other languages use the optional online `deep-translator` service to translate a randomized challenge from English. Translation requires an internet connection; if translation is unavailable, the app visibly reports that the fallback phrase remains in English rather than pretending it was translated.

## Important security limitation

This application provides working registration/login routes, password/PIN hashing, local SQLite records, audio capture and storage, per-user document storage, and a voice-recording step. **It does not yet run an AI-generated-speech detector or speaker-verification model.** A captured recording alone is not proof of identity, and the current local document gate is not sufficient for confidential production documents. Integrate and validate AASIST (or another anti-spoof model), ECAPA-TDNN/SpeechBrain (or another speaker-verification model), replay/liveness protections, encrypted storage, CSRF protections, rate limiting, audit retention, and deployment secrets before relying on biometric security. The chart library loads from a CDN, so the browser needs internet access for charts.

## Troubleshooting

- `python` not found: install Python 3.10+ and enable **Add Python to PATH**.
- Microphone unavailable: use `http://127.0.0.1:5000` or HTTPS, not a plain `file:///` page, and grant browser permission.
- Port 5000 busy: stop the other Flask process or change `app.run(port=5001)` at the bottom of `app.py`.
- Challenge translation unavailable: check internet connectivity and retry; English fallback is explicitly identified.
