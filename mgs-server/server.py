from flask import Flask, request, jsonify
from gensim.models import KeyedVectors
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CORS(app)

print("Loading model...")
model = KeyedVectors.load_word2vec_format("GoogleNews-vectors-negative300.bin", binary=True)
print("Model loaded!")

def is_variant(candidate, inputs):
    cand_lower = candidate.lower()
    for w in inputs:
        wl = w.lower()
        if cand_lower == wl:  # 完全一样
            return True
        if cand_lower in [wl + "s", wl + "es"]:  # 简单复数
            return True
    return False

@app.route("/vector_arithmetic", methods=["POST"])
def vector_arithmetic():
    data = request.get_json()
    words = data.get("words", [])
    topk = int(data.get("topk", 5))  # 默认 top1

    if not words:
        return jsonify({"error": "No words provided"}), 400

    try:
        result_vec = None
        for w in words:
            if w.startswith("-"):
                vec = -model[w[1:]]
            else:
                vec = model[w]
            result_vec = vec if result_vec is None else result_vec + vec

        similars = model.similar_by_vector(result_vec, topn=topk)
        results = [{"word": w, "score": float(s)} for w, s in similars]
        return jsonify({"results": results})


    except KeyError as e:
        return jsonify({"error": f"Word not in vocabulary: {str(e)}"}), 400


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    words = data.get("words", [])
    topk = int(data.get("topk", 5))  

    if not words:
        return jsonify({"error": "No words provided"}), 400

    try:
        # === 1. embedding arithmetic ===
        semantic_vec = (model['dragon'] + model['knight'] + model['magic']) / 3
        result_vec = None
        for w in words:
            if w.startswith("-"):
                key = w[1:]
                if key not in model:
                    return jsonify({"error": f"Word not in vocabulary: {key}"}), 400
                vec = -model[key]
            else:
                if w not in model:
                    return jsonify({"error": f"Word not in vocabulary: {w}"}), 400
                vec = model[w]
            result_vec = vec if result_vec is None else result_vec + vec + semantic_vec

        # === 2. nearest neighbors ===
        similars = model.similar_by_vector(result_vec, topn=topk)
        raw_results = [{"word": w, "score": float(s)} for w, s in similars]
        results = [item for item in raw_results if not is_variant(item["word"], words)]



        # === 4. construct GPT prompt ===
        # 给 LLM 多个候选词，让它选择最合适的
        candidates_text = ", ".join([item["word"] for item in results[:5]])  # 取前 top5
        words_text = ", ".join([item for item in words])  # 取前 top5
        print("words_text:", words_text)
        full_prompt = f"""
        You are selecting a fantasy-themed card keyword.
        Here are the candidate words: {candidates_text}.

        Task:
        1. Choose the one word that best fits the theme of a fantasy world card game.
        2. Generate a one-sentence imaginative description for that word.
        3. Don't choose words that is a variant of another (e.g., plural form) in the input list:
        {words_text}

        Return the result in JSON format with two keys:
        - "word": the chosen word
        - "description": the description text

        Do not add extra commentary, return valid JSON only.
        """

        # === 5. call GPT model ===
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": full_prompt}]
        )

        # 解析 GPT 返回的 JSON
        
        try:
            chosen = json.loads(resp.choices[0].message.content.strip())
        except Exception:
            chosen = {
                "word": results[0]["word"],
                "description": resp.choices[0].message.content.strip()
            }

        return jsonify({
            "candidates": results,
            "chosen": {
                "word": chosen["word"],
                "description": chosen["description"],
                "score": next((item["score"] for item in results if item["word"] == chosen["word"]), results[0]["score"])
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
