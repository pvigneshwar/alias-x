# ALIAS_X — Autonomous Verification Protocol

**AI-driven academic credential verification in under 60 seconds.**

ALIAS_X (Autonomous Linked Intelligence for Academic Screening and eXecution)
automates the entire certificate verification pipeline:

1. **Upload** a degree certificate (JPG/PNG)
2. **OCR** — Google Gemini 1.5 Pro Vision extracts Name, University, Degree, Year
3. **Uplink** — Intelligence Uplink discovers the registrar's phone & email
4. **Verify** — Bland AI places a voice call and classifies the transcript → VERIFIED / REJECTED

---

## Project Structure

```
ALIAS_X/
├── app.py               # Streamlit dashboard — main entry point
├── auth_manager.py      # SHA-256 credential auth, agent registration
├── ocr_engine.py        # Gemini 1.5 Pro Vision OCR engine
├── intel_uplink.py      # Registrar contact discovery via web search
├── ai_caller.py         # Bland AI telephony + transcript classification
├── report_generator.py  # fpdf2 PDF verification certificate generator
├── agents.json          # Agent credential store (auto-created)
├── verification_log.json# Audit log (auto-created on first verification)
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── ALIAS_X.spec         # PyInstaller .exe build spec (Windows)
└── README.md
```

---

## Requirements

- **Python 3.10+ (64-bit)** — mandatory for google-generativeai SDK
- **Windows 10 64-bit v1903+** (for .exe build; source runs cross-platform)
- Internet connection (5 Mbps+) for live API mode

### Hardware Minimum
| Component | Minimum |
|-----------|---------|
| CPU | Intel Core i5 8th Gen / AMD Ryzen 5 (4 cores) |
| RAM | 8 GB DDR4 |
| Storage | 256 GB SSD |
| Display | 1280×720 |

---

## Setup

### 1. Clone / download the project

```bash
git clone https://github.com/your-org/alias-x.git
cd alias-x
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
BLAND_AI_KEY=your_bland_ai_key_here
```

- **Gemini API key** → https://aistudio.google.com
- **Bland AI key** → https://app.bland.ai

---

## Running the Application

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

### First-time setup
1. Go to the **Register** tab and create your agent Codename + Access Key
2. Log in with those credentials
3. Upload a certificate and follow the pipeline

### Simulation Mode
Toggle **Simulation Mode** in the sidebar to run the full pipeline
offline using mock data — no API keys required.

---

## Building the Windows .exe

```bash
pip install pyinstaller
pyinstaller ALIAS_X.spec
```

The standalone executable will be at `dist/ALIAS_X.exe`.
It requires no Python installation to run — just double-click.

---

## API Keys Reference

| Service | Environment Variable | Where to get it |
|---------|---------------------|-----------------|
| Google Gemini 1.5 Pro | `GEMINI_API_KEY` | https://aistudio.google.com |
| Bland AI | `BLAND_AI_KEY` | https://app.bland.ai |

---

## Features

- **Zero-crash resilience** — any API failure falls back to Simulation Mode
- **Human-in-the-Loop (HITL)** — agent reviews OCR data and authorises the call
- **Structured audit log** — `verification_log.json` timestamped JSON array
- **PDF certificates** — downloadable A4 report for every session
- **Role-based auth** — SHA-256 hashed credentials, injection-sanitised
- **E.164 phone validation** — rejects malformed numbers before dialling

---

## Security Notes

- Never commit `.env` to version control — it's listed in `.gitignore`
- `agents.json` stores only SHA-256 hashes, never plaintext passwords
- All login errors return a generic "ACCESS DENIED" message (no field-level hints)

---

## License

Academic project — Department of Computer Science, 2023–2026.
