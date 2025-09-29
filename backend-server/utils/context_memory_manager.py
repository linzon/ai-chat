"""
基于mem0框架的上下文记忆系统
使用conversation_id和user_id共同区分会话上下文
本地缓存存储实现
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
import pickle
from dataclasses import dataclass, asdict
from enum import Enum

# 如果没有安装mem0，请先安装：pip install mem0ai
try:
    from mem0 import Memory
except ImportError:
    print("请先安装mem0: pip install mem0ai")
    Memory = None


class ContextMemoryManager:
    """支持会话级别的上下文记忆管理器"""
    
    def __init__(self, 
                 config: Optional[Dict] = None,
                 enable_mem0: bool = True):
        """
        初始化记忆管理器
        
        Args:
            cache_dir: 本地缓存目录
            config: mem0配置选项
            enable_mem0: 是否启用mem0（用于测试时可以禁用）
        """
        os.environ["OPENAI_API_KEY"] = "sk-5ceee3c3e7e422c812938b314925ded"
        os.environ["OPENAI_BASE_URL"] = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        self.enable_mem0 = enable_mem0 and Memory is not None
        config = {
            "llm": {  # 配置语言模型，用于理解文本和提取信息
                "provider": "openai_structured",  # 使用 OpenAI
                "config": {
                    "model": "text-embedding-v4",  # 性价比高的模型
                }
            },
            "vector_store": {  # 配置向量存储，用于存储和检索缓存内容
                "provider": "milvus",  # 使用本地存储，简单方便
                "config": {
                    "collection_name": "my_memories",  # Your collection name
                    "url": "./milvus.db", 
                }
            }
        }

        if self.enable_mem0:
            # mem0配置
            simple_config = config or {"version": "v1.1"}
            self.memory = Memory.from_config(simple_config)
        else:
            self.memory = None
    
    def add_memory(self, user_id: str, conversation_id: str, 
                   message: str, role: str = "user",
                   metadata: Optional[Dict] = None) -> Dict:
        """
        添加记忆到特定用户的特定会话
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            message: 消息内容
            role: 角色 (user/assistant/system)
            metadata: 额外的元数据
            
        Returns:
            操作结果
        """
        
        # 生成记忆ID
        timestamp = datetime.now().isoformat()
        memory_id = self._generate_memory_id(user_id, conversation_id, timestamp)
        
        # 如果启用mem0，添加到mem0
        mem0_id = None
        if self.enable_mem0 and self.memory:
            try:
                result = self.memory.add(
                    message,
                    user_id=f"{user_id}_{conversation_id}",
                    metadata={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "role": role,
                        **(metadata or {})
                    }
                )
                mem0_id = result.get("id") if isinstance(result, dict) else None
            except Exception as e:
                print(f"mem0添加失败: {e}")
        
        return {
            "status": "success",
            "memory_id": memory_id,
            "mem0_id": mem0_id
        }
    
    def search_in_conversation(self, user_id: str, conversation_id: str,
                              query: str, limit: int = 5) -> List[Dict]:
        """
        在特定会话中搜索记忆
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            匹配的记忆列表
        """
        matched = []
        # 如果启用mem0，也使用mem0搜索
        if self.enable_mem0 and self.memory:
            try:
                mem0_results = self.memory.search(
                    query=query,
                    user_id=f"{user_id}_{conversation_id}",
                    limit=limit
                )
                # 合并结果
                for result in mem0_results:
                    if len(matched) < limit:
                        matched.append(result)
            except Exception as e:
                print(f"mem0搜索失败: {e}")
        
        return matched[:limit]
    
    
    def get_conversation_context(self, user_id: str, conversation_id: str,
                                max_messages: int = 10,
                                max_tokens: int = 1000) -> str:
        """
        获取会话上下文摘要（用于LLM）
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            max_messages: 最大消息数量
            max_tokens: 最大token数（近似字符数）
            
        Returns:
            格式化的上下文字符串
        """
    
        memories = self.search_in_conversation(
            user_id, conversation_id, "", limit=max_messages * 2
        )
        # 构建上下文
        context_parts = []
        total_length = 0
        
        for memory in memories:
            role = memory.get("role", "user")
            message = memory.get("message", "")
            
            # 格式化消息
            if role == "user":
                formatted = f"User: {message}"
            elif role == "assistant":
                formatted = f"Assistant: {message}"
            else:
                formatted = f"System: {message}"
            
            # 检查长度
            if total_length + len(formatted) > max_tokens:
                # 如果超过长度，截断消息
                remaining = max_tokens - total_length
                if remaining > 50:  # 至少保留50个字符
                    formatted = formatted[:remaining] + "..."
                    context_parts.append(formatted)
                break
            
            context_parts.append(formatted)
            total_length += len(formatted) + 1  # +1 for newline
        return "\n".join(context_parts)
       
    def _generate_memory_id(self, user_id: str, conversation_id: str, 
                           timestamp: str) -> str:
        """生成记忆ID"""
        combined = f"{user_id}_{conversation_id}_{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
# 使用示例
if __name__ == "__main__":
    # 创建记忆管理器
    memory_manager = ContextMemoryManager(
        enable_mem0=True
    )
    
    # 用户和会话ID
    user_id = "user123"
    conversation_id_1 = "conv_001"
    conversation_id_2 = "conv_002"
    
    
    # 添加一些对话记忆
    print("\n=== 添加对话记忆到会话1 ===")
    memory_manager.add_memory(
        user_id, conversation_id_1,
        "我想学习Python的异步编程",
        role="user"
    )
    
    memory_manager.add_memory(
        user_id, conversation_id_1,
        "Python的异步编程主要使用async/await语法。让我为你介绍一下基础概念...",
        role="assistant"
    )
    
    memory_manager.add_memory(
        user_id, conversation_id_1,
        "能给我一个简单的例子吗？",
        role="user"
    )
    
    memory_manager.add_memory(
        user_id, conversation_id_1,
        "当然！这里是一个简单的异步函数示例：\n```python\nasync def hello():\n    await asyncio.sleep(1)\n    print('Hello')\n```",
        role="assistant"
    )
    
    # 添加不同的对话内容
    memory_manager.add_memory(
        user_id, conversation_id_2,
        "我需要分析一些销售数据",
        role="user"
    )
    
    memory_manager.add_memory(
        user_id, conversation_id_2,
        "我可以帮你分析销售数据。你有什么具体的分析需求吗？",
        role="assistant"
    )
    
    # 搜索功能
    print("\n=== 在会话1中搜索 'async' ===")
    search_results = memory_manager.search_in_conversation(
        user_id, conversation_id_1, "async"
    )
    for result in search_results:
        print(f"- {result['message'][:60]}...")
    

    # 获取会话上下文（用于LLM）
    print("\n=== 会话1的上下文摘要 ===")
    context = memory_manager.get_conversation_context(
        user_id, conversation_id_1,
        max_messages=5,
        max_tokens=500
    )
    print(context)
    
    # 演示另一个用户的独立会话
    print("\n=== 另一个用户的会话 ===")
    user_id_2 = "user456"
    conversation_id_3 = "conv_003"
    

    memory_manager.add_memory(
        user_id_2, conversation_id_3,
        "什么是神经网络？",
        role="user"
    )