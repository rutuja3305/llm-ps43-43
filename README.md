# LinkedIn Profile Optimizer (PS43)

GenAI mini project, Problem Statement 43.

**Problem:** Student LinkedIn profiles are weak. This app rewrites the headline and About section from the
user's current headline, About, skills and target role, and shows a before/after comparison.

**Output:** 3 headline options (each with a different angle) + a rewritten About section + keywords used + improvement tips.

## Stack

- Python 3.10+
- Streamlit (UI) in `app.py`
- Backend logic in `optimizer.py` (prompt, LLM call, JSON parsing and validation)
- `openai` client library, which works with Groq, Gemini, OpenAI and local Ollama
- No model training and no database

## Project structure

```
app.py               Streamlit UI (frontend)
optimizer.py         Prompt, LLM call, validation (backend)
sample_inputs.json   5 sample profiles for testing
tests/               Offline unit tests (fake LLM, no key needed)
.env.example         Template for your API key
requirements.txt
```

## 1. Get your own API key (free options)

Pick ONE provider.

**Option A: Groq (free, fastest to set up)**
1. Go to https://console.groq.com and sign in.
2. Open **API Keys** and click **Create API Key**.
3. Copy the key (it starts with `gsk_`). It is shown only once.

**Option B: Google Gemini (free tier)**
1. Go to https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key** and copy it.

**Option C: OpenAI (paid)**
1. Go to https://platform.openai.com/api-keys, create a key, and make sure the account has credit.

**Option D: Ollama (fully local, no key)**
1. Install Ollama from https://ollama.com, then run `ollama pull llama3.1`.
2. Keep Ollama running. Set `LLM_PROVIDER=ollama` and leave the key empty.

## 2. Add the key to the project

1. In the project folder, copy `.env.example` to a new file named `.env`.
   - Windows: `copy .env.example .env`
   - Mac/Linux: `cp .env.example .env`
2. Open `.env` and set your provider and key, for example:
   ```
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_your_real_key_here
   ```
   For Gemini use `LLM_PROVIDER=gemini`; for OpenAI use `LLM_PROVIDER=openai`.
3. Save the file. Never upload `.env` anywhere (it is already listed in `.gitignore`).

You can also skip the `.env` file and paste the key into the app's sidebar. That key stays in memory only.

If a provider has renamed its model, set `LLM_MODEL=` in `.env` to a current model name from the provider's docs.

## 3. Install and run

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## 4. How to use

1. Choose a sample profile from the dropdown, or type your own details.
2. Enter a target role (required) and at least one of: headline, About, skills.
3. Click **Optimize my profile**.
4. Pick a headline option and compare before and after. Download the result as `.txt`.

## 5. Run the tests (no API key needed)

```bash
pip install pytest
python -m pytest -q
```

## How it works

1. `validate_inputs` checks the form (target role required, length limits).
2. `build_user_prompt` formats the inputs and marks missing fields as "(not provided)".
3. A system prompt instructs the model to use only the provided facts, return exactly 3 headlines (max 220 characters)
   and an About section (110 to 180 words), with no emojis or cliches, and to answer in a fixed JSON shape.
4. `optimize_profile` calls the model in JSON mode. If the output is not valid, it retries once with a repair message.
5. Provider errors (bad key, rate limit, wrong model, no connection) are turned into plain messages.

## Limitations

- The model can only rewrite what you give it. Check every sentence is true for you before posting.
- Output quality depends on the model and on how much detail the input has.
- It does not connect to LinkedIn.
