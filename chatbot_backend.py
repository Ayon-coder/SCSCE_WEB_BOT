# ===============================================================
# SCCSE Chatbot Backend (FIXED VERSION WITH OFF-TOPIC PROTECTION)
# ===============================================================

import os
import logging
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage

from pdf import get_index
from chat_db import init_db, save_message, get_user_messages, save_summary, get_last_summary
from prompts import new_prompt, instruction_str  # Import your strict prompts

# Initialize DB
init_db()

# ---------------------------------------------------------------
# Basic Setup
# ---------------------------------------------------------------
logging.getLogger().setLevel(logging.ERROR)
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTES_FILE = os.path.join(BASE_DIR, "notes.txt")
PASS_KEY = "admin123"

os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(NOTES_FILE):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        f.write("🗒️ SCCSE Notes Log\n")

# ---------------------------------------------------------------
# LLM Setup
# ---------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("❌ Set GROQ_API_KEY in .env")

llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0.0  # ⚠️ SET TO 0 FOR STRICT ADHERENCE
)

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    cache_folder="./embedding_cache"
)

Settings.llm = llm
Settings.embed_model = embed_model

# ---------------------------------------------------------------
# Load PDF
# ---------------------------------------------------------------
pdf_path = os.path.join(DATA_DIR, "sccse.pdf")
if not os.path.exists(pdf_path):
    raise FileNotFoundError("❌ sccse.pdf missing inside /data folder")

sccse_pdf = PDFReader().load_data(file=pdf_path)
sccse_index = get_index(sccse_pdf, "sccse")

# Create a simple retriever for RAG
sccse_retriever = sccse_index.as_retriever(similarity_top_k=3)

# ---------------------------------------------------------------
# Memory System (Per-User)
# ---------------------------------------------------------------
# Store separate memory for each user
user_memories = {}

def get_user_memory(user_id):
    """Get or create memory buffer for a specific user"""
    if user_id not in user_memories:
        user_memories[user_id] = ChatMemoryBuffer.from_defaults(token_limit=50)
    return user_memories[user_id]

pending_note = None
pending_delete = False


# ---------------------------------------------------------------
# OFF-TOPIC DETECTION (Code-Level Safety Net)
# ---------------------------------------------------------------
def is_off_topic(query: str) -> bool:
    """
    Pre-filter off-topic queries before they reach the LLM.
    This is a safety net in case the LLM ignores prompts.
    """
    query_lower = query.lower().strip()
    
    # Allow greetings and casual chat
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
                 'how are you', 'what\'s up', 'whats up', 'sup', 'yo', 'greetings',
                 'thank you', 'thanks', 'bye', 'goodbye', 'see you', 'ok', 'okay',
                 'yes', 'no', 'sure', 'alright', 'cool', 'nice', 'great']
    
    if any(greeting == query_lower or query_lower.startswith(greeting + ' ') for greeting in greetings):
        return False
    
    # Allow very short queries (likely greetings or follow-ups)
    if len(query_lower) <= 10 and '?' not in query_lower:
        return False
    
    # Whitelist: If query mentions SCCSE, it's on-topic
    sccse_keywords = ['sccse', 'team', 'teams', 'event', 'events', 'member', 'members', 
                      'join', 'chapter', 'activity', 'activities', 'club']
    has_sccse = any(keyword in query_lower for keyword in sccse_keywords)
    
    if has_sccse:
        return False
    
    # Blacklist: Common off-topic patterns
    off_topic_patterns = [
        'what is python', 'what is dsa', 'what is java', 'what is ai',
        'how to learn', 'explain', 'who is the founder', 'who founded',
        'what is nasa', 'what is machine learning', 'what is programming',
        'how do i code', 'teach me', 'tutorial', 'solve this problem',
        'what is 2+2', 'calculate', 'what is the capital', 'who is president',
        'what is variable', 'what is function', 'what is algorithm',
        'debug this', 'fix my code', 'what is recursion', 'what is oop',
        'write a program', 'write code', 'help me code'
    ]
    
    has_off_topic = any(pattern in query_lower for pattern in off_topic_patterns)
    
    if has_off_topic:
        return True
    
    # Additional check: Single-word technical queries (but not greetings)
    single_word_tech = ['python', 'java', 'dsa', 'nasa', 'algorithm', 'variable', 
                        'recursion', 'oop', 'debugging', 'malloc', 'pointer', 'coding']
    words = query_lower.split()
    if len(words) <= 2 and any(tech in query_lower for tech in single_word_tech):
        return True
    
    return False


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def read_notes():
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


def append_note(text):
    try:
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n- {text.strip()}")
    except:
        pass


def generate_summary_if_needed(user_id):
    history = get_user_messages(user_id, limit=50)

    if len(history) < 20:
        return

    last_summary = get_last_summary(user_id)
    if last_summary:
        return

    convo_text = "\n".join([f"{r[0]}: {r[1]}" for r in history])

    prompt = f"""
    Summarize the user's skills and SCCSE-related preferences.

    Conversation:
    {convo_text}
    """

    result = llm.complete(prompt)
    summary = result.text.strip()

    save_summary(user_id, summary)


# ---------------------------------------------------------------
# Extract skills from any text
# ---------------------------------------------------------------
skill_map = {
    "tech": [
        "python", "java", "c++", "coding", "programming",
        "machine learning", "ml", "ai", "deeplearning",
        "web dev", "web development", "backend", "frontend",
        "data analysis", "data science", "algorithms",
        "dsa", "problem solving", "cloud", "docker",
    ],

    "design": [
        "figma", "ui", "ux", "graphic design", "illustration",
        "photoshop", "canva", "poster", "banner", "logo",
        "video editing", "editing", "premiere pro", "after effects",
    ],

    "pr": [
        "communication", "public speaking", "convincing",
        "talking to strangers", "teamwork", "leadership",
        "event management", "content writing", "storytelling",
        "social media", "marketing", "negotiation",
        "presentation", "anchoring", "community building"
    ]
}


def detect_skill_origin(user_id):
    """Determines whether skills came from MEMORY or SUMMARY."""
    # Get this user's specific memory
    memory = get_user_memory(user_id)
    
    memory_text = " ".join([
        m.content.lower() for m in memory.get_all() if m.role == "user"
    ])

    # Check memory first
    for team, words in skill_map.items():
        if any(w in memory_text for w in words):
            return "memory", team

    # Check summary next
    summary = get_last_summary(user_id)
    if summary:
        s = summary.lower()
        for team, words in skill_map.items():
            if any(w in s for w in words):
                return "summary", team

    return None, None


# ---------------------------------------------------------------
# MAIN CHAT FUNCTION
# ---------------------------------------------------------------
def get_chat_response(message: str, user_name=None, user_id=None):

    global pending_note, pending_delete

    msg_lower = message.lower().strip()
    
    # Get this user's specific memory
    memory = get_user_memory(user_id)

    # Save user message to DB
    save_message(user_id, "user", message)

    # -----------------------------------------------------------
    # ⚠️ OFF-TOPIC FILTER (Applied FIRST, before anything else)
    # -----------------------------------------------------------
    if is_off_topic(message):
        off_topic_response = "I'm sorry, but I can only help with SCCSE-related information."
        save_message(user_id, "assistant", off_topic_response)
        return off_topic_response

    # -----------------------------------------------------------
    # If user asks "what is my name?"
    # -----------------------------------------------------------
    if "what is my name" in msg_lower:
        return f"Your name is {user_name}." if user_name else "I don't know your name."

    # -----------------------------------------------------------
    # Passkey responses
    # -----------------------------------------------------------
    if pending_note:
        if msg_lower == PASS_KEY:
            append_note(pending_note)
            text = pending_note
            pending_note = None
            return f"✅ Note saved: '{text}'"
        return "🚫 Incorrect passkey. Try again."

    if pending_delete:
        if msg_lower == PASS_KEY:
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                f.write("🗒️ SCCSE Notes Log\n")
            pending_delete = False
            return "🗑️ All notes have been deleted successfully."
        return "🚫 Incorrect passkey. Try again."

    # -----------------------------------------------------------
    # Note saving request
    # -----------------------------------------------------------
    if msg_lower.startswith("note that"):
        pending_note = message.split("note that", 1)[-1].strip()
        return "🔐 This action requires the admin passkey. Please provide the passkey."

    # -----------------------------------------------------------
    # Delete notes request
    # -----------------------------------------------------------
    if "delete notes.txt" in msg_lower or "clear notes" in msg_lower:
        pending_delete = True
        return "🔐 This action requires the admin passkey. Please provide the passkey."

    # -----------------------------------------------------------
    # Handling "how do you know my skills?"
    # -----------------------------------------------------------
    if "how do you know" in msg_lower or "how did you know" in msg_lower:
        origin, team = detect_skill_origin(user_id)

        if origin == "memory":
            return "You mentioned your skills earlier in the conversation."
        elif origin == "summary":
            return "I remembered it from the summary of our earlier conversations."
        else:
            return "I can only rely on what you've shared during our chats."

    # -----------------------------------------------------------
    # EVENT QUERY HANDLING (Special case - check notes first)
    # -----------------------------------------------------------
    event_keywords = ['event', 'evnt', 'upcoming', 'schedule', 'when is', 'tournament', 'competition']
    
    if any(keyword in msg_lower for keyword in event_keywords):
        notes_content = read_notes()
        
        # Check if there's actual event info in notes (not just the header)
        notes_lines = [line.strip() for line in notes_content.split('\n') if line.strip() and not line.startswith('🗒️')]
        
        if not notes_lines:
            # No events in notes
            response = "There are no upcoming events at the moment."
            save_message(user_id, "assistant", response)
            memory.put(ChatMessage(role="user", content=message))
            memory.put(ChatMessage(role="assistant", content=response))
            return response
        
        # If we have notes, let the RAG handle it (it will use notes data)
    
    # -----------------------------------------------------------
    # TEAM RECOMMENDATION LOGIC
    # -----------------------------------------------------------
    team_triggers = [
        "which team should i join",
        "what team should i join",
        "suggest a team",
        "which sccse team",
        "best team for me",
        "where should i join",
        "team should i join",  # Catches typos like "wchisch team should i join"
        "recommend a team",
        "which team",
        "what team"
    ]

    if any(t in msg_lower for t in team_triggers):

        origin, detected_team = detect_skill_origin(user_id)

        # No skills known → ask user
        if not detected_team:
            response = "You haven't told me about your skills yet. What are you good at?"
            save_message(user_id, "assistant", response)
            return response

        # Skill origin tracking
        memory.put(ChatMessage(role="assistant", content=f"[SKILL_ORIGIN:{origin}]"))

        if detected_team == "tech":
            response = "Based on your skills, you would be a great fit for the Tech Team!"
        elif detected_team == "design":
            response = "With your design-related skills, the Design Team suits you well!"
        elif detected_team == "pr":
            response = "Your communication and soft skills make you a strong fit for the PR Team!"
        
        save_message(user_id, "assistant", response)
        return response

    # -----------------------------------------------------------
    # NORMAL SCCSE RAG RESPONSE (Direct LLM call with custom prompt)
    # -----------------------------------------------------------
    
    # Retrieve relevant context from PDF
    retrieved_nodes = sccse_retriever.retrieve(message)
    pdf_context = "\n".join([node.text[:500] for node in retrieved_nodes])
    
    # Get notes
    notes_text = read_notes()
    
    # Build the prompt using our strict template
    system_prompt = f"""You are the SCCSE chatbot for the Students' Chapter of CSE at AOT.

QUERY: "{message}"

YOUR TASK:
1. If this is a GREETING (hi, hello, thanks, bye) → Respond warmly
2. If this is about SCCSE (teams, events, members, activities) → Answer using the data below
3. If this is OFF-TOPIC (Python, NASA, DSA, coding, math, general knowledge) → Respond ONLY: "I'm sorry, but I can only help with SCCSE-related information."

AVAILABLE INFORMATION:

NOTES (Most Recent & Important - Use This FIRST for events):
{notes_text}

PDF (General SCCSE Information):
{pdf_context}

CRITICAL RULES FOR EVENTS:
• If the query is about events/schedules, ONLY use information from the NOTES section above
• If NOTES section is empty or doesn't have event info, say: "There are no upcoming events at the moment."
• NEVER use old event information from the PDF for current event queries
• Events are time-sensitive - only trust the NOTES section

OTHER RULES:
• Answer directly and naturally - do NOT explain your reasoning
• NEVER mention "notes", "PDF", "data", or "according to"
• Just state the information as if you naturally know it
• For non-event queries, you can use PDF information
• If no information available: "I'm not sure about that. I only provide information related to SCCSE members, teams, events, and activities."

RESPONSE:"""
    
    # Call LLM directly with our strict prompt
    response = llm.complete(system_prompt)
    llm_answer = response.text.strip()

    # Save to memory + DB
    memory.put(ChatMessage(role="user", content=message))
    memory.put(ChatMessage(role="assistant", content=llm_answer))

    save_message(user_id, "assistant", llm_answer)
    generate_summary_if_needed(user_id)

    return llm_answer


# ---------------------------------------------------------------
# Debug mode
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Debug Mode ON")
    print("Testing off-topic detection...")
    
    test_queries = [
        "who is the founder of nasa",
        "what is python",
        "what teams does sccse have",
        "how to learn dsa"
    ]
    
    for q in test_queries:
        print(f"\nQuery: '{q}'")
        print(f"Off-topic: {is_off_topic(q)}")
    
    print("\n" + "="*50)
    print("Chat interface:")
    while True:
        text = input("You: ")
        print("Bot:", get_chat_response(text, user_name="DebugUser", user_id=1))
