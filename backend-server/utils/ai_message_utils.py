import os
from typing import List, Dict, Any, Union
from utils.image_analyzer import process_image_with_pil
from utils.file_utils import extract_filename_from_url, analyze_document


def build_text_message(prompt: str) -> List[Dict[str, Any]]:
    """
    构建纯文本消息
    
    Args:
        prompt (str): 用户输入的文本
        
    Returns:
        List[Dict[str, Any]]: 消息结构列表
    """
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]


def build_image_message(prompt: str, file_url: str) -> List[Dict[str, Any]]:
    """
    构建图像消息
    
    Args:
        prompt (str): 用户输入的文本
        file_url (str): 图像文件的URL路径
        
    Returns:
        List[Dict[str, Any]]: 消息结构列表
    """
    # 从URL中提取文件名并构建文件路径
    file_name = extract_filename_from_url(file_url)
    file_path = os.path.join('api', 'uploads', file_name)
    
    # 处理图像并转换为base64
    base64_image = process_image_with_pil(file_path)
    
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }
    ]


def build_document_message(prompt: str, file_url: str) -> List[Dict[str, Any]]:
    """
    构建文档消息
    
    Args:
        prompt (str): 用户输入的文本
        file_url (str): 文档文件的URL路径
        
    Returns:
        List[Dict[str, Any]]: 消息结构列表
    """
    # 从URL中提取文件名并构建文件路径
    file_name = extract_filename_from_url(file_url)
    file_path = os.path.join('api', 'uploads', file_name)
    
    # 分析文档内容
    file_content = analyze_document(file_path)
    
    return [
        {"role": "system", "content": file_content},
        {"role": "user", "content": prompt}
    ]


def build_message_by_type(message_type: str, prompt: str, file_url: str = None) -> List[Dict[str, Any]]:
    """
    根据消息类型构建相应的消息结构
    
    Args:
        message_type (str): 消息类型 ("text", "image", "document")
        prompt (str): 用户输入的文本
        file_url (str, optional): 文件URL路径
        
    Returns:
        List[Dict[str, Any]]: 消息结构列表
    """
    if message_type == "text":
        return build_text_message(prompt)
    elif message_type == "image":
        return build_image_message(prompt, file_url)
    elif message_type == "document":
        return build_document_message(prompt, file_url)
    else:
        # 默认处理为文本消息
        return build_text_message(prompt)