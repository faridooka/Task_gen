from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from docx import Document
import openai
import zipfile

# 🔐 OpenAI кілті (арнайы .env арқылы сақтау ұсынылады)
openai.api_key = "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"

app = Flask(__name__)
CORS(app)

# 🔁 Flan-T5 моделін жүктеу
model_name = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# 🔄 Flan генерациялау функциясы
def generate_task_flan(topic, task_format, difficulty, language):
    prompt = (
        f"Generate 1 {task_format} educational task on the topic '{topic}'. "
        f"The difficulty level is {difficulty.lower()}. "
        f"Write the task in {language} language. "
        f"Provide 4 options labeled A), B), C), D) and clearly state the correct answer like 'Answer: A'."
    )
    inputs = tokenizer(prompt, return_tensors="pt", padding=True)
    outputs = model.generate(
        **inputs,
        max_length=300,
        do_sample=True,
        top_k=50,
        top_p=0.92,
        temperature=0.85,
        repetition_penalty=1.2
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

# 🔄 OpenAI генерациялау функциясы
def generate_task_openai(topic, task_format, difficulty, language):
    prompt = (
        f"Generate 1 {task_format} educational task on the topic '{topic}'. "
        f"The difficulty level is {difficulty.lower()}. "
        f"Write the task in {language} language. "
        f"Provide 4 options labeled A), B), C), D) and clearly state the correct answer like 'Answer: A'."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    return response["choices"][0]["message"]["content"].strip()

# 🔁 Негізгі генерациялау маршруты
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    topic = data.get("topic")
    task_format = data.get("format")
    difficulty = data.get("difficulty")
    language = data.get("language", "English")
    quantity = int(data.get("quantity", 1))
    model_choice = data.get("model", "Flan-T5")

    tasks = []
    answers = []

    for i in range(quantity):
        if model_choice == "Flan-T5":
            task_text = generate_task_flan(topic, task_format, difficulty, language)
        else:
            task_text = generate_task_openai(topic, task_format, difficulty, language)

        answer = "Unknown"
        if "Answer:" in task_text:
            answer = task_text.split("Answer:")[-1].strip()
            task_text = task_text.split("Answer:")[0].strip()

        tasks.append(f"Question {i+1}:\n{task_text}")
        answers.append(f"Answer {i+1}: {answer}")

    # DOCX файлдарға сақтау
    tasks_doc = Document()
    tasks_doc.add_heading(f"{task_format.title()} Tasks on '{topic}'", level=1)
    for t in tasks:
        tasks_doc.add_paragraph(t)
        tasks_doc.add_paragraph("-" * 40)
    tasks_doc.save("tasks.docx")

    answers_doc = Document()
    answers_doc.add_heading(f"Answers for '{topic}'", level=1)
    for a in answers:
        answers_doc.add_paragraph(a)
    answers_doc.save("answers.docx")

    # ZIP жасау
    with zipfile.ZipFile("all_files.zip", "w") as zipf:
        zipf.write("tasks.docx")
        zipf.write("answers.docx")

    return jsonify({
        "tasks": tasks,
        "answers": answers,
        "download_tasks_url": "/download/tasks",
        "download_answers_url": "/download/answers",
        "download_all_url": "/download/all"
    })

# 📦 Жүктеу маршруттары
@app.route("/download/tasks", methods=["GET"])
def download_tasks():
    return send_file("tasks.docx", as_attachment=True)

@app.route("/download/answers", methods=["GET"])
def download_answers():
    return send_file("answers.docx", as_attachment=True)

@app.route("/download/all", methods=["GET"])
def download_all():
    return send_file("all_files.zip", as_attachment=True)

# 🌐 Жай index бет (Render жұмыс істеп тұрғанын тексеру үшін)
@app.route("/", methods=["GET"])
def index():
    return "🟢 Generator service is running!"
