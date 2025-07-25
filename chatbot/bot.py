import os
import json
import sqlite3
import pytesseract
from PIL import ImageGrab
import fitz  # PyMuPDF
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

# ========================
# Load configuration
# ========================
with open("config/config.json", "r") as f:
    config = json.load(f)

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = config.get("tesseract_path", r"C:\Users\ronal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")

# Ensure TESSDATA_PREFIX is set
tessdata_path = r"C:\Users\ronal\AppData\Local\Programs\Tesseract-OCR\tessdata"
if not os.environ.get("TESSDATA_PREFIX"):
    os.environ["TESSDATA_PREFIX"] = tessdata_path

# Check if tessdata exists
if not os.path.exists(os.environ["TESSDATA_PREFIX"]):
    print(f"⚠ Warning: TESSDATA_PREFIX path not found: {os.environ['TESSDATA_PREFIX']}")
    print("Please make sure tessdata folder exists and contains eng.traineddata.")

# Set API Key
os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]

# ========================
# LangChain configuration
# ========================
agent = ChatGoogleGenerativeAI(
    model=config["MODEL_NAME"],
    google_api_key=config["GOOGLE_API_KEY"]
)

# Load prompt templates
with open("prompt/prompt.txt", "r", encoding="utf-8") as f:
    prompt_template = f.read()

with open("prompt/prompt_question.txt", "r", encoding="utf-8") as f:
    prompt_template_question = f.read()

with open("prompt/prompt_resume.txt", "r", encoding="utf-8") as f:
    prompt_template_resume = f.read()

# Create PromptTemplate objects
prompt = PromptTemplate(input_variables=["q"], template=prompt_template)
prompt_question = PromptTemplate(input_variables=["question"], template=prompt_template_question)
prompt_resume = PromptTemplate(input_variables=["resume"], template=prompt_template_resume)

# Chain setup
llm_chain = prompt | agent
llm_chain_question = prompt_question | agent
llm_chain_resume = prompt_resume | agent

# Stop words
stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}

def filter_stop_words(keywords):
    """Remove stop words"""
    return [word.lower() for word in keywords if word.lower() not in stop_words]

def get_bot_answer(question):
    """Get chatbot answer"""
    response = llm_chain.invoke(question)
    return response.content

def get_bot_answer_question(question):
    """Get chatbot answer for screenshot questions"""
    response = llm_chain_question.invoke(question)
    return response.content

def get_bot_answer_resume(resume):
    """Get chatbot answer for resume processing"""
    response = llm_chain_resume.invoke(resume)
    return response.content

def get_kg_answer(query, db_name="knowledge/knowledge.db", top_n=3):
    """Get knowledge base answer"""
    import re
    keywords = re.findall(r'\b\w+\b', query.lower())
    filtered_keywords = filter_stop_words(keywords)

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    results = []
    for keyword in filtered_keywords:
        cursor.execute("SELECT question, answer FROM knowledge WHERE question LIKE ?", ('%' + keyword + '%',))
        results += cursor.fetchall()
    conn.close()
    return list(set(results))[:top_n]

def capture_and_extract_text():
    """Capture full screen and extract text using Tesseract OCR"""
    screenshot = ImageGrab.grab()
    screenshot_path = "assets/screenshot.png"
    screenshot.save(screenshot_path)

    try:
        text = pytesseract.image_to_string(screenshot, lang="eng")
        return text
    except pytesseract.TesseractError as e:
        print("❌ Tesseract OCR Error:", str(e))
        print("Please check if Tesseract is installed and TESSDATA_PREFIX is set.")
        return ""
    except Exception as e:
        print("Unexpected error during OCR:", str(e))
        return ""

def generate_prompt(file_path):
    """Extract resume text from PDF and generate prompt.txt"""
    doc = fitz.open(file_path)
    resume = ""
    for page in doc:
        resume += page.get_text("text")

    extracted_info = get_bot_answer_resume(resume) + \
        "\n\nAbove is all your information. Answer questions briefly and to the point. You are currently looking for internship opportunities, and now you want to apply your skills to practical work. In this interview, your job is to answer my questions clearly. Your answers should be concise and to the point. No need to be overly formal, just talk normally with the interviewer. You should focus on clearly explaining your thought process, using practical examples (if applicable). Avoid using too much jargon unless necessary, and strive for answers that are concise and demonstrate your technical abilities. I will ask you some technical questions. Your task is to answer questions in a way that shows you are suitable for this role. Whatever the interviewer asks you, be sure to answer in English. Question: {q} Answer: "

    with open("prompt/prompt.txt", "w", encoding="utf-8") as f:
        f.write(extracted_info)
    print("✅ prompt.txt has been generated successfully")
