# similarity.py
import re
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
import nltk

# Load local SentenceTransformer model
model = SentenceTransformer('./my_model')

def clean_text(text: str) -> str:
    return re.sub(r'[^\w\s]', '', text.lower())

def word_similarity(text1: str, text2: str):
    # Guard against empty
    if not text1.strip() or not text2.strip():
        return 0.0, []

    try:
        vecs = CountVectorizer().fit_transform([text1, text2]).toarray()
        cosine = np.dot(vecs[0], vecs[1]) / (np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[1]))
        words1 = set(clean_text(text1).split())
        words2 = set(clean_text(text2).split())
        common = list(words1 & words2)
        return round(cosine, 3), common
    except ValueError:
        return 0.0, []

def semantic_similarity(text1: str, text2: str, threshold: float = 0.7):
    if not text1.strip() or not text2.strip():
        return 0.0, []

    # Overall text embedding
    emb1_full = model.encode(text1, convert_to_tensor=True)
    emb2_full = model.encode(text2, convert_to_tensor=True)
    overall_score = util.cos_sim(emb1_full, emb2_full).item()

    # More robust sentence splitting using nltk
    sents1 = [s.strip() for s in sent_tokenize(text1) if len(s.split()) > 3]
    sents2 = [s.strip() for s in sent_tokenize(text2) if len(s.split()) > 3]

    paraphrases = []
    if sents1 and sents2:
        emb1 = model.encode(sents1, convert_to_tensor=True)
        emb2 = model.encode(sents2, convert_to_tensor=True)
        sim_matrix = util.cos_sim(emb1, emb2).cpu().numpy()

        seen = set()
        for i, s1 in enumerate(sents1):
            for j, s2 in enumerate(sents2):
                score = sim_matrix[i][j]
                if threshold <= score < 0.99:
                    key = (s1.lower(), s2.lower())
                    if key not in seen:
                        paraphrases.append((s1, s2, round(float(score), 3)))
                        seen.add(key)

    return round(float(overall_score), 3), paraphrases

def compare_texts(text1: str, text2: str):
    word_score, similar_words = word_similarity(text1, text2)
    semantic_score, paraphrased_phrases = semantic_similarity(text1, text2)
    return {
        "word_score": word_score,
        "similar_words": similar_words,
        "semantic_score": semantic_score,
        "paraphrased_phrases": paraphrased_phrases
    }
