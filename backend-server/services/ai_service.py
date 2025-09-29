# AI service to handle different models
import time
import sys
import os
import random
import os
from openai import OpenAI
from pathlib import Path
from utils.image_analyzer import process_image_with_pil
from utils.file_utils import extract_filename_from_url, analyze_document
from utils.ai_message_utils import build_message_by_type
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AIService:
    def __init__(self):
        # Initialize available models
        self.models = {
            "doubao-seed-1-6-thinking-250715": self._doubao_model,
            "qwen3-max": self._qwen_model,
        }
    
    def _doubao_model(self, prompt: str, file_url: str = None, message_type: str = "text"):
        """
        Mock implementation for Qwen model
        In real implementation, this would call the actual Doubao API
        """

        # 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
        # 初始化Ark客户端，从环境变量中读取您的API Key
        client = OpenAI(
            # 此为默认路径，您可根据业务所在地域进行配置
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
            api_key=os.environ.get("ARK_API_KEY", "f1ff0594-8663-44a2-85d7-182bcc51f22c"),
        )
        
        # 使用新的消息构建工具构建消息
        messages = build_message_by_type(message_type, prompt, file_url)

        completion = client.chat.completions.create(
            # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
            model="doubao-seed-1-6-thinking-250715",
            extra_body={"enable_thinking": True},  # 开启思考模式
            stream=True,
            messages=messages
        )
        for chunk in completion:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                yield "<think>" + chunk.choices[0].delta.reasoning_content + "</think>"
            if delta.content:
                yield "<content>" + chunk.choices[0].delta.content + "</content>"
    
    def _qwen_model(self, prompt: str, file_url: str = None, message_type: str = "text"):
        """
        Mock implementation for Baichuan model
        In real implementation, this would call the actual qwen API
        """
    
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=os.getenv("DASHSCOPE_API_KEY", "sk-5ceee3c3e7ee422c812938b314925ded"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        # 使用新的消息构建工具构建消息（对于文本类型）
        messages = build_message_by_type(message_type, prompt, file_url)

        completion = client.chat.completions.create(
            model="qwen3-max",
            messages=messages,
            stream=True
        )
        yield "<think>" + "未开启模型思考！" + "</think>"
        for chunk in completion:
            delta = chunk.choices[0].delta
            yield "<content>" + delta.content + "</content>"
    
    def get_available_models(self):
        return list(self.models.keys())
    
    def chat_completion(self, model: str, prompt: str, user_id: str, file_url: str = None, message_type: str = "text"):
        """
        Generate chat completion using specified model
        """
        # In a real implementation, you would integrate with mem0 here
        # For now, we'll just use a simple approach
        
        # Generate response using selected model
        if model in self.models:
            yield from self.models[model](prompt, file_url, message_type)
        else:
            yield f"模型 {model} 不受支持"