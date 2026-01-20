from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from io import BytesIO
import urllib.parse
import mimetypes

app = FastAPI()
DB_FILE = "data.db"

# CORS 設定（任意）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    ''', (file.filename, attributes, sqlite3.Binary(file_content)))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"id": new_id, "message": "File uploaded successfully"}

# ファイルダウンロード
@app.get("/download/{data_id}")
def view_file(data_id: int):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT filename, file_data FROM marketplace_data WHERE id=?", (data_id,))
        row = c.fetchone()
        conn.close()
    
        if not row:
            raise HTTPException(status_code=404, detail="File not found")
    
        filename, file_data = row
        if isinstance(file_data, memoryview):
            file_data = file_data.tobytes()
    
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "text/plain"  # ← ここがポイント
        download_filename = f"[{data_id}_{filename}"
        headers = {
            "Content-Disposition": f'attachment; filename="{download_filename}"'
        }
        
        return Response(content=file_data, media_type=mime_type, headers=headers)
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # 詳細なエラーをサーバーログに出す
        raise HTTPException(status_code=500, detail=str(e))


# 属性一覧取得
@app.get("/attributes/{data_id}")
def get_attributes(data_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT attributes FROM marketplace_data WHERE id=?", (data_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return JSONResponse(status_code=404, content={"error": "Data not found"})
    return JSONResponse(content={"attributes": row[0]})

# ファイル一覧取得
@app.get("/files/")
def list_files():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, filename, upload_time FROM marketplace_data ORDER BY upload_time DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "filename": r[1], "upload_time": r[2]} for r in rows]

# Railway / Heroku 用に PORT を環境変数から取得
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

#uvicorn database:app --reload
#http://127.0.0.1:8000/docs
