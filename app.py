from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import os
import tempfile
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_with_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a CLIL expert and task designer. Follow instructions strictly."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

@app.route("/generate_gpt", methods=["POST"])
def generate_gpt():
    data = request.json
    topic = data.get("topic", "Informatics")
    english_level = data.get("english_level", "A2")
    bloom_level = data.get("bloom_level", "Understand")
    task_type = data.get("task_type", "question")

    prompt = (
        f"Create CLIL-based tasks for the topic '{topic}' in Informatics.\n"
        f"Include the 3 CLIL components:\n"
        f"📖 Reading – task requiring reading/comprehension.\n"
        f"✍️ Writing – task requiring written expression.\n"
        f"🗣️ Speaking – task requiring verbal explanation.\n\n"
        f"Each task should be 1–2 sentences.\n"
        f"English level: {english_level}\n"
        f"Bloom's taxonomy level: {bloom_level}\n"
        f"Task type: {task_type}\n\n"
        f"Return JSON format:\n"
        f'{{"reading": "...", "writing": "...", "speaking": "..."}}'
    )

    try:
        result_text = generate_with_gpt(prompt)
        import json
        result_json = json.loads(result_text)
    except Exception:
        result_json = {
            "reading": f"'{topic}' тақырыбына байланысты мәтінді оқып, негізгі ақпаратты бөліп көрсетіңіз.",
            "writing": f"'{topic}' тақырыбы бойынша қысқаша мақала жазыңыз.",
            "speaking": f"'{topic}' тақырыбын ауызша түсіндіріп беріңіз."
        }

    tasks = [
        "📖 Reading: " + result_json.get("reading", ""),
        "✍️ Writing: " + result_json.get("writing", ""),
        "🗣️ Speaking: " + result_json.get("speaking", "")
    ]
    return jsonify({"tasks": tasks})

@app.route("/download_docx", methods=["POST"])
def download_docx():
    data = request.json
    tasks = data.get("tasks", [])
    doc = Document()
    doc.add_heading('CLIL Tasks', level=1)
    for i, task in enumerate(tasks, start=1):
        doc.add_paragraph(f"{i}. {task}")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    return send_file(temp_file.name, as_attachment=True, download_name="clil_tasks.docx")

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    data = request.json
    tasks = data.get("tasks", [])

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=letter)

    width, height = letter
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "CLIL Tasks")
    y -= 30

    c.setFont("Helvetica", 12)
    for i, task in enumerate(tasks, start=1):
        lines = [f"{i}. {task}"]
        for line in lines:
            c.drawString(50, y, line)
            y -= 20
            if y < 60:
                c.showPage()
                y = height - 50

    c.save()
    return send_file(temp_file.name, as_attachment=True, download_name="clil_tasks.pdf")

if __name__ == "__main__":
    app.run(debug=True)
