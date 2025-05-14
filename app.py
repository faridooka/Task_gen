from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import tempfile
import os
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_with_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a CLIL methodology expert. Generate classroom tasks for teachers that integrate subject content (e.g., biology), target language functions (e.g., describe, explain), and national or cultural values. The tasks must help learners improve both academic subject knowledge and language skills simultaneously. Respond in numbered format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message["content"]

@app.route("/generate_gpt", methods=["POST"])
def generate_gpt():
    data = request.json
    topic = data["topic"]
    format_type = data["format"]
    level = data["level"]
    count = int(data["count"])
    subject = data.get("subject", "General")

    prompt = f"Create {count} classroom tasks for the subject '{subject}' on the topic '{topic}', in the format '{format_type}', " \
             f"and at the difficulty level '{level}'. Each task must integrate content knowledge, a language function (e.g., explain, define), " \
             f"and a cultural or national value. Format: Task 1: ..., Task 2: ..., etc."

    result = generate_with_gpt(prompt)
    return jsonify({"tasks": result.split("\n"), "answers": ["(See above)"]})

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
    c.setFont("Helvetica", 12)
    c.drawString(50, y, "CLIL Tasks")
    y -= 30
    for i, task in enumerate(tasks, start=1):
        lines = c.beginText(50, y)
        lines.textLine(f"{i}. {task}")
        c.drawText(lines)
        y -= 40
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    return send_file(temp_file.name, as_attachment=True, download_name="clil_tasks.pdf")

if __name__ == "__main__":
    app.run(debug=True)
