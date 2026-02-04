# 🎓 AI-Powered College Helpdesk Chatbot

A web-based chatbot designed to assist students and faculty with college-related queries. This project uses a **rule-based approach first** and falls back to **AI (OpenAI GPT)** only when needed.

---

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [Customization](#customization)
- [Guardrails](#guardrails)
- [API Endpoints](#api-endpoints)
- [Future Enhancements](#future-enhancements)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **Rule-Based Responses**: Quick answers from a predefined knowledge base
- **AI Fallback**: Uses OpenAI GPT for unknown queries (optional)
- **Safety Guardrails**: Filters inappropriate, off-topic, and spam content
- **Modern UI**: Clean, responsive chat interface
- **Quick Suggestions**: One-click common questions
- **No Database Required**: Uses JSON file for knowledge base
- **Beginner Friendly**: Well-commented code throughout

---

## 📁 Project Structure

```
college_helpdesk_chatbot/
│
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── knowledge_base.json     # Predefined Q&A data
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
├── static/                 # Static files
│   ├── css/
│   │   └── style.css       # Styling
│   └── js/
│       └── chat.js         # Frontend logic
│
├── templates/              # HTML templates
│   └── index.html          # Chat interface
│
└── utils/                  # Utility modules
    ├── __init__.py         # Package initializer
    ├── rule_engine.py      # Pattern matching logic
    ├── ai_fallback.py      # OpenAI integration
    └── guardrails.py       # Safety checks
```

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download the Project

```bash
cd path/to/your/project/folder
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Edit `config.py`

1. **Set Your College Name**:
```python
COLLEGE_NAME = "Your College Name Here"
```

2. **Set OpenAI API Key** (Optional - for AI fallback):
```python
OPENAI_API_KEY = "your-openai-api-key-here"
```

Get your API key from: https://platform.openai.com/api-keys

3. **Adjust Other Settings** as needed:
- `SIMILARITY_THRESHOLD`: How strict the matching should be (0.0-1.0)
- `BLOCKED_WORDS`: Words to filter out
- `OFF_TOPIC_KEYWORDS`: Topics outside college scope

---

## ▶️ Running the Application

### Start the Server

```bash
python app.py
```

### Access the Chatbot

Open your browser and go to:
```
http://localhost:5000
```

You should see the chat interface!

---

## 🔄 How It Works

### Message Flow

```
User Message
     ↓
┌─────────────────┐
│   Guardrails    │  ← Check for safety, spam, off-topic
└────────┬────────┘
         ↓ (if safe)
┌─────────────────┐
│  Rule Engine    │  ← Search knowledge base for match
└────────┬────────┘
         ↓ (if no match)
┌─────────────────┐
│  AI Fallback    │  ← Get response from OpenAI
└────────┬────────┘
         ↓
   Bot Response
```

### Components Explained

1. **Guardrails** (`utils/guardrails.py`)
   - Validates input (not empty, not too long)
   - Checks for blocked/offensive words
   - Detects off-topic queries
   - Prevents personal info sharing

2. **Rule Engine** (`utils/rule_engine.py`)
   - Loads knowledge base from JSON
   - Preprocesses user query
   - Calculates similarity with patterns
   - Returns best matching response

3. **AI Fallback** (`utils/ai_fallback.py`)
   - Only used when rule engine fails
   - Sends query to OpenAI with strict system prompt
   - Returns AI-generated response

---

## 🎨 Customization

### Adding New Q&A Pairs

Edit `knowledge_base.json`:

```json
{
    "tag": "new_topic",
    "patterns": [
        "question pattern 1",
        "question pattern 2",
        "question pattern 3"
    ],
    "responses": [
        "Response 1",
        "Response 2"
    ]
}
```

### Changing the UI

- **Colors**: Edit CSS variables in `static/css/style.css`
- **Layout**: Modify `templates/index.html`
- **Behavior**: Update `static/js/chat.js`

### Adding More Blocked Words

Edit `config.py`:
```python
BLOCKED_WORDS = [
    "word1", "word2", "word3"
]
```

---

## 🛡️ Guardrails

The chatbot implements these safety measures:

| Guardrail | Description |
|-----------|-------------|
| Input Validation | Checks for empty, too short, or too long messages |
| Spam Detection | Blocks repeated characters, all caps, excessive punctuation |
| Blocked Words | Filters offensive or inappropriate terms |
| Off-Topic Filter | Redirects non-college queries |
| Personal Info Check | Prevents sharing phone numbers, emails, etc. |
| AI Prompt Control | Strict system instructions for AI responses |

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main chat interface |
| `/chat` | POST | Process chat message |
| `/health` | GET | Health check |

### Chat API Example

```javascript
// Request
POST /chat
Content-Type: application/json

{
    "message": "What is the admission process?"
}

// Response
{
    "response": "To apply for admission...",
    "source": "knowledge_base"
}
```

---

## 🚀 Future Enhancements

Ideas to extend this project:

1. **Database Integration**: Store chat history
2. **User Authentication**: Login system
3. **Admin Panel**: Manage knowledge base via UI
4. **Multi-language Support**: Hindi/regional languages
5. **Voice Input**: Speech-to-text integration
6. **Analytics Dashboard**: Track common queries
7. **Feedback System**: Let users rate responses
8. **Email Integration**: Forward complex queries to admin

---

## ❓ Troubleshooting

### Common Issues

**1. "Module not found" error**
```bash
pip install -r requirements.txt
```

**2. OpenAI not working**
- Check if API key is valid
- Ensure you have credits in your OpenAI account
- The chatbot will still work with rule-based responses

**3. Port 5000 already in use**
Change the port in `app.py`:
```python
app.run(port=5001)
```

**4. Styles not loading**
- Clear browser cache
- Check if static files path is correct

---

## 👨‍🎓 For Students

This project is designed for learning. Here's what you can explore:

1. **Flask Basics**: Routes, templates, static files
2. **Frontend Development**: HTML, CSS, JavaScript
3. **API Integration**: How to call external APIs
4. **Text Processing**: Pattern matching, similarity
5. **Software Design**: Modular code structure

---

## 📄 License

This project is created for educational purposes. Feel free to use and modify for your college project.

---

## 🙏 Credits

- Flask Framework: https://flask.palletsprojects.com/
- OpenAI API: https://openai.com/
- Google Fonts (Poppins): https://fonts.google.com/

---

**Happy Coding! 🚀**
