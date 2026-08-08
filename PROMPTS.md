# PROMPTS.md — Conversation Export

---

## Prompt 1 — User

```
your task is to go through all the files in ~/problem_files/ folder and help with creating a perfect interviewer program, my idea is to have a python based project with uvicorn, and using a free ai model as the interviewer.

While we text your side task is to export conversations without changing content and keeping the same format in "./PROMPTS.md".

Prepare the implementation plan.
```

## Response 1 — Assistant

Read all files in `problem_files/`:
- `problem_statement.md` — Hackathon challenge: build an AI Interview Agent for a 31-day AI engineering cohort
- `technical-spec.md` — API contract: single `POST /api/interview` endpoint with sessionId-based state
- `hackathon_rules.md` — Evaluation: eligibility, authenticity, judging rubric, live steer challenge
- `candidates.json` — 20 candidate profiles with missions, attempts, skips, and learning signals
- `curriculum.json` — 31-day curriculum across 8 modules covering AI/ML engineering topics

Created an implementation plan with:
- **Stack**: Python + FastAPI + Uvicorn + Groq free tier LLM (Llama 3.3 70B)
- **Architecture**: Session manager, candidate analyzer, question generator, LLM client, interview engine
- **Key features**: Adaptive questioning based on candidate signals, follow-up generation, structured feedback
- **Open questions**: Model preference (Groq vs Gemini vs Ollama), frontend needs, deployment target

See `implementation_plan.md` for full details.

---
