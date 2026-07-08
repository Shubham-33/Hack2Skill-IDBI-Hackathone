# Deploy & Submit — Prospect Assist AI

Three links the IDBI portal asks for: **GitHub repo**, **live product**, **demo video**. Steps below.

---

## 1. GitHub (public repo)

The repo is already committed locally. Push it public:

```bash
# with GitHub CLI (easiest):
gh auth login
gh repo create prospect-assist-ai --public --source=. --remote=origin --push

# or manually:
#   create an empty public repo on github.com, then:
git remote add origin https://github.com/<your-username>/prospect-assist-ai.git
git push -u origin master
```

`.env` is git-ignored, so **no secrets are pushed**. Data + trained models **are** committed, so a clone runs with zero setup.

→ Paste the repo URL into deck slide 13 and the submission portal.

---

## 2. Live product link (deployment)

The app is containerised ([Dockerfile](Dockerfile)) — WeasyPrint's native libs are baked in, and data/models are committed, so it boots with no setup. Pick one host:

### Option A — Render (free, simplest)
1. Push to GitHub (step 1).
2. [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint** → select the repo. It reads [render.yaml](render.yaml).
3. (Optional) add `NVIDIA_API_KEY` in the dashboard for AI-written copy — without it the app runs in graceful degraded mode.
4. Deploy → you get `https://prospect-assist-ai.onrender.com`. Health check: `/health`.
   *(Free instances sleep when idle — open the link ~30 s before the demo to wake it.)*

### Option B — Railway
[railway.app](https://railway.app) → **New Project → Deploy from GitHub repo** → it auto-detects the Dockerfile → add `NVIDIA_API_KEY` (optional) → Deploy.

### Option C — Google Cloud Run
```bash
gcloud run deploy prospect-assist-ai --source . --region asia-south1 \
  --allow-unauthenticated --port 8000 --set-env-vars NVIDIA_API_KEY=nvapi-xxxx
```

### Verify any deployment
```bash
curl https://<your-url>/health          # {"ok": true, ...}
```

→ Paste the URL into deck slide 13 (**Final Product Link**) and the portal.

**Test the container locally first (optional):**
```bash
docker build -t prospect-assist-ai .
docker run -p 8000:8000 -e NVIDIA_API_KEY=$NVIDIA_API_KEY prospect-assist-ai
# open http://localhost:8000
```

---

## 3. Demo video (3 minutes)

Follow [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) — it's a beat-by-beat 3-minute script. Record screen + voiceover, upload **unlisted** to YouTube or Drive (link-shareable), and paste the link into deck slide 13.

---

## Submission checklist
- [ ] Team name + leader filled on deck slide 1
- [ ] GitHub repo pushed (public) → link on slide 13
- [ ] App deployed → live URL on slide 13, verified via `/health`
- [ ] 3-min demo video recorded + uploaded → link on slide 13
- [ ] Deck exported (the `.pptx` — or File → Export → PDF if the portal wants PDF)
- [ ] All three links pasted into the Hack2skill submission portal
