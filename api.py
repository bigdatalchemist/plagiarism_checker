# api.py
from flask import Blueprint, request, jsonify
from utils.utils import extract_text_from_file
from utils.webscraper import extract_text_from_url
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from config import SYSTEM_PAGE_LIMIT

api = Blueprint('api', __name__)

model = SentenceTransformer('./my_model')
SYSTEM_PAGE_LIMIT = 10

def word_similarity(text1, text2):
    if not text1.strip() or not text2.strip():
        return 0.0, []

    try:
        vectorizer = CountVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        cosine = np.dot(vectors[0], vectors[1]) / (
            np.linalg.norm(vectors[0]) * np.linalg.norm(vectors[1])
        )
        similar_words = set(text1.lower().split()) & set(text2.lower().split())
        return round(cosine, 2), list(similar_words)
    except ValueError:
        return 0.0, []

def semantic_similarity(text1, text2):
    if not text1.strip() or not text2.strip():
        return 0.0, []

    embedding1 = model.encode(text1, convert_to_tensor=True)
    embedding2 = model.encode(text2, convert_to_tensor=True)
    similarity = util.cos_sim(embedding1, embedding2).item()

    sentences1 = [s.strip() for s in text1.split(".") if len(s.strip().split()) > 3]
    sentences2 = [s.strip() for s in text2.split(".") if len(s.strip().split()) > 3]

    paraphrased = []
    seen_pairs = set()

    for s1 in sentences1:
        for s2 in sentences2:
            sim_score = util.cos_sim(
                model.encode(s1, convert_to_tensor=True),
                model.encode(s2, convert_to_tensor=True)
            ).item()
            if 0.6 < sim_score < 0.98:
                pair = (s1.lower(), s2.lower())
                if pair not in seen_pairs:
                    paraphrased.append((s1, s2, round(sim_score, 2)))
                    seen_pairs.add(pair)

    return round(similarity, 2), paraphrased

@api.route("/api/check", methods=["POST"])
def api_check():
    try:
        mode = request.form.get("mode", "text")
        pages = int(request.form.get("pages", 1))
        pages = min(pages, SYSTEM_PAGE_LIMIT)

        text1, text2 = "", ""

        if mode == "text":
            text1 = request.form.get("text1", "").strip()
            text2 = request.form.get("text2", "").strip()
            if not text1 or not text2:
                return jsonify({"error": "Both text fields are required."}), 400

        elif mode == "file":
            file1 = request.files.get("file1")
            file2 = request.files.get("file2")
            if not file1 or not file2:
                return jsonify({"error": "Both files must be uploaded."}), 400
            text1, len1, _ = extract_text_from_file(file1, pages)
            text2, len2, _ = extract_text_from_file(file2, pages)
            if len1 == 0 or len2 == 0:
                return jsonify({"error": "Insufficient text extracted from one or both files."}), 400

        elif mode == "url":
            url1 = request.form.get("url1", "").strip()
            url2 = request.form.get("url2", "").strip()
            if not url1 or not url2:
                return jsonify({"error": "Both URLs are required."}), 400
            text1, len1 = extract_text_from_url(url1)
            text2, len2 = extract_text_from_url(url2)
            if len1 < 100 or len2 < 100:
                return jsonify({"error": "Insufficient content extracted from one or both URLs."}), 400

        else:
            return jsonify({"error": "Invalid mode."}), 400

        word_score, similar_words = word_similarity(text1, text2)
        semantic_score, paraphrased_phrases = semantic_similarity(text1, text2)

        return jsonify({
            "word_score": word_score,
            "semantic_score": semantic_score,
            "similar_words": similar_words,
            "paraphrased_phrases": [
                {
                    "sentence1": p[0],
                    "sentence2": p[1],
                    "similarity": p[2]
                } for p in paraphrased_phrases
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
