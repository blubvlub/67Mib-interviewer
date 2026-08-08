# AI Interview Agent

An AI-powered technical interview agent that conducts personalized, multi-turn interviews for candidates of a 31-day AI engineering cohort.

## Tech Stack

- **Backend**: Python + FastAPI + Uvicorn
- **LLM**: Groq (Llama 3.3 70B — free tier)
- **Frontend**: Web-based chat interface

## Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API

Single endpoint as per the technical specification:

```
POST /api/interview
```

See `problem_files/technical-spec.md` for full API contract.

## Project Structure

```
├── app/                    # Application source code
├── problem_files/          # Hackathon problem data
├── frontend/               # Web chat interface
├── PROMPTS.md              # AI usage log
└── README.md
```
