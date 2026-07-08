---
name: hackathon-playbook
description: Use when the user is starting a hackathon, vibe-coding sprint, or any time-boxed prototype with judging criteria. Triggers on phrases like "hackathon", "PromptWars", "vibe coding", "build in N hours", "prototype with judges", "MVP for a demo". Provides a phased build playbook, stack picker, deploy templates, score-driven polish loop, and copy-paste code patterns proven on a real 3rd-prize-winning submission.
---

# Hackathon Playbook

> Distilled from a real PromptWars hackathon run that shipped a Gemini-powered meeting-to-action-items tool, scored 93% on judging, and won 3rd prize. Every pattern below was paid for in build time.

## When to invoke this skill

- User mentions a hackathon, vibe-coding event, or judged demo with a deadline under 24 hours
- User asks for a "1-hour MVP" or "build something to demo"
- User shares judging criteria (Code Quality, Security, Efficiency, Testing, Accessibility, etc.)
- User describes a problem and wants the fastest path to a deployable prototype

## Qualifying questions to ask first (don't skip)

Before writing any code, get these answers — they determine the entire stack:

1. **How much time do you have?** (1 hour vs 8 hours vs weekend changes everything)
2. **What's the judging rubric?** Get the dimensions and weights. Optimize for them.
3. **What's installed on your machine?** Specifically: `node`, `python3`, `gcloud`, `docker`. **Don't assume — check.** Network for installs is often slow.
4. **What cloud / platform credits do you have?** GCP, AWS, Azure, Vercel, Cloudflare?
5. **Any LLM API key already?** Anthropic, OpenAI, Google AI Studio? Use what you have.
6. **Demo logistics:** are you presenting from your laptop, or is the URL evaluated remotely? Affects deploy urgency.
7. **Is this graded on a live URL or on the GitHub repo?** Some judges only read code.

If you can't get answers, default to the recipe in "The 90-minute MVP" below.

---

## Core operating principles

### 1. Demo-first thinking
Build backwards from the 90-second arc. Write the demo script BEFORE writing code. Every minute of build time should map to a moment in that demo. If a feature doesn't show up on stage, it doesn't ship.

### 2. Pivot fast on environment issues
If `node` isn't installed and pip is faster than brew install, switch to Flask. If the Anthropic SDK install is timing out, hit the REST API directly with `requests`. **Don't fight your environment — route around it.** A working Flask app beats a planned Next.js app every time.

### 3. The "no-OAuth trick"
**Never start with OAuth in a hackathon.** OAuth eats 30+ minutes (consent screens, scope reviews, redirect URIs, token storage, refresh logic). Most "integrations" you'd build via OAuth have URL-spec equivalents:

| Service | URL-spec endpoint | Auth needed |
|---|---|---|
| Google Calendar | `https://calendar.google.com/calendar/render?action=TEMPLATE&text=...&dates=...&add=...` | None — opens in user's logged-in tab |
| Gmail | `https://mail.google.com/mail/?view=cm&fs=1&to=...&su=...&body=...` | None — same |
| Google Docs (read public) | `https://docs.google.com/document/d/<DOC_ID>/export?format=txt` | None — works for "Anyone with link" Docs |
| Twitter/X | `https://twitter.com/intent/tweet?text=...` | None |
| LinkedIn share | `https://www.linkedin.com/sharing/share-offsite/?url=...` | None |
| WhatsApp | `https://wa.me/?text=...` | None |

These open the target service with prefilled actions. User clicks Save/Send. **Identical demo experience to a real integration, zero auth setup.** Be honest about it in your pitch — judges respect the engineering judgment.

### 4. One LLM call per user action
Use **structured output schemas** (Gemini's `responseSchema`, OpenAI's `response_format`, Anthropic's tool calling) to guarantee parseable JSON. Skip retry loops, skip string parsing. One call in, one structured object out.

### 5. Sample-load on demand
Bake a realistic sample input into the UI as a "Load sample" button. Demo works on a cold click without typing. Saves you on stage when nerves hit.

### 6. Score the rubric ruthlessly
If judging is automated/itemized:
- After first submission, identify the 1-2 weakest dimensions
- Target those specifically — don't try to lift everything
- 100% on Testing (with a coverage gate) is achievable in 30 min and gives you a defensible win
- Accessibility (semantic HTML + ARIA labels) is also achievable in 30 min

---

## The 90-minute MVP sprint (when truly time-boxed)

Hard checkpoints. If you miss one, cut scope, don't extend the phase.

### Phase 0 — Decisions (5 min, BEFORE coding)

Settle these:
1. **Stack:** what's installed locally? Pick from "Stack picker" below.
2. **LLM:** which key do you have? Use the simplest available.
3. **Demo arc:** write 5 bullet points of the 90-second demo. Tape it to your screen.
4. **What you're NOT building:** explicitly list non-goals.

### Phase 1 — Skeleton + extraction (30 min)

Build the absolute minimum:
- One page with input + button + output panel
- Backend route that calls the LLM and returns structured JSON
- Hardcode a sample input visible behind a "Load sample" button
- **Stop when:** paste input → click button → see structured output

### Phase 2 — The visible feature (20 min)

Whatever your "secret sauce" is, build it visibly. For Postmeet, that was the Trello-style board grouped by assignee. Pick the *one* visualization that makes the demo pop.

### Phase 3 — Distribution / output (15 min)

How does the result leave the app? Email? Calendar? Slack? Use URL-spec patterns from the table above. Per-item buttons. Optional: a "do all" bulk button (always opens N tabs at once — staggered with `setTimeout` to dodge popup blockers).

### Phase 4 — Deploy + smoke test (15 min)

- Cloud Run via `gcloud run deploy --source .` + buildpacks (no Dockerfile)
- Pass API keys via Secret Manager (security rubric points)
- Add `--min-instances=1 --cpu-boost` to prevent cold starts
- After deploy, **always smoke-test with curl** before saying "done"
- Verify the revision number incremented from the previous deploy

### Phase 5 — Demo prep (5 min)

- Pre-load sample input
- Practice the 90-second arc once out loud
- Open the live URL in a fresh tab
- Have a fallback plan if the URL fails on stage

---

## Stack picker (proven combinations)

### Python is installed, no Node:
**Flask + Tailwind CDN + LLM REST API** (don't bother with SDKs — slower install, more moving parts)
- Single `app.py` (~200 LOC fits a 1-hour build)
- `templates/index.html` with Tailwind via `<script src="https://cdn.tailwindcss.com">`
- Inline JS to start; extract to `static/` only if time permits
- Deps: `flask`, `requests`, `python-dotenv`, `gunicorn` (for deploy)

### Node is installed, fast network:
**Next.js + Tailwind + AI SDK**
- `npx create-next-app@latest --typescript --tailwind --app`
- One page, one API route, one LLM call
- Deploy to Vercel: `vercel deploy` — 30 seconds

### You want zero infrastructure:
**Static HTML + bring-your-own-API-key**
- Single `index.html`, vanilla JS
- User pastes their LLM API key into a localStorage-backed input
- Deploy to GitHub Pages or Cloudflare Pages
- Risky for judges (they'd need their own key) — only use if scoring is on code, not on live demo

### You need real persistence:
**Add a Google Sheet as a "database"**
- Skip Postgres / Supabase setup (eats 20+ min)
- Use a Sheet as your data store via the Sheets API + service account
- Adds another Google service to the rubric

---

## Deploy template (Cloud Run, copy-paste-ready)

This script handles APIs, Secret Manager, IAM, and deploy in one shot. Saves the deploy.sh in `web/` (or your app root).

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: ./deploy.sh PROJECT_ID API_KEY
PROJECT_ID="${1:?Usage: ./deploy.sh PROJECT_ID API_KEY}"
API_KEY="${2:?Usage: ./deploy.sh PROJECT_ID API_KEY}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-myapp}"
SECRET_NAME="${SECRET_NAME:-app-api-key}"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# Secret Manager: store/update API key
if gcloud secrets describe "$SECRET_NAME" >/dev/null 2>&1; then
  echo -n "$API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
else
  echo -n "$API_KEY" | gcloud secrets create "$SECRET_NAME" --data-file=- --replication-policy=automatic
fi

# Grant Cloud Run runtime SA access
PROJECT_NUM=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:${PROJECT_NUM}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" --quiet

# Deploy
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-secrets "API_KEY=${SECRET_NAME}:latest" \
  --memory 512Mi \
  --min-instances 1 \
  --max-instances 3 \
  --cpu-boost \
  --timeout 60 \
  --quiet

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')
echo "✅ Deployed: $URL"
```

### Cloud Run prerequisites for fresh GCP projects (gotcha)

In 2024+, the default Compute Engine SA no longer has Cloud Build/Run permissions. You MUST grant these once per project:

```bash
PROJECT=your-project-id
SA=$(gcloud projects describe $PROJECT --format='value(projectNumber)')-compute@developer.gserviceaccount.com
for role in roles/cloudbuild.builds.builder roles/run.builder roles/storage.objectViewer roles/logging.logWriter roles/artifactregistry.writer; do
  gcloud projects add-iam-policy-binding $PROJECT --member="serviceAccount:$SA" --role="$role" --quiet
done
```

If your first `gcloud run deploy --source .` fails with "PERMISSION_DENIED: Build failed because the default service account is missing required IAM permissions" — this is the fix.

### Required files for Cloud Run buildpacks

```
web/
├── Procfile              # web: gunicorn -b 0.0.0.0:$PORT --workers 2 --timeout 60 app:app
├── requirements.txt      # flask, gunicorn, requests, python-dotenv, ...
├── runtime.txt           # python-3.10
├── .gcloudignore         # .env, .tmp/, __pycache__/, .pytest_cache/
└── app.py                # entry: must honor $PORT env var, bind 0.0.0.0
```

### Buildpacks-friendly Flask startup
```python
if __name__ == "__main__":  # pragma: no cover
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
```

### Cache-busting static assets on every deploy (do this from day one)

The single most-painful "ghost bug" of any iterative deploy: users open the redeployed site and see *the old JS* because their browser cached `/static/app.js`. Symptoms: features that work locally fail in production, click handlers go missing, dead UI elements. Native confirm dialogs say things like *"setMode is not a function"* in console.

The fix is two lines of Python and one templating change. Apply this before your first deploy:

```python
# In app.py
from typing import Final
from pathlib import Path

BUILD_ID: Final[str] = str(int(Path(__file__).stat().st_mtime))

@app.context_processor
def inject_build_id() -> dict[str, str]:
    return {"build_id": BUILD_ID}
```

```html
<!-- In your template -->
<script src="/static/app.js?v={{ build_id }}" defer></script>
<link rel="stylesheet" href="/static/app.css?v={{ build_id }}">
```

The `?v=...` value changes on every deploy (file mtime → new query string → browser bypasses cache). No CDN config, no manual versioning, no "tell users to hard-refresh". Free.

**Skip this and you will lose 30+ minutes debugging "why isn't my redeploy taking" when the answer is browser cache.** This was paid for in real time.

---

## Cloud Shell deploy flow (when local gcloud isn't available)

If you don't have gcloud installed and brew install is too slow:

1. Open https://shell.cloud.google.com (gcloud preinstalled, pre-authed)
2. **Use git clone instead of zip upload** — single source of truth, eliminates the "wrong zip uploaded" risk
3. ```bash
   rm -rf ~/myapp && \
   git clone https://github.com/YOU/REPO.git ~/myapp && \
   cd ~/myapp/web && \
   chmod +x deploy.sh && \
   ./deploy.sh PROJECT_ID API_KEY
   ```
4. **Always check the revision number** — it must increment (e.g. 00006 → 00007). If it doesn't, the deploy didn't actually take.

---

## Test gate template (gives you 100% on Testing rubric)

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --cov=app --cov-report=term-missing --cov-fail-under=100"

[tool.coverage.run]
source = ["app"]
branch = true

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if __name__ == .__main__.:"]
fail_under = 100
show_missing = true
```

`tests/conftest.py` (handles module-level env-var guards):
```python
import os, sys
from pathlib import Path
os.environ.setdefault("API_KEY", "test-key-fixture")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import app as app_module

@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c

@pytest.fixture
def app_mod():
    return app_module
```

### Testing patterns that hit 100% coverage

- **Mock all HTTP** — `unittest.mock.patch("app.requests.post")` returning a MagicMock with `.ok`, `.status_code`, `.json()`, `.text`
- **Test module-level guards** with `importlib.reload` after mutating env vars + monkey-patching `dotenv.load_dotenv`
- **Test every error branch** — for each `try/except`, write a test that triggers each exception type
- **Test middleware directly** — call `after_request` hooks with a crafted `flask.Response` to hit branches the test client can't reach
- **Use `# pragma: no cover` ONLY on truly untestable lines** — `if __name__ == "__main__":`, raise statements during import-only paths

---

## Efficiency wins (cheap, measurable)

These three add up to ~15 percentage points on Efficiency rubric:

### 1. gzip middleware (stdlib only, no Flask-Compress dependency)
```python
@app.after_request
def gzip_response(response):
    if response.direct_passthrough or response.status_code < 200 or response.status_code >= 300:
        return response
    if response.headers.get("Content-Encoding"):
        return response
    if "gzip" not in (request.headers.get("Accept-Encoding") or ""):
        return response
    if response.content_length is not None and response.content_length < 500:
        return response
    data = gzip.compress(response.get_data(), compresslevel=6)
    response.set_data(data)
    response.headers["Content-Encoding"] = "gzip"
    response.headers["Content-Length"] = str(len(data))
    response.headers["Vary"] = "Accept-Encoding"
    return response
```

Verify with: `curl -sI --compressed http://your-url/` — should show `Content-Encoding: gzip`. Typical win: 60-70% smaller HTML/JSON on the wire.

### 2. Cache-Control on the index page
```python
@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp
```

### 3. Static assets cached
```python
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24  # 1 day
```

### 4. Cloud Run cold-start prevention
Add to `gcloud run deploy`: `--min-instances 1 --cpu-boost`

---

## Code quality wins (cheap, observable)

These show up immediately to anyone reading the repo:

### Type hints + docstrings + named constants
```python
from typing import Final, Pattern

MIN_TRANSCRIPT_LENGTH: Final[int] = 30
DOC_ID_RE: Final[Pattern[str]] = re.compile(r"/document/d/([a-zA-Z0-9_-]+)")

def fetch_doc_text(url: str) -> str:
    """Fetch plain text from a public Google Doc.

    :raises ValueError: URL doesn't match expected shape.
    :raises PermissionError: Doc isn't shared publicly.
    :raises RuntimeError: Other non-2xx fetch result.
    """
    ...
```

### Section banners separate concerns
```python
# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
```

### Extract inline JS to a static file
A `<script>` block over 200 lines belongs in `static/app.js`. Keeps HTML scannable and the JS becomes browser-cacheable separately.

### ruff config in pyproject.toml
```toml
[tool.ruff]
line-length = 110
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]
```

### GitHub Actions CI workflow (visible signal)
`.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
jobs:
  test:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: web } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10", cache: pip }
      - run: pip install -r requirements.txt && pip install -r requirements-dev.txt
      - run: pytest
        env: { API_KEY: test-key-ci }
```

A green CI badge on the GitHub README is a credibility marker for any judge browsing the repo.

---

## UX patterns to copy (proven in user testing)

These are non-obvious choices that get rediscovered every hackathon. Skip rebuilding from scratch.

### 1. One input that auto-detects mode > multiple input tabs

If your app accepts multiple input shapes (paste text, paste URL, upload file, fetch from API), the lazy default is to make N tabs and force the user to pick. **Better: one combined input that auto-detects from content.**

```js
// Single textarea — detect what it contains, branch backend call accordingly
function detectMode() {
  const text = $('input').value.trim();
  if (URL_RE.test(text) && text.length < 250 && !text.includes('\n\n')) return 'url';
  if (detectedMode === 'file' && text === $('input').dataset.fileContent) return 'file';
  return 'text';
}
```

Pair with: drag-and-drop on `document` for file uploads, an "Attach file" button anchored inside the input area, a small italic hint that lights up when a non-text mode is detected (`"Detected: Google Doc URL"`).

Fewer clicks, less explanation, more flexibility. Users figure it out without reading.

### 2. Bulk dispatch consolidates by recipient, not by item

If your app sends N artifacts to M people, the lazy default is to dispatch N times (e.g. one email per task). **Better: group by recipient and send M times** (one email per person, listing all their items).

```js
// Wrong: N tasks → N emails
items.forEach(item => window.open(mailUrl(item), '_blank'));

// Right: N tasks across M people → M emails
const byOwner = {};
items.forEach(it => (byOwner[it.owner] = byOwner[it.owner] || []).push(it));
Object.entries(byOwner).forEach(([owner, list]) => {
  window.open(consolidatedMailUrl(owner, list), '_blank');
});
```

For Calendar events the opposite is true — each task becomes its own slot, so per-task dispatch is correct. The rule: **consolidate where the medium permits it (email, Slack), split where the medium requires it (calendar events, file exports).**

### 3. Inline editing with dotted-underline affordance

Modal edit forms break flow. Click-anywhere-to-edit beats them. The trick is making editability *discoverable* without cluttering the default state.

```css
.editable {
  cursor: pointer;
  border-bottom: 1px dotted transparent;  /* invisible, but reserves space */
  transition: border-color 0.15s, background 0.15s;
  padding: 0 2px;
}
.editable:hover {
  border-bottom-color: #8C8377;
  background: rgba(232,116,60,0.04);
}
```

Hover reveals a dotted underline + subtle accent tint — universal "this is editable" signal without needing pencil icons or hover tooltips.

JS pattern: event delegation on the parent container, swap `<span>` ↔ `<input>` on click, save on blur or Enter, Escape cancels:

```js
container.addEventListener('click', (e) => {
  if (!e.target.classList.contains('editable')) return;
  startEdit(e.target);
});

function startEdit(span) {
  const input = document.createElement('input');
  input.value = span.textContent;
  span.replaceWith(input);
  input.focus(); input.select();
  input.addEventListener('blur', () => commit(input.value));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') commit(span.textContent);  // revert
    if (e.key === 'Enter') commit(input.value);
  });
}
```

### 4. localStorage with TTL + restore-toast

Refresh = lost work is the #1 dropoff in single-page tools. Add this in 15 min:

```js
const STORAGE_KEY = 'app:state:v1';
const TTL_MS = 7 * 24 * 60 * 60 * 1000;

function persist(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ data: state, savedAt: Date.now() }));
}

function maybeRestore() {
  const blob = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
  if (!blob || Date.now() - blob.savedAt > TTL_MS) return;
  showToast({
    message: `Restore last session? (saved ${formatAgo(blob.savedAt)})`,
    actions: [
      { label: 'Restore', onClick: () => render(blob.data) },
      { label: 'Discard', onClick: () => localStorage.removeItem(STORAGE_KEY) },
    ],
    sticky: true,
  });
}
```

The restore prompt is non-blocking (toast), dismissible, and the TTL prevents week-old state from haunting users. Always pair `persist()` with every state mutation, not just initial load.

### 5. Toast notifications > native confirm() / alert()

`window.confirm()` blocks the page, looks like 2007, and breaks visual flow. For non-urgent confirmations (bulk operations, restore prompts, undo windows), use a custom toast with action buttons.

```js
function showToast({ message, actions = [], durationMs = 6000, sticky = false }) {
  const toast = document.createElement('div');
  toast.className = 'fixed bottom-6 right-6 bg-ink text-cream px-4 py-3 max-w-sm shadow-lg';
  // ... append message + action buttons
  document.body.appendChild(toast);
  if (!sticky) setTimeout(() => toast.remove(), durationMs);
}
```

Bonus: toasts can stack, support undo windows, and don't interrupt typing in inputs.

### 6. Skeleton placeholders should match the shape of incoming data

A skeleton loader's job is to communicate *what's coming*, not just *that something's loading*. If your output is a kanban board with columns of cards, render one column with 3 card-shaped skeletons — not 4 empty rectangles. Users orient faster.

---

## Accessibility wins (15 min, +5-10 points)

- Skip-to-content link as first element after `<body>`
- Semantic HTML: `<main>`, `<section>`, `<article>`, `<header>`, `<nav>`
- ARIA on every interactive element: `aria-label`, `role="status"` for live regions, `role="tab"` + `aria-selected` for tab toggles
- Visible focus rings: `focus:ring-2 focus:ring-indigo-400`
- Keyboard shortcuts: ⌘/Ctrl+Enter for primary action
- Color contrast 4.5:1 minimum (WCAG AA), 7:1 for AAA — verify with browser devtools

---

## Anti-patterns to avoid (paid for in lost time)

| Anti-pattern | Cost | Fix |
|---|---|---|
| Starting with OAuth | 30+ min | Use URL-spec dispatch patterns instead |
| Installing the LLM SDK | 5-15 min when network is slow | Hit the REST API directly with `requests` |
| `npm create-next-app` without checking `node` is installed | 10+ min wasted | Run `which node` first; pivot to Flask if missing |
| Building a database before extraction works | 20+ min | Skip persistence for v1; ephemeral is fine |
| Uploading wrong zip to Cloud Shell | 1-3 min per failed deploy | Use git clone from GitHub instead |
| Trusting "deploy succeeded" without smoke testing | embarrassing demo | Always `curl` the live URL after deploy |
| `git push` failing on first hackathon repo | 10+ min on auth | Push from your IDE's source control panel (it has its own auth) |
| Force-pushing to main on a shared repo | data loss | Only force-push on a fresh repo with single contributor |
| Inline JS over 200 lines | code-quality penalty | Extract to `static/app.js` with `defer` attribute |
| Skipping tests "to save time" | testing-rubric penalty | 30 min of mocked tests = 100% coverage gate |
| **Trusting browser cache after a redeploy** | 30+ min debugging "why isn't my redeploy taking" | Cache-bust `<script src="/static/app.js?v={{ build_id }}">` from day one (see Deploy template) |
| **Multiple tabs for input modes when one auto-detecting input would do** | clutter, more clicks, more explanation | One textarea + auto-detect from content (see UX patterns #1) |
| **Bulk dispatch sends one artifact per item instead of consolidating per recipient** | spammy emails, popup-blocker chaos | Group by recipient (see UX patterns #2) |
| **Native `confirm()` for non-blocking choices** | breaks flow, looks like 2007 | Toast with action buttons (see UX patterns #5) |

---

## When you redeploy and the URL still shows old code

This bit Postmeet hard. Diagnostic checklist, in order of likelihood:

1. **Browser cache.** If the deploy logs say success but features are missing in YOUR browser, a stale `app.js` is the most likely culprit. **Test:** open the URL in an incognito window or hard-refresh (`Cmd+Shift+R`). If features now appear, it was cache. **Permanent fix:** add the build_id query string to your script tag (see Deploy template). Most sessions of "why isn't my redeploy taking" end here.
2. **Did the deploy actually run?** Check for `✅ Deployed: ...` final line.
3. **Did the revision number increment?** `gcloud run revisions list --service S --region R --limit 5`. If it didn't, the build didn't take.
4. **Did the right files get uploaded?** Check unzip output for the critical files. Missing files like `static/app.js` from the unzip = wrong zip uploaded. **Use git clone instead of zip uploads** to eliminate this class of error.
5. **Is there a CDN cache between you and Cloud Run?** Add a query param: `curl "$URL/?cachebust=$(date +%s)"`. If size differs, it's caching. If not, it's truly the deployed code.
6. **When in doubt, smoke-test with curl, not with a browser** — browsers cache aggressively, curl doesn't.

Always smoke-test with this script after a deploy:
```bash
URL=https://your-service.run.app
echo "1) GET /:" && curl -sI -H "Accept-Encoding: identity" $URL/ | head -5
echo "2) New feature in HTML:" && curl -s $URL/ | grep -c "EXPECTED_NEW_STRING"
echo "3) New endpoint:" && curl -s $URL/new-endpoint
echo "4) Revision:" && gcloud run services describe SERVICE --region REGION --format='value(status.latestReadyRevisionName)'
```

If feature count is 0, the new code isn't live regardless of what the deploy log said.

---

## Score-driven polish loop

If judging is iterative (graded → resubmit → graded again), here's the loop:

1. **Submit basic working version** (the 90-min MVP). Get a baseline score.
2. **Identify the 1-2 weakest dimensions.** Don't try to lift everything.
3. **Pick the highest ROI fix.** Match the dimension to the table:

| Weak dimension | High-ROI fix | Time | Score lift |
|---|---|---|---|
| Testing | Add pytest + 100% coverage gate (`pyproject.toml`) | 30 min | +10-15% |
| Efficiency | gzip middleware + Cache-Control + min-instances | 15 min | +10-15% |
| Code Quality | Type hints + docstrings + JS extraction + ruff config + CI | 30 min | +5-10% |
| Accessibility | ARIA labels + skip link + focus rings + ⌘+Enter | 15 min | +3-7% |
| Security | Move secrets to Secret Manager + add `.gcloudignore` | 10 min | +3-5% |
| Google Services usage | Add Sheets-as-database OR Docs URL fetch (no-OAuth trick) | 25 min | +5-10% |
| Problem Statement Alignment | Sharper README problem section + better demo script | 15 min | +2-5% |

4. **Redeploy and verify.** Always smoke-test — the new code must actually be live.
5. **Resubmit.** Reassess.

---

## Pitch deck quick-start (for pitch-required hackathons)

If the hackathon includes a pitch component, use this slide skeleton:

1. **Title** — product name + 1-line tagline + your name
2. **Problem** — 3 bullets, real pain, real numbers if available
3. **Solution** — 3 benefit-led points (not features). Show the product, not the architecture.
4. **Traction** — actual numbers: build time, test coverage, services integrated, score so far
5. **Impact / Quote** — strong metric or pull-quote
6. **Secret Sauce** — what makes you uniquely buildable. Often: a clever choice that saves time/auth/setup.
7. **Business Model** — pricing tier table (Free / Team / Enterprise)
8. **Market (TAM)** — bottom-up calculation, never top-down
9. **Team** — be honest about being solo. "Looking for X co-founder" beats fake advisors.
10. **The Ask** — funding amount + 3 milestones for that capital

Style: minimalist or glassmorphism. Geist + Inter for fonts. One idea per slide. Bento-box layout for traction.

---

## After the hackathon ends

Always do:
- **Rotate any API keys** that were pasted in chat or screenshots — treat them as compromised
- **Document the demo URL** in the README so judges can find it later
- **Save the score breakdown** somewhere — useful for the next hackathon's strategy
- **Push final commits** before stage time runs out — don't rely on GitHub being current after the deadline

---

## Meta: when this skill is helpful and when it isn't

**Use this skill for:**
- Hackathons with judging rubrics
- Vibe-coding demos with a hard deadline
- Rapid prototypes that need a live URL within a few hours
- "Build a demo for the investor on Friday" sprints

**Don't use this skill for:**
- Production systems (the patterns here trade durability for speed; e.g., URL-spec dispatch is great for hackathon, mediocre for a real product)
- Long-term codebases (the "skip tests early" advice doesn't apply when the code lives for years)
- Teams of 5+ (this is solo / pair-programming optimized)

**The most important rule:** when judging is on a working live URL, *the URL has to actually work on stage.* Build everything else around that goal, and you'll be in the prize range.
