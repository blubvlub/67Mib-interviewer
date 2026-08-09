# AI Interview Agent | 67Mib

An enterprise-grade, AI-powered technical interview agent designed for the 31-day AI Engineering Cohort.

Built for the **AI Cohort Hackathon**, this project evaluates candidates by seamlessly adapting to their background, parsing learning signals from their cohort missions, and driving a natural, guided technical conversation. It features a stunning, professional UI and a highly resilient, asynchronous backend.

---

## 🚀 Key Features

- **Adaptive Intelligence**: Reads `candidates.json` to map passed/failed/skipped missions to the 31-day curriculum, forming a complete picture of the candidate's strengths and weaknesses.
- **Dynamic Questioning**: Generates a customized interview plan on the fly. Prioritizes areas where the candidate struggled to probe for true understanding, while verifying depth in their strong areas.
- **Professional Minimalist UI**: A stunning, high-contrast interface featuring a **Dark/Light Mode Toggle**, pure monochrome palettes, and buttery-smooth message animations.
- **Live Interview Pressure**: Features a real-time countdown timer (15 minutes + 1 minute overtime) and a live progress bar to simulate the pacing and pressure of a real technical screen. Auto-terminates when time expires.
- **Concurrent & Asynchronous**: The backend uses `AsyncGroq` and `asyncio`, allowing multiple candidates to be interviewed simultaneously without blocking the server event loop.
- **Structured Feedback**: Concludes the interview with an actionable JSON report detailing strengths, gaps, and concrete next steps, beautifully rendered in the UI with color-coded badges.

## 🛠 Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **AI/LLM**: `openai/gpt-oss-120b` (Powered by Groq's Asynchronous Client)
- **Frontend**: HTML5, CSS3 (CSS Variables for Theming), Vanilla JavaScript, Marked.js

---

## 💻 Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/blubvlub/67Mib-interviewer.git
   cd 67Mib-interviewer
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and add your API keys.

5. **Start the server**
   ```bash
   uvicorn app.main:app --port 8000
   ```

6. **Access the application**
   Open your browser and navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## ☁️ Deployment

The project is fully configured for deployment on serverless or container-based platforms.

### Vercel (Requires GitHub)
A `vercel.json` configuration is included.
1. Import your GitHub repository in [Vercel](https://vercel.com).
2. Add your `GROQ_API_KEY` in the Environment Variables section.
3. Click **Deploy**.

> **Note**: Vercel's free tier imposes a strict 10-second timeout on Serverless Functions. Since large LLMs (like the 120B model) can sometimes take 10-15 seconds to reply, you may occasionally see `504 Timeout` errors. For a more stable free-tier experience, we recommend Render or Koyeb.

### Render / Koyeb
If using a platform like Render or Koyeb, use the following start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

---

## 🏗 Project Structure

```text
├── app/                        # Application backend
│   ├── main.py                 # FastAPI endpoints & static serving
│   ├── config.py               # Configuration & env vars
│   ├── models.py               # Pydantic schemas mapping to Technical Spec
│   ├── session.py              # In-memory interview session manager
│   ├── interview_engine.py     # Core conversational logic
│   ├── candidate_analyzer.py   # Analyzes learning signals & curriculum gaps
│   ├── question_generator.py   # Formulates prioritized interview plans
│   ├── llm_client.py           # Robust Async Groq client with rate limit handling
│   └── prompts.py              # Tuned prompt templates
├── frontend/                   # Web chat interface
│   ├── index.html              
│   ├── style.css               
│   └── app.js                  
├── problem_files/              # Hackathon data (curriculum & candidates)
├── tests/                      
│   └── simulate_interview.py   # Automated evaluation script
├── PROMPTS.md                  # Hackathon AI Usage Log
├── requirements.txt
└── README.md
```

---

## 📜 API Specification

The application exactly matches the Hackathon's requested `POST /api/interview` contract.

**Start Interview Payload:**
```json
{
  "sessionId": "sess_123xyz",
  "candidate": { ... full candidate object ... }
}
```

**Conversation Turn Payload:**
```json
{
  "sessionId": "sess_123xyz",
  "message": "My answer to the question..."
}
```
*(Supports a special `FORCE_END_INTERVIEW` message to gracefully wrap up demos or when the timer expires)*
