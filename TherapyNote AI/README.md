# Therapy Session Note Assistant

A Gradio-based web application that allows mental health professionals to transcribe, summarize, and generate structured session reports from audio or text input.  
Supports both **Chinese** and **English** interfaces, with integrated **SQLite** database management for session history.

---

## Features

- Record or upload audio, `.txt`, `.pdf`, or `.docx` session notes
- Automatic transcription using **OpenAI Whisper** model
- Summarization into structured clinical reports, including:
  - Chief Complaint
  - History of Present Illness
  - Mental Status Examination
  - Assessment
  - Possible Diagnoses
  - Recommendations
  - Plan
  - Follow-Up
- Editable session summaries before finalizing
- View and refresh the history of all previous sessions
- Download session notes as **PDF reports**
- Language toggle between **中文** and **English**

---

## UI/UX Highlights

- Step-by-step guided workflow (**Basic Info → Upload → Report Generation**)
- Visual step indicators for progress tracking
- Integrated progress bar
- Custom embedded CSS for sidebar layout, scrolling, and visual polish
- Clean, simple interface optimized for fast clinical use

---

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/therapy-session-assistant.git
   cd therapy-session-assistant

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install gradio openai reportlab python-docx python-dotenv pypdf2

4. **Set up environment variables**
   Create a .env file containing:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here

6. **Run the app**
   ```bash
   python app.py
    The app will be available at: http://127.0.0.1:7860

---

## Project Structure
    app.py            # Main application (UI + logic)
    assistant.db      # SQLite database for session history
    .env              # Environment variables (OpenAI API Key)
    README.md         # Project documentation

---

## Tech Stack
**Gradio** — Frontend and backend web interface

**OpenAI API** — Whisper and GPT models for transcription and summarization

**SQLite** — Local database management

**ReportLab** — Dynamic PDF report generation

**Embedded CSS** — Custom UI styling

---
## Notes
- OpenAI API usage may incur costs depending on your account settings.
- Ensure that your API Key has access to gpt-4o and whisper-1.
- Session tracking is automatically managed based on patient name and visit number.
