import os
import sqlite3
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openai import OpenAI
import gradio as gr
import tempfile
import PyPDF2

# Initialize OpenAI client
import dotenv
dotenv.load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# Database
DB_PATH = "assistant.db"

def init_database():
    try:
        # 确保数据库目录存在
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # 连接数据库
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        c = conn.cursor()
        
        # 创建表
        c.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_number INTEGER,
            doctor TEXT,
            patient TEXT,
            date TEXT,
            transcript TEXT,
            summary TEXT,
            diseases TEXT,
            UNIQUE(patient, visit_number)
        )''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# 初始化数据库

if not init_database():
    print("Failed to initialize database. The application may not work properly.")

# 创建全局数据库连接
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# i18n
i18n = {
    "中文": {
        "doctor": "医生姓名",
        "patient": "病人姓名",
        "date": "日期",
        "record": "录制/上传音频",
        "file": "上传文件",
        "text": "手动输入文本 (可选)",
        "next": "下一步",
        "transcript": "转录文本",
        "summary": "总结",
        "edit": "编辑总结",
        "save": "保存总结",
        "download": "下载报告",
        "new_chat": "新对话",
        "history": "历史记录",
        "refresh": "刷新历史记录",
        "step1": "基本信息",
        "step2": "上传内容",
        "step3": "生成报告",
        "processing": "正在处理...",
        "generating": "正在生成总结...",
        "saving": "正在保存记录...",
        "report": "正在生成报告...",
        "complete": "完成！",
        "required": "请填写所有必填字段",
        "input_required": "请至少提供一种输入方式（音频、文件或文本）"
    },
    "English": {
        "doctor": "Doctor Name",
        "patient": "Patient Name",
        "date": "Date",
        "record": "Record/Upload Audio",
        "file": "Upload File",
        "text": "Manual Input Text (Optional)",
        "next": "Next Step ",
        "transcript": "Transcript",
        "summary": "Summary",
        "edit": "Edit Summary",
        "save": "Save Summary",
        "download": "Download Report",
        "new_chat": "New Conversation",
        "history": "History",
        "refresh": "Refresh History",
        "step1": "Basic Information",
        "step2": "Upload Content",
        "step3": "Generate Report",
        "processing": "Processing...",
        "generating": "Generating Summary...",
        "saving": "Saving Record...",
        "report": "Generating Report...",
        "complete": "Complete!",
        "required": "Please fill in all required fields",
        "input_required": "Please provide at least one input method (audio, file, or text)"
    }
}

# Core Functions
def transcribe_audio(audio_path, file_obj):
    if audio_path:
        # 上传的是音频，送给 Whisper 识别
        with open(audio_path, 'rb') as f:
            resp = client.audio.transcriptions.create(file=f, model="whisper-1")
            return resp.text
    elif file_obj:
        # 上传的是文本文件
        filename = file_obj.name.lower()
        if filename.endswith('.txt'):
            with open(file_obj.name, 'r', encoding='utf-8') as f:
                return f.read()
        elif filename.endswith('.pdf'):
            import PyPDF2
            reader = PyPDF2.PdfReader(file_obj.name)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif filename.endswith('.docx'):
            import docx
            doc = docx.Document(file_obj.name)
            text = ''
            for para in doc.paragraphs:
                text += para.text + '\\n'
            return text
        else:
            raise ValueError("Unsupported file type: only .txt, .pdf, .docx supported!")
    else:
        return ""


def summarize_and_extract(text, info):
    prompt = f"Patient Info: {info}\nTranscript: {text}\nPlease summarize the above dialogue in a medical report style and list possible diagnoses. The list need to contain the 1.Chief Complaint, 2. History of Present Illness, 3. Mental Status Examination, 4. Assessment, 5. Possible Diagnoses, 6. Recommendations, 7. Plan, 8. Follow-Up"
    resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content

def generate_report(doctor, patient, date, session_id, transcript, summary):
    # print(f"Generating Report: Doctor={doctor}, Patient={patient}, Date={date}, Session={session_id}")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    # Markdown文本部分（供网页显示）
    markdown_text = f"""# This is the session #{session_id}

**Doctor:** {doctor}  
**Patient:** {patient}  
**Date:** {date}  

---

## Transcript
{transcript}

---

## Summary & Possible Diagnoses
{summary}
"""
    # 插入基本信息
    story.append(Paragraph(f"This is the session #{session_id}", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Doctor: {doctor}", styles['Normal']))
    story.append(Paragraph(f"Patient: {patient}", styles['Normal']))
    story.append(Paragraph(f"Date: {date}", styles['Normal']))
    story.append(Spacer(1, 24))

    # 插入转录文本
    story.append(Paragraph("Transcript:", styles['Heading2']))
    story.append(Paragraph(transcript.replace("\n", "<br/>"), styles['BodyText']))
    story.append(Spacer(1, 12))

    # 插入总结
    story.append(Paragraph("Summary & Possible Diagnoses:", styles['Heading2']))
    story.append(Paragraph(summary.replace("\n", "<br/>"), styles['BodyText']))

    doc.build(story)
    buffer.seek(0)
    return buffer, markdown_text


# Build UI
def build_ui():
    doctor_state = gr.State("")
    patient_state = gr.State("")
    date_state = gr.State("")

    custom_css = """
    body { background-color: #f7f7f8; }
    .gradio-container { max-width: 100%; padding: 0; }
    .sidebar { background: white; padding: 20px; height: 100vh; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }
    .content { padding: 40px; height: 100vh; overflow-y: auto; }
    .progress-bar { 
        width: 100%; 
        height: 4px; 
        background: #e0e0e0; 
        margin: 20px 0; 
        border-radius: 2px; 
        overflow: hidden; 
    }
    .progress-bar-fill { 
        height: 100%; 
        background: #4a6bdf; 
        transition: width 0.3s ease; 
    }
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
        padding: 0 20px;
    }
    .step {
        text-align: center;
        flex: 1;
        position: relative;
    }
    .step:not(:last-child):after {
        content: '';
        position: absolute;
        top: 20px;
        right: -50%;
        width: 100%;
        height: 2px;
        background: #e0e0e0;
    }
    .step.active {
        color: #4a6bdf;
    }
    .step.completed {
        color: #4a6bdf;
    }
    .step-number {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 8px;
    }
    .step.active .step-number {
        background: #4a6bdf;
        color: white;
    }
    .step.completed .step-number {
        background: #4a6bdf;
        color: white;
    }
    """
    with gr.Blocks(css=custom_css) as demo:
        lang = gr.Dropdown(choices=["中文", "English"], value="中文", label="🌐 Language")
        labels = gr.State(i18n["中文"])
        current_step = gr.State(0)
        transcript_state = gr.State("")
        summary_state = gr.State("")
        pdf_path_state = gr.State("")

        # Progress bar
        progress_html = """
        <div class="progress-bar">
            <div class="progress-bar-fill" style="width: 0%"></div>
        </div>
        """
        progress = gr.HTML(progress_html)

        # Step indicator
        step_indicator_html = """
        <div class="step-indicator">
            <div class="step active" id="step1">
                <div class="step-number">1</div>
                <div class="step-title">{step1}</div>
            </div>
            <div class="step" id="step2">
                <div class="step-number">2</div>
                <div class="step-title">{step2}</div>
            </div>
            <div class="step" id="step3">
                <div class="step-number">3</div>
                <div class="step-title">{step3}</div>
            </div>
        </div>
        """
        step_indicator = gr.HTML(step_indicator_html)

        with gr.Row():
            with gr.Column(elem_classes=["sidebar"], scale=1):
                gr.Markdown("## Assistant")
                new_chat_btn = gr.Button(value="新对话")
                history_btn = gr.Button(value="历史记录")
            with gr.Column(elem_classes=["content"], scale=4):
                step1 = gr.Column(visible=True)
                step2 = gr.Column(visible=False)
                step3 = gr.Column(visible=False)
                history_area = gr.Column(visible=False)

                with step1:
                    doctor = gr.Textbox(label="医生姓名")
                    patient = gr.Textbox(label="病人姓名")
                    date = gr.Textbox(label="日期", value=str(datetime.today().date()))
                    next1 = gr.Button(value="下一步")

                with step2:
                    audio = gr.Audio(label="录制/上传音频", type='filepath')
                    file_obj = gr.File(label="上传文件", file_types=[".pdf", ".txt", ".docx"])
                    text_input = gr.Textbox(label="手动输入文本 (可选)", lines=10)
                    next2 = gr.Button(value="下一步")

                with step3:
                    transcript_md = gr.Markdown(label="转录文本", value="", visible=True)
                    summary_md = gr.Markdown(label="总结", value="", visible=True)
                    edit_btn = gr.Button(value="编辑总结")
                    edited_summary = gr.Textbox(label="Edit Summary", lines=10, visible=False)
                    save_edit_btn = gr.Button(value="保存总结", visible=False)
                    download_btn = gr.File(label="下载报告", visible=False)

                with history_area:
                    history_btn_view = gr.Button(value="刷新历史记录")
                    history_table = gr.Dataframe(
                        headers=["ID", "Visit", "Doctor", "Patient", "Date", "Transcript", "Summary"],
                        interactive=True,
                        visible=False
                    )
                    history_transcript = gr.Textbox(label="Transcript", lines=10, visible=False)
                    history_summary = gr.Textbox(label="Summary", lines=10, visible=False)
                    history_download = gr.File(label="Download Report", visible=False)

        # Define UI interactions
        def switch_language(language):
            labels = i18n[language]
            step_html = step_indicator_html.format(
                step1=labels["step1"],
                step2=labels["step2"],
                step3=labels["step3"]
            )
            return labels, gr.update(label=labels["doctor"]), gr.update(label=labels["patient"]), \
                   gr.update(label=labels["date"]), gr.update(label=labels["record"]), \
                   gr.update(label=labels["file"]), gr.update(label=labels["text"]), \
                   gr.update(value=labels["next"]), gr.update(value=labels["next"]), \
                   gr.update(label=labels["transcript"]), gr.update(label=labels["summary"]), \
                   gr.update(value=labels["edit"]), gr.update(value=labels["save"]), \
                   gr.update(label=labels["download"]), gr.update(value=labels["new_chat"]), \
                   gr.update(value=labels["history"]), gr.update(value=labels["refresh"]), \
                   gr.update(value=step_html)

        def update_progress(step):
            progress_html = f"""
            <div class="progress-bar">
                <div class="progress-bar-fill" style="width: {step * 33.33}%"></div>
            </div>
            """
            return progress_html

        def go_step2(doc_name, pat_name, date_str, labels):
            if not all([doc_name, pat_name, date_str]):
                gr.Warning(labels["required"])
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 0, update_progress(0), "", "", ""
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), 1, update_progress(1), doc_name, pat_name, date_str

        def go_step3(audio_path, file_upload, manual_text, labels, doc_name, pat_name, date_str):
            if not any([audio_path, file_upload, manual_text.strip()]):
                gr.Warning(labels["input_required"])
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), 1, update_progress(1), "", "", None
            
            progress = gr.Progress()
            progress(0.2, desc=labels["processing"])
            transcript = manual_text if manual_text.strip() else transcribe_audio(audio_path, file_upload)
            progress(0.5, desc=labels["generating"])
            info = f"Doctor: {doc_name}, Patient: {pat_name}, Date: {date_str}"
            summary = summarize_and_extract(transcript, info)
            progress(0.8, desc=labels["saving"])
            
            # 获取该病人的就诊次数
            c.execute("SELECT MAX(visit_number) FROM history WHERE patient = ?", (pat_name,))
            result = c.fetchone()
            visit_number = (result[0] or 0) + 1  # 当前是第几次就诊
            
            # 插入新记录
            c.execute("INSERT INTO history (visit_number, doctor, patient, date, transcript, summary, diseases) VALUES (?,?,?,?,?,?,?)",
                      (visit_number, doc_name, pat_name, date_str, transcript, summary, ''))
            conn.commit()
            
            # 获取刚插入记录的id
            c.execute("SELECT id FROM history WHERE patient = ? AND visit_number = ?", (pat_name, visit_number))
            record_id = c.fetchone()[0]
            
            progress(0.9, desc=labels["report"])
            pdf_buffer, markdown_text = generate_report(doc_name, pat_name, date_str, visit_number, transcript, summary)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_buffer.read())
                tmp_path = tmp.name
            progress(1.0, desc=labels["complete"])
            
            return (
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=True),
                gr.update(visible=False),
                2, update_progress(2),
                gr.update(value=transcript),   # 更新 transcript_md
                gr.update(value=markdown_text),  # 更新 summary_md
                tmp_path  # 给 download 按钮
            )
        def enter_edit(summary_content):
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True, value=summary_content), gr.update(visible=True)

        def save_summary(edited_content, transcript, markdown_text, doc_name, pat_name, date_str):
            info = "Edited Info"
            # 获取该病人的最新就诊记录
            c.execute("SELECT MAX(visit_number) FROM history WHERE patient = ?", (pat_name,))
            result = c.fetchone()
            visit_number = result[0] or 0
            
            pdf_buffer, markdown_text = generate_report(doc_name, pat_name, date_str, visit_number, transcript, edited_content)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_buffer.read())
                tmp_path = tmp.name
            return edited_content, gr.update(value=edited_content, visible=True), gr.update(visible=True), tmp_path

        def load_history():
            # 查询所有历史记录，按日期降序排列
            c.execute("""
                SELECT id, visit_number, doctor, patient, date, transcript, summary 
                FROM history 
                ORDER BY date DESC, visit_number DESC
            """)
            rows = c.fetchall()
            
            # 如果没有记录，返回空列表
            if not rows:
                return gr.update(
                    value=[],
                    headers=["ID", "Visit", "Doctor", "Patient", "Date", "Transcript", "Summary"],
                    visible=True
                )
            
            # 格式化数据
            formatted_rows = []
            for row in rows:
                # 截断过长的文本
                transcript = row[5][:100] + "..." if len(row[5]) > 100 else row[5]
                summary = row[6][:100] + "..." if len(row[6]) > 100 else row[6]
                
                formatted_rows.append([
                    row[0],  # id
                    row[1],  # visit_number
                    row[2],  # doctor
                    row[3],  # patient
                    row[4],  # date
                    transcript,
                    summary
                ])
            
            return gr.update(
                value=formatted_rows,
                headers=["ID", "Visit", "Doctor", "Patient", "Date", "Transcript", "Summary"],
                visible=True
            )

        def view_history_details(evt: gr.SelectData):
            if evt.index[0] is None:  # 如果没有选择行
                return "", "", ""
            
            # 获取选中行的ID
            selected_id = evt.value[evt.index[0]][0]
            
            # 查询完整记录
            c.execute("""
                SELECT transcript, summary 
                FROM history 
                WHERE id = ?
            """, (selected_id,))
            result = c.fetchone()
            
            if result:
                return result[0], result[1], gr.update(visible=True)
            return "", "", gr.update(visible=False)

        # Event bindings
        lang.change(fn=switch_language, inputs=[lang], 
                   outputs=[labels, doctor, patient, date, audio, file_obj, text_input, next1, next2,
                           transcript_md, summary_md, edit_btn, save_edit_btn, download_btn,
                           new_chat_btn, history_btn, history_btn_view, step_indicator])

        new_chat_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), 
                                   gr.update(visible=False), 0, update_progress(0)), 
                          outputs=[step1, step2, step3, history_area, current_step, progress])
        
        history_btn.click(lambda: (gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 
                                  gr.update(visible=True), 0, update_progress(0)), 
                         outputs=[step1, step2, step3, history_area, current_step, progress])

        next1.click(go_step2, 
            inputs=[doctor, patient, date, labels], 
            outputs=[step1, step2, step3, history_area, current_step, progress, doctor_state, patient_state, date_state]
        )

        next2.click(go_step3, inputs=[audio, file_obj, text_input, labels, doctor, patient, date], 
                   outputs=[step1, step2, step3, history_area, current_step, progress, 
                           transcript_md, summary_md, download_btn])

        edit_btn.click(enter_edit, inputs=[summary_md], outputs=[summary_md, summary_md, edited_summary, save_edit_btn])
        save_edit_btn.click(save_summary, inputs=[edited_summary, transcript_md, summary_md, doctor, patient, date], outputs=[summary_md, summary_md, download_btn, pdf_path_state])
        history_btn_view.click(load_history, inputs=[], outputs=[history_table])
        history_table.select(
            fn=view_history_details,
            outputs=[history_transcript, history_summary, history_download]
        )

    return demo

app = build_ui()
app.launch()
