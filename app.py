"""
Darkroom Caption Lab — Flask backend for the image-captioning capstone project.

Loads the trained CNN+LSTM (init-inject) model, a frozen InceptionV3 feature
extractor for new uploaded images, and the vocabulary built in Phase 1.
Serves a single-page UI and a /generate endpoint that returns a caption.
"""

import os
import pickle
import numpy as np
from flask import Flask, request, jsonify, render_template
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import InceptionV3
from tensorflow.keras.applications.inception_v3 import preprocess_input
from tensorflow.keras.preprocessing.sequence import pad_sequences

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(APP_DIR, "model", "caption_model_1.keras")
ARTIFACTS_PATH = os.path.join(APP_DIR, "model", "phase1_artifacts.pkl")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Load everything once at startup — not per-request, that would be far too slow
# ---------------------------------------------------------------------------
print("Loading vocabulary and config...")
with open(ARTIFACTS_PATH, "rb") as f:
    artifacts = pickle.load(f)

word_to_idx = artifacts["word_to_idx"]
idx_to_word = artifacts["idx_to_word"]
MAX_LENGTH = artifacts["max_length"]

print("Loading trained caption model...")
caption_model = load_model(MODEL_PATH)

print("Loading frozen InceptionV3 feature extractor...")
feature_extractor = InceptionV3(weights="imagenet", include_top=False, pooling="avg")
feature_extractor.trainable = False

print("All models loaded. Ready to serve.")

# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

def extract_feature(pil_image):
    """Preprocess a PIL image and run it through the frozen CNN encoder."""
    img = pil_image.convert("RGB").resize((299, 299))
    arr = np.array(img).astype("float32")
    arr = preprocess_input(arr)
    arr = np.expand_dims(arr, axis=0)
    feature = feature_extractor.predict(arr, verbose=0)[0]
    return feature


def generate_caption_greedy(image_feat, max_length=MAX_LENGTH):
    in_seq = [word_to_idx["startseq"]]
    for _ in range(max_length):
        padded = pad_sequences([in_seq], maxlen=max_length, padding="post")
        preds = caption_model.predict([np.expand_dims(image_feat, 0), padded], verbose=0)
        next_idx = int(np.argmax(preds[0]))
        if idx_to_word[next_idx] == "endseq":
            break
        in_seq.append(next_idx)
    words = [idx_to_word[i] for i in in_seq[1:]]
    return " ".join(words)


def generate_caption_beam(image_feat, beam_width=3, max_length=MAX_LENGTH):
    start = [word_to_idx["startseq"]]
    sequences = [(start, 0.0)]

    for _ in range(max_length):
        all_candidates = []
        for seq, score in sequences:
            if idx_to_word[seq[-1]] == "endseq":
                all_candidates.append((seq, score))
                continue
            padded = pad_sequences([seq], maxlen=max_length, padding="post")
            preds = caption_model.predict([np.expand_dims(image_feat, 0), padded], verbose=0)[0]
            top_k = np.argsort(preds)[-beam_width:]
            for idx in top_k:
                candidate_seq = seq + [int(idx)]
                candidate_score = score + np.log(preds[idx] + 1e-10)
                all_candidates.append((candidate_seq, candidate_score))

        ordered = sorted(all_candidates, key=lambda x: x[1] / len(x[0]), reverse=True)
        sequences = ordered[:beam_width]

        if all(idx_to_word[seq[-1]] == "endseq" for seq, _ in sequences):
            break

    best_seq = sequences[0][0]
    words = [idx_to_word[i] for i in best_seq[1:] if idx_to_word[i] != "endseq"]
    return " ".join(words)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded."}), 400

    file = request.files["image"]
    method = request.form.get("method", "beam")

    try:
        pil_image = Image.open(file.stream)
    except Exception:
        return jsonify({"error": "Could not read image file."}), 400

    feature = extract_feature(pil_image)

    if method == "greedy":
        caption = generate_caption_greedy(feature)
    else:
        caption = generate_caption_beam(feature, beam_width=3)

    return jsonify({"caption": caption, "method": method})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)
