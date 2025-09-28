# AI service to handle different models
import time
import sys
import os
import random
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
        thinking_process = [
            "正在分析用户问题：调整了思考过程和模型回复的输出格式",
            "检索相关知识库：思考过程会逐步显示每个步骤，并带有",
            "构建回答框架：这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验，这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验，这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验",
            "生成详细内容：这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验",
            "校验回答准确性：这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验这些修改确保了用户体验更加接近主流AI助手（如DeepSeek、Kimi）的效果，提供了更好的交互体验"
        ]
        
        # 模拟思考过程
        for thought in thinking_process:
            yield f"{thought}"
            time.sleep(0.5)
        
        response = f"\n这是来自 Qwen-2.5 模型的响应: 我收到了您的消息 '{prompt}'。这是一个模拟响应，用于演示 AG-UI 协议的流式输出功能。它会逐步显示，就像真实的AI助手一样。"
        for i in range(0, len(response), 3):
            yield response[i:i+3]
            time.sleep(0.05)  # 模拟网络延迟
    
    def _baichuan_model(self, prompt: str):
        """
        Mock implementation for Baichuan model
        In real implementation, this would call the actual Baichuan API
        """
        thinking_process = [
            "理解用户意图...",
            "查询相关资料...",
            "组织语言结构...",
            "完善回答内容...",
            "优化表达方式..."
        ]
        
        # 模拟思考过程
        for thought in thinking_process:
            yield f"{thought}"
            time.sleep(0.5)
        
        response = f"\n这是来自 Baichuan v1.0 模型的响应: 我理解您的消息 '{prompt}'。这是一个示例响应，用于演示流式输出效果。"
        for i in range(0, len(response), 3):
            yield response[i:i+3]
            time.sleep(0.05)  # 模拟网络延迟
    
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