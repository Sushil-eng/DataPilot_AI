# DataPilot AI — Generic AI-Powered Data Intelligence Platform

DataPilot AI is an enterprise-grade, generic AI-powered data intelligence platform. It converts plain-text prompt requests into dynamic schemas, plans multi-step data collection workflows, executes web discovery and extraction, cleanses, validates, and deduplicates data, and serves analytics and exports via an interactive web interface.

---

## 🌟 Key Capabilities

- **AI Intent & Schema Planning**: Generates structured dynamic JSON schemas tailored to any user prompt using LLMs.
- **Generic Source Discovery**: Searches across generic web sources and structured directories with domain query variation.
- **Resilient Data Extraction**: Extracts structured fields from web HTML and API sources with fallbacks.
- **Robust Cleaning & Validation**: Normalizes dates, phone numbers, prices, and emails; validates field constraints.
- **Strict Deduplication**: Performs exact and fuzzy deduplication on extracted dataset records.
- **MongoDB Persistence**: Stores schemas, tasks, workflows, sources, datasets, and dataset records.
- **JWT Authentication & Ownership**: Secure user registration, password hashing (bcrypt), token authentication, and data isolation.
- **Analytics & Export Engine**: Provides real-time dashboard analytics, dataset exploration, search, filtering, and 1-click CSV/JSON export.

---

## 🏗️ Architecture & Pipeline Overview

```
User Request (Prompt)
  │
  ├── 1. AI Planning (Intent & Dynamic Schema Generation)
  ├── 2. Workflow Initialization (9 Pipeline Steps)
  ├── 3. Source Discovery (Generic & Multi-Domain Queries)
  ├── 4. Data Extraction (Web Page & HTML Scraping)
  ├── 5. Data Cleaning (Normalizers & Standardizers)
  ├── 6. Validation (Schema Type & Constraint Auditing)
  ├── 7. Deduplication (Exact Fingerprints & Similarity Matching)
  ├── 8. Dataset Storage (MongoDB Collections & Provenance)
  └── 9. Analytics & Export (Interactive UI, CSV/JSON Download)
```

---

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS (Vanilla custom design tokens), Lucide Icons, Recharts, React Router v6.
- **Backend**: FastAPI (Python 3.11+), Pydantic v2, Motor (Async MongoDB Driver), PyJWT, Bcrypt, HTTPX.
- **Database**: MongoDB 6.0+.
- **AI / LLM**: Groq (Llama 3.3 70B), OpenAI GPT-4, Google Gemini.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ installed
- Node.js 18+ installed
- MongoDB running locally on `mongodb://localhost:27017` (or MongoDB Atlas connection string)

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run FastAPI Dev Server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install

# Run Vite Dev Server
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🧪 Integration & End-to-End Testing

Run the automated backend integration suite covering authentication, task CRUD, pipeline execution across 4 target scenarios, dataset exports, and security checks:

```bash
cd backend
.\venv\Scripts\python.exe test_phase5_prompt4.py
```

### Verified Test Scenarios
1. *"Find 30 AI startups in India founded after 2022."*
2. *"Find Python developer jobs in Mumbai."*
3. *"Find laptops under ₹50,000 with at least 16GB RAM."*
4. *"Find construction companies in Mumbai with website, location and services."*

---

## 🔒 Security & Authorization

- **Password Hashing**: Pre-hashed with SHA-256 and stored using Bcrypt.
- **Stateless Auth**: Signed JWT tokens (`Bearer <token>`).
- **User Data Isolation**: Protected task, dataset, record, and export endpoints. Unauthorized access returns clean `404/403` status codes without leaking object existence or stack traces.
- **Sanitized Errors**: Unified error formatting:
  ```json
  {
    "success": false,
    "error": {
      "message": "Resource not found or unauthorized access."
    }
  }
  ```

---

## 📄 License

MIT License. Built with ❤️ for Advanced AI Data Intelligence.
