from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Новый синтаксис OpenAI >= 1.0.0
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_with_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a CLIL methodology expert. Generate a list of classroom tasks for school teachers using the CLIL (Content and Language Integrated Learning) approach. Each task should:\n\n- follow one of the 15 formats (matching, short_answer, true_false, multiple_choice, fill_in_the_blank, ordering, open_ended, dialogue_completion, categorization, matching_definitions, gap_fill, table_completion, problem_solving, scenario_based, case_analysis);\n- integrate subject content, target language functions (e.g. define, explain, describe), and national or cultural values;\n- be written clearly and fully in one paragraph per task;\n- **do not number inner elements** inside the task body.\n\nUse the format:\nTask 1: ...\nTask 2: ..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

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
