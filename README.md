# AI Interview Agent

An AI-powered technical interview agent that conducts personalized, multi-turn interviews for candidates of a 31-day AI engineering cohort.

Built for the **AI Cohort Hackathon**, this project evaluates candidates by seamlessly adapting to their background, parsing learning signals from their cohort missions, and driving a natural, guided technical conversation.

---

## 🚀 Features

- **Adaptive Intelligence**: Reads `candidates.json` to map passed/failed/skipped missions to the 31-day curriculum, forming a complete picture of the candidate's strengths and weaknesses.
- **Dynamic Questioning**: Generates a customized interview plan on the fly. Prioritizes areas where the candidate struggled to probe for true understanding, while verifying depth in their strong areas.
- **Intelligent Follow-ups**: Evaluates answers in real-time, asking deep follow-up questions or transitioning naturally when a topic is exhausted.
- **Structured Feedback**: Concludes the interview with an actionable JSON report detailing strengths, gaps, and concrete next steps.
- **Premium Interface**: A sleek, dark-mode, glassmorphism chat interface (HTML/CSS/JS) with markdown rendering, typing indicators, and full responsiveness.
- **Robust Architecture**: Built on FastAPI and Uvicorn. Implements resilient LLM client logic to handle rate limits and temporary failures gracefully.

## 🛠 Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **AI/LLM**: Groq API (Llama 3.3 70B Versatile)
- **Frontend**: HTML5, CSS3 (Custom Dark Theme), Vanilla JavaScript, Marked.js

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
   Open `.env` and add your **Groq API Key**:
   ```env
   GROQ_API_KEY=your_groq_key_here
   ```
   *(You can get a free key at [console.groq.com](https://console.groq.com))*

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Access the application**
   Open your browser and navigate to: [http://localhost:8000](http://localhost:8000)

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
│   ├── llm_client.py           # Robust Groq client with rate limit handling
│   └── prompts.py              # Tuned prompt templates
├── frontend/                   # Web chat interface
│   ├── index.html              
│   ├── style.css               
│   └── app.js                  
├── problem_files/              # Hackathon data (curriculum & candidates)
├── tests/                      
│   └── simulate_interview.py   # Automated evaluation script
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

The project includes an automated test script that spins up a virtual candidate and runs a full, 12-turn simulated interview against the local API to verify logic, follow-ups, and rate-limit handling.

To run the simulation:
```bash
python tests/simulate_interview.py
```

---

## 📜 API Specification

The application exactly matches the Hackathon's requested `POST /api/interview` contract.

**Start Interview Payload:**
```json
{
  "sessionId": "session-123",
  "candidate": { ... full candidate object ... }
}
```

**Conversation Turn Payload:**
```json
{
  "sessionId": "session-123",
  "message": "My answer to the question..."
}
```
*(Supports a special `FORCE_END_INTERVIEW` message to gracefully wrap up demos)*
