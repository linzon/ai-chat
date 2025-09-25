from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Response, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.deps import get_db_session

router = APIRouter(prefix="/upload", tags=["upload"])

# 确保上传目录存在
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session)
):
    """
    上传文件接口
    """
    try:
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 返回文件信息
        return {
            "filename": file.filename,
            "saved_filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
            "content_type": file.content_type,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/files/{filename}")
async def get_file(filename: str, request: Request):
    """
    获取上传的文件（返回实际文件）
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件未找到")
    
    # 返回文件响应
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        stat_result=os.stat(file_path)
    )