import os
from flask import Flask, render_template, request
import spacy
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
import PyPDF2



nlp = spacy.load("en_core_web_sm")


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs("uploads", exist_ok=True)


def load_skill_list():
    skills = set()
    try:
        with open("skills_list.txt", "r", encoding="utf-8") as f:
            for line in f:
                skill = line.strip().lower()
                if skill:
                    skills.add(skill)
    except:
        print("Skill list file missing!")
    return skills


SKILL_LIBRARY = load_skill_list()


def extract_text(file):
    filename = secure_filename(file.filename)
    ext = filename.split(".")[-1].lower()
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    text = ""

    if ext == "pdf":
        reader = PyPDF2.PdfReader(filepath)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + " "
        return text

    elif ext == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        return text

    return ""


def preprocess(text):
    doc = nlp(text.lower())
    tokens = []

    for token in doc:
        if token.is_alpha and not token.is_stop:
            tokens.append(token.lemma_)
    return tokens


def extract_skills(tokens):
    extracted = set()

    
    for word in tokens:
        if word in SKILL_LIBRARY:
            extracted.add(word)

    
    text = " ".join(tokens)
    for skill in SKILL_LIBRARY:
        if " " in skill and skill in text:
            extracted.add(skill)

    return extracted


def match_skills(resume_skills, jd_skills):
    matched = resume_skills.intersection(jd_skills)
    missing = jd_skills - resume_skills

    partial = set()

    for skill in list(missing):
        for r in resume_skills:
         
            if skill[:4] == r[:4]:
                partial.add(skill)
                break

    missing = missing - partial
    return matched, partial, missing



def generate_chart(matched_count, missing_count):
    labels = ["Matched", "Missing"]
    values = [matched_count, missing_count]

    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.savefig("static/graph.png", dpi=100)
    plt.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    resume_file = request.files["resume"]
    jd_file = request.files["jobdesc"]

    resume_text = extract_text(resume_file)
    jd_text = extract_text(jd_file)

    resume_tokens = preprocess(resume_text)
    jd_tokens = preprocess(jd_text)

    resume_skills = extract_skills(resume_tokens)
    jd_skills = extract_skills(jd_tokens)

    matched, partial, missing = match_skills(resume_skills, jd_skills)

    generate_chart(len(matched), len(missing))

    recommendations = [f"Learn '{m}' to improve your match score." for m in missing]

    return render_template(
        "result.html",
        matched_skills=sorted(matched),
        partial_matches=sorted(partial),
        missing_skills=sorted(missing),
        recommendations=recommendations,
        resume_skills=sorted(resume_skills)
    )


if __name__ == "__main__":
    app.run(debug=True)
