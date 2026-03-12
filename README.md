# AI Pair Engineer

Paste Python code, get back design analysis, generated tests, refactored code, and a quality score.

It is a pair programmer not a code reviewer. It understands your intent, spots architectural issues, writes test suites, and refactors your code with explanations.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your DeepSeek API key:

```
DEEPSEEK_API_KEY=your_key_here
```

## Run

```bash
streamlit run app.py
```

## What You Get

| Section | Output |
|---|---|
| Design Analysis | SOLID violations, coupling issues, security concerns, race conditions, N+1 queries |
| Generated Tests | Complete, copy-paste ready pytest suite |
| Refactored Code | Full rewritten code with inline comments and change summary |
| Pair Notes | Quality score (1-10), actionable next steps, conversational advice |

