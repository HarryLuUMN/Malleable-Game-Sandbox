from flask import Flask, request, jsonify
from gensim.models import KeyedVectors
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CORS(app)

print("Loading model...")
model = KeyedVectors.load_word2vec_format("GoogleNews-vectors-negative300.bin", binary=True)
print("Model loaded!")

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
    prompt = "this is a simulation game about a fantasy world, choose a word that best fits the theme"

    if not words:
        return jsonify({"error": "No words provided"}), 400

    try:
        # === 1. 词向量算术 ===
        result_vec = None
        for w in words:
            if w.startswith("-"):
                vec = -model[w[1:]]
            else:
                vec = model[w]
            result_vec = vec if result_vec is None else result_vec + vec

        similars = model.similar_by_vector(result_vec, topn=topk)
        results = [{"word": w, "score": float(s)} for w, s in similars]

        # === 2. 构造 GPT prompt ===
        candidate_words = ", ".join([item["word"] for item in results])
        full_prompt = f"""
            The word embedding model has suggested these candidate words: {candidate_words}.
            Your task: based on the user prompt below, pick exactly one word from the candidate list.
            Do not invent new words, only select one from the list.

            User prompt: {prompt}
            Return only the selected word.
        """

        # === 3. 调用 GPT ===
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": full_prompt}]
        )

        chosen_word = resp.choices[0].message.content.strip()

        return jsonify({
            "candidates": results,
            "chosen": chosen_word
        })

    except KeyError as e:
        return jsonify({"error": f"Word not in vocabulary: {str(e)}"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
