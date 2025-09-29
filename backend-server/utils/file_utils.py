import os
import uuid
import re
from urllib.parse import urlparse
import os
from pathlib import Path
import pandas as pd
from docx import Document
import PyPDF2
import pdfplumber
from typing import Union


def extract_filename_from_url(url: str) -> str:
    """
    从URL中提取文件名
    
    Args:
        url (str): 完整的URL路径
        
    Returns:
        str: 提取的文件名，如果无法提取则返回空字符串
        
    Examples:
        >>> extract_filename_from_url("/uploads/9bcf4800-69aa-44b4-8948-c037f2f20cde.png")
        '9bcf4800-69aa-44b4-8948-c037f2f20cde.png'
        >>> extract_filename_from_url("http://example.com/uploads/9bcf4800-69aa-44b4-8948-c037f2f20cde.png")
        '9bcf4800-69aa-44b4-8948-c037f2f20cde.png'
    """
    if not url:
        return ""
    
    # 解析URL
    parsed_url = urlparse(url)
    
    # 获取路径部分
    path = parsed_url.path
    
    # 获取文件名（路径的最后一部分）
    filename = os.path.basename(path)
    
    # 验证是否为有效的UUID格式文件名
    if is_uuid_filename(filename):
        return filename
    
    return filename

def is_uuid_filename(filename: str) -> bool:
    """
    检查文件名是否为UUID格式
    
    Args:
        filename (str): 文件名
        
    Returns:
        bool: 如果是UUID格式返回True，否则返回False
    """
    if not filename:
        return False
    
    # 分离文件名和扩展名
    name_part = os.path.splitext(filename)[0]
    
    # UUID正则表达式
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    return bool(uuid_pattern.match(name_part))

def generate_uuid_filename(original_filename: str) -> str:
    """
    生成UUID格式的文件名，保留原始扩展名
    
    Args:
        original_filename (str): 原始文件名
        
    Returns:
        str: UUID格式的文件名
    """
    # 获取文件扩展名
    _, ext = os.path.splitext(original_filename)
    
    # 生成UUID文件名
    uuid_filename = str(uuid.uuid4()) + ext.lower()
    
    return uuid_filename

class DocumentReader:
    """支持多种文档格式的读取器"""
    
    @staticmethod
    def read_docx(file_path: Union[str, Path]) -> str:
        """读取Word文档内容"""
        try:
            doc = Document(file_path)
            content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            return '\n'.join(content)
        except Exception as e:
            raise Exception(f"读取Word文档失败: {str(e)}")
    
    @staticmethod
    def read_pdf(file_path: Union[str, Path]) -> str:
        """读取PDF文档内容"""
        try:
            content = []
            
            # 方法1: 使用pdfplumber（推荐，能更好地提取文本）
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        content.append(text)
            
            # 如果pdfplumber提取失败，尝试使用PyPDF2作为备选
            if not any(content):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            content.append(text)
            
            return '\n'.join(content) if content else "无法从PDF中提取文本内容"
        except Exception as e:
            raise Exception(f"读取PDF文档失败: {str(e)}")
    
    @staticmethod
    def read_excel(file_path: Union[str, Path]) -> str:
        """读取Excel文档内容"""
        try:
            content = []
            
            # 读取所有工作表
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 添加工作表名称
                content.append(f"工作表: {sheet_name}")
                
                # 处理数据框内容
                if not df.empty:
                    # 添加列名
                    columns = " | ".join([str(col) for col in df.columns])
                    content.append(f"列名: {columns}")
                    
                    # 添加前几行数据作为示例（避免内容过长）
                    for i, row in df.head(10).iterrows():
                        row_content = " | ".join([str(cell) for cell in row.values])
                        content.append(f"行 {i+1}: {row_content}")
                    
                    # 如果数据很多，添加提示
                    if len(df) > 10:
                        content.append(f"... 还有 {len(df) - 10} 行数据未显示")
                
                content.append("")  # 添加空行分隔不同工作表
            
            return '\n'.join(content)
        except Exception as e:
            raise Exception(f"读取Excel文档失败: {str(e)}")
    
    @staticmethod
    def read_document(file_path: Union[str, Path]) -> str:
        """自动识别文件类型并读取内容"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 根据文件扩展名选择读取方法
        extension = file_path.suffix.lower()
        
        if extension == '.docx':
            return DocumentReader.read_docx(file_path)
        elif extension == '.pdf':
            return DocumentReader.read_pdf(file_path)
        elif extension in ['.xlsx', '.xls']:
            return DocumentReader.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {extension}")

def analyze_document(file_path: str, max_length: int = 10000) -> str:
    """分析文档并回答问题"""
    try:
        # 读取文档内容
        reader = DocumentReader()
        doc_content = reader.read_document(file_path)
        
        # 如果内容过长，可以截取部分（根据模型token限制调整）
        if len(doc_content) > max_length:
            doc_content = doc_content[:max_length] + "...\n[内容已截断]"
        return doc_content
        
    except Exception as e:
        return f"分析文档时出错: {str(e)}"
    

def chunk_document_content(content: str, chunk_size: int = 4000) -> list:
    """将长文档内容分块"""
    chunks = []
    for i in range(0, len(content), chunk_size):
        chunks.append(content[i:i+chunk_size])
    return chunks

def analyze_long_document(file_path: str, question: str, chunk_size: int = 4000) -> list:
    """分析长文档（分块处理）"""
    reader = DocumentReader()
    content = reader.read_document(file_path)
    
    # 如果内容不长，直接处理
    if len(content) <= chunk_size:
        return analyze_document(file_path, question)
    
    # 长文档分块处理
    chunks = chunk_document_content(content)
    
    return chunks