from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import sqlite3
import json

app = FastAPI()
DB_FILE = "data.db"

# DB初期化
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS marketplace_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            attributes TEXT,
            file_data BLOB,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ファイルアップロード＋属性保存
@app.post("/upload/")
async def upload_file(
    file: UploadFile = File(...),
    attributes: str = Form("{}")  # JSON文字列
):
    file_content = await file.read()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO marketplace_data (filename, attributes, file_data)
        VALUES (?, ?, ?)
    ''', (file.filename, attributes, file_content))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"id": new_id, "message": "File uploaded successfully"}

@app.get("/download/{data_id}")
def download_file(data_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT filename, file_data FROM marketplace_data WHERE id=?", (data_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"error": "File not found"}
    filename, file_data = row
    return {
        "filename": filename,
        "file_data": file_data
    }

# 属性一覧取得
@app.get("/attributes/{data_id}")
def get_attributes(data_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT attributes FROM marketplace_data WHERE id=?", (data_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"error": "Data not found"}
    return row[0]

# ファイル一覧取得
@app.get("/files/")
def list_files():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, filename, upload_time FROM marketplace_data ORDER BY upload_time DESC")
    rows = c.fetchall()
    conn.close()
    # リストを辞書形式で返す
    return [{"id": r[0], "filename": r[1], "upload_time": r[2]} for r in rows]

#uvicorn database:app --reload
#http://127.0.0.1:8000/docs
