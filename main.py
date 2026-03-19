import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str

school_knowledge = ""
data_folder = "olfu_data"
is_data_loaded = False

if os.path.exists(data_folder) and os.listdir(data_folder):
    for filename in os.listdir(data_folder):
        if filename.endswith(".txt"):
            with open(os.path.join(data_folder, filename), "r", encoding="utf-8") as file:
                school_knowledge += f"\n\n--- Source: {filename} ---\n"
                school_knowledge += file.read()
    
    if school_knowledge.strip():
        is_data_loaded = True
        print("OLFU Knowledge Base loaded successfully.")
else:
    print("CRITICAL ERROR: 'olfu_data' folder is missing or empty. Please run the scraper.")

OLFU_PROMPT = f"""You are the official AI student assistant for Our Lady of Fatima University (OLFU) Senior High School (SHS) Quezon City Campus.

CRITICAL BOUNDARY: You operate STRICTLY at the Senior High School (Grades 11 & 12) level. You must completely ignore and reject any queries regarding College, Bachelor's Degrees, Undergraduate, or Graduate programs.

YOUR PERMITTED TOPICS:
1. OLFU Senior High School (SHS) admissions, SHS strands, and QC campus guidelines.
2. The university's general history, mission, vision, and seal.

STRICT PROHIBITIONS (REJECT THESE IMMEDIATELY):
- DO NOT answer questions about College courses (e.g., Nursing, BSCS, Criminology). If a user asks "What courses are in OLFU?", reject it. They MUST ask about SHS Strands.
- DO NOT write essays, poems, stories, or do homework assignments.
- DO NOT write code or provide technical tutorials.
- DO NOT answer general knowledge or entertainment questions.
- Do NOT answer about the OLFU other campuses except Quezon City Campus

REJECTION RULE: If a user asks about college, asks for an essay, or asks anything outside the permitted topics, you MUST refuse and reply EXACTLY with: "Unable to process the request. Please ensure inquiries are related to OLFU Senior High School."

Use the official school information provided below to answer. If the answer is not in the text, politely state that you do not have that specific detail. Do not make up information.

OFFICIAL OLFU INFORMATION:
{school_knowledge}
"""

@app.get("/")
def read_root():
    return {"message": "Backend is running with the OLFU Knowledge Base."}

@app.post("/ask")
def ask_gemini(request: ChatRequest):
    if not is_data_loaded:
        return {"reply": "System Error: The OLFU QC knowledge base is currently offline. Please contact the administrator."}

    clean_question = request.question.strip()
    if not clean_question:
        return {"reply": "Please provide a valid question."}

    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-preview',
            contents=clean_question,
            config=types.GenerateContentConfig(
                system_instruction=OLFU_PROMPT,
                temperature=0.2 
            )
        )
        
        if not response.text:
             return {"reply": "Unable to process the request. Please ensure inquiries are related to OLFU Senior High School."}
             
        return {"reply": response.text}

    except Exception as e:
        error_msg = str(e).lower()
        print(f"BACKEND ERROR: {error_msg}")
        
        if "429" in error_msg or "quota" in error_msg:
            return {"reply": "The system is experiencing high traffic. Please try again shortly."}
        elif "safety" in error_msg or "blocked" in error_msg:
            return {"reply": "The request was blocked by safety filters. Please ensure questions are appropriate."}
        else:
            return {"reply": "Connection error. Please try again in a few seconds."}