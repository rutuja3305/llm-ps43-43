# Submission guide and 2-page report template (PS43)

Do NOT include this file in the Code ZIP you upload if you prefer; it is only a helper.

## A. Git commands (repository name: llm-ps43-<YourRollNo>, set to Public)

```bash
git init
git add .
git commit -m "LLM mini project PS43"
git branch -M main
git remote add origin https://github.com/<username>/llm-ps43-<RollNo>.git
git push -u origin main
```

Check on GitHub that `.env` is NOT in the file list. If the repo already has a README, run
`git pull origin main --allow-unrelated-histories` before pushing, or use Add file > Upload files instead.

## B. Drive folder checklist

```
Your individual folder/
  Report.pdf          2 pages, A4, 12 pt
  Code.zip            project folder with NO .env and NO venv
  github_link.txt     your repository URL
  screenshots/        3 to 5 screenshots
  demo_video.mp4      optional
```

Screenshots to take (Win + Shift + S): (1) sidebar with provider set, (2) a sample filled in,
(3) the 3 headline options, (4) the before/after view, (5) the error message when target role is empty.

## C. Report template (write in your own words, 2 pages)

**Header:** LinkedIn Profile Optimizer, PS43, <Name>, Roll No 43, <Class>, <GitHub link>

**Problem statement:** Student LinkedIn profiles are weak and generic, which reduces recruiter visibility.
The tool rewrites the headline and About section from the student's skills and target role.
It helps students and freshers who do not know how to present themselves.

**Tools and model:** Python, Streamlit, openai client library, python-dotenv; LLM: <e.g. Llama 3.3 70B via Groq / Gemini 2.5 Flash>.

**Procedure (edit to match what you actually did):**
1. Created a virtual environment and installed the libraries.
2. Created a free API key at <provider> and stored it in a `.env` file.
3. Tested the prompt in the provider's playground with 3 to 5 sample profiles.
4. Wrote `optimizer.py` to validate inputs, build the prompt, call the model and parse the JSON.
5. Built the Streamlit UI in `app.py` with input fields, sample loader, headline cards and a before/after view.
6. Tested on 5 sample inputs and checked headline (220) and About (2600) length limits.
7. Pushed the code to GitHub and uploaded the files to Drive.

**Prompt used:** paste the SYSTEM_PROMPT from `optimizer.py`. Then describe ONE real improvement you made,
for example: "At first the model invented numbers and achievements, so I added the rule to use only facts from the input."
(Only write this if it happened. Run the app and note a genuine problem you saw.)

**Results:** 1 or 2 screenshots with one sample input and its output.

**Challenges:** Real problems you hit, such as invalid JSON, headlines longer than 220 characters, API rate limits or
wrong model names, and how you fixed them (retry with a repair message, length check, LLM_MODEL override).

**Conclusion:** What works (3 distinct headlines, honest rewriting, error handling), what does not
(cannot verify facts, depends on input quality), and one improvement (upload a resume PDF to fill the fields automatically).
