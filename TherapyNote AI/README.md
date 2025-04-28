Therapy Session Note Assistant
A Gradio-based web application that allows mental health professionals to transcribe, summarize, and generate structured session reports from audio or text input. It supports Chinese and English interfaces and automatically manages session history with an integrated SQLite database.

Features
- Record or upload audio, .txt, .pdf, or .docx session notes.
- Automatic transcription using OpenAI Whisper model.
- Summarization into structured clinical reports, including:
    - Chief Complaint
    - History of Present Illness
    - Mental Status Examination
    - Assessment
    - Possible Diagnoses
    - Recommendations
    - Plan
    - Follow-Up
- Editable session summaries before finalizing.
- View and refresh history of all previous sessions.
- Download session notes as PDF reports.
- Language toggle between 中文 and English

UI/UX Features
- Step-by-step guided workflow (Basic Info → Upload → Report Generation).
- Visual step indicators for progress tracking.
- Integrated progress bar.
- Custom page styling with embedded CSS for sidebar layout, content scrolling, and visual polish.
- Simple, clean interface designed for fast clinical use.

Quick Start
1. Clone the repository
    git clone https://github.com/yourusername/therapy-session-assistant.git
    cd therapy-session-assistant

2. Install dependencies
    pip install -r requirements.txt
If requirements.txt is missing, manually install:
    pip install gradio openai reportlab python-docx python-dotenv pypdf2

3. Setup environment variables
    Create a .env file (already included) containing:
    OPENAI_API_KEY=your_openai_api_key_here
    Replace your_openai_api_key_here with your actual OpenAI API Key.

4. Run the app
    python app.py
    The app will be available at http://127.0.0.1:7860/.

Project Structure

├── app.py            # Main application (UI + logic)
├── assistant.db      # SQLite database for session history
├── .env              # Environment variables (OpenAI API Key)
└── README.md         # Project documentation

Tech Stack
Gradio - frontend and backend web interface
OpenAI API - Whisper and GPT models for transcription and summarization
SQLite - local database management
ReportLab - dynamic PDF report generation
Embedded CSS - custom UI styling

Notes
- The OpenAI API usage will incur costs depending on your account settings.
- Ensure that your API Key has access to gpt-4o and whisper-1.
- Session tracking is managed by patient name and visit number automatically.

