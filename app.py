from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openai import OpenAI
import json

app = Flask(__name__)

# 👇 Тек осы сайтқа рұқсат береміз
CORS(app, origins=["https://cliledu.kz"])

# 👇 Барлық жауаптарға CORS headers қосу
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://cliledu.kz')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# ✅ OpenAI клиенті
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_with_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a CLIL methodology expert. Generate a set of tasks using the CLIL approach (reading, writing, speaking)."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

@app.route("/generate_gpt", methods=["POST", "OPTIONS"])
def generate_gpt():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight"}), 200

    data = request.json
    topic = data.get("topic", "Unknown Topic")

    prompt = (
        f"Generate one CLIL-based task set for the topic '{topic}' in the subject 'Informatics'.\n"
        f"Use three integrated parts:\n"
        f"📖 Reading – A task that asks the learner to read and understand the topic.\n"
        f"✍️ Writing – A task that asks the learner to write or express in written form.\n"
        f"🗣️ Speaking – A task that asks the learner to explain or describe the topic verbally.\n\n"
        f"Each part should be 1–2 sentences long and clearly related to informatics.\n"
        f"Return in JSON format like:\n"
        f'{{"reading": "...", "writing": "...", "speaking": "..."}}'
    )

    try:
        result_text = generate_with_gpt(prompt)
        result_json = json.loads(result_text)
    except Exception:
        result_json = {
            "reading": f"Осы тақырыпқа қатысты мәтінді оқып, негізгі идеяларын анықтаңыз.",
            "writing": f"'{topic}' тақырыбы бойынша өз ойыңызды жазбаша түрде білдіріңіз.",
