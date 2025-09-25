# AI service to handle different models
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AIService:
    def __init__(self):
        # Initialize available models
        self.models = {
            "qwen-2.5": self._qwen_model,
            "baichuan-v1.0": self._baichuan_model
        }
    
    def _qwen_model(self, prompt: str):
        """
        Mock implementation for Qwen model
        In real implementation, this would call the actual Qwen API
        """
        response = f"这是来自 Qwen-2.5 模型的响应: 我收到了您的消息 '{prompt}'。这是一个模拟响应。"
        for i in range(0, len(response), 4):
            yield response[i:i+4]
            time.sleep(0.1)  # 模拟网络延迟
    
    def _baichuan_model(self, prompt: str):
        """
        Mock implementation for Baichuan model
        In real implementation, this would call the actual Baichuan API
        """
        response = f"这是来自 Baichuan v1.0 模型的响应: 我理解您的消息 '{prompt}'。这是一个示例响应。"
        for i in range(0, len(response), 4):
            yield response[i:i+4]
            time.sleep(0.1)  # 模拟网络延迟
    
    def get_available_models(self):
        return list(self.models.keys())
    
    def chat_completion(self, model: str, prompt: str, user_id: str):
        """
        Generate chat completion using specified model
        """
        # In a real implementation, you would integrate with mem0 here
        # For now, we'll just use a simple approach
        
        # Generate response using selected model
        if model in self.models:
            yield from self.models[model](prompt)
        else:
            yield f"模型 {model} 不受支持"