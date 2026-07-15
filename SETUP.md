# Darkroom Caption Lab — Setup & Deployment

## 1. Add your trained model files

Create a `model/` folder inside `flask_app/` and place these two files in it:

```
flask_app/
├── model/
│   ├── caption_model_3.keras       <- your Phase 3 init-inject model
│   └── phase1_artifacts.pkl        <- from Phase 1 (word_to_idx, idx_to_word, max_length)
├── app.py
├── requirements.txt
├── Dockerfile
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## 2. Run locally first (always test before deploying)

```bash
cd flask_app
pip install -r requirements.txt
python app.py
```

Open `http://localhost:7860` in your browser. Upload a photo, hit "Develop Caption," confirm it works before touching deployment. First request will be slow (~10-20s) since InceptionV3 and your model load into memory — this is normal, only happens once at startup, not per-request.

## 3. Deploy — pick one

### Option A: HuggingFace Spaces (recommended — free, good ML-community signal)

1. Create a new Space at huggingface.co/new-space
2. Choose **Docker** as the Space SDK (not Gradio/Streamlit — you're running raw Flask)
3. Push this whole `flask_app/` folder as the Space's repo:
   ```bash
   git init
   git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/darkroom-caption-lab
   git add .
   git commit -m "Initial deploy"
   git push origin main
   ```
4. The Space will build the Dockerfile automatically and serve on port 7860 — matches what's already set in `app.py` and the `Dockerfile`, no changes needed
5. **Model file size warning:** `caption_model_3.keras` is likely 30-80MB depending on your vocab size — well within HF Spaces' free tier limits, but if you used Git LFS-unfriendly upload methods, use `git lfs track "*.keras"` before committing

### Option B: Render (free tier)

1. Push this repo to GitHub
2. On Render: New → Web Service → connect your repo
3. Environment: Docker (it'll pick up the Dockerfile automatically)
4. Render sets its own `$PORT` env var — the app already reads `os.environ.get("PORT", 7860)`, so no code change needed
5. Free tier note: Render's free web services spin down after inactivity — first request after idle will be slow (~30s+) while it wakes up. Mention this if you link it on your resume so reviewers aren't confused by the delay.

## 4. After deploying

Add the live link to your README and resume bullet, e.g.:
> Deployed as an interactive web app (Flask, Docker) on HuggingFace Spaces — [link]

Test the live link yourself once before sharing it anywhere — confirm the model actually loaded correctly in the deployed environment (check the Space/Render logs for the "All models loaded. Ready to serve." message from `app.py`).
