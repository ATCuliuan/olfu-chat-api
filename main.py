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

OLFU_PROMPT = f"""You are the official student assistant for Our Lady of Fatima University (OLFU) Senior High School, specifically for the Quezon City (QC) Campus.

Your ONLY job is to answer questions about OLFU SHS admissions, the QC Campus, SHS Strands, and school guidelines.

RULE 1: If a user asks a question that is NOT related to OLFU or Senior High School, you MUST reply with EXACTLY: "I'm sorry, but I am programmed to only answer questions related to OLFU Senior High School."
RULE 2: Use the official school information provided below to answer the user's questions accurately. If the answer is not in the information below, politely state that you don't have that specific detail.

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