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


class ConversationStatus(Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"


@dataclass
class ConversationInfo:
    """会话信息数据类"""
    conversation_id: str
    user_id: str
    created_at: str
    updated_at: str
    status: ConversationStatus
    metadata: Dict[str, Any]
    message_count: int = 0


@dataclass
class MemoryRecord:
    """记忆记录数据类"""
    id: str
    user_id: str
    conversation_id: str
    message: str
    role: str  # user/assistant/system
    timestamp: str
    metadata: Dict[str, Any]
    memory_id: Optional[str] = None  # mem0返回的ID


class LocalCacheStorage:
    """本地缓存存储适配器 - 支持用户和会话两级存储"""
    
    def __init__(self, cache_dir: str = "./memory_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建用户和会话子目录
        self.users_dir = self.cache_dir / "users"
        self.conversations_dir = self.cache_dir / "conversations"
        self.users_dir.mkdir(exist_ok=True)
        self.conversations_dir.mkdir(exist_ok=True)
    
    def _get_safe_filename(self, *parts: str) -> str:
        """生成安全的文件名"""
        combined = "_".join(parts)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_user_path(self, user_id: str) -> Path:
        """获取用户数据路径"""
        filename = self._get_safe_filename(user_id)
        return self.users_dir / f"user_{filename}.pkl"
    
    def _get_conversation_path(self, user_id: str, conversation_id: str) -> Path:
        """获取会话数据路径"""
        filename = self._get_safe_filename(user_id, conversation_id)
        return self.conversations_dir / f"conv_{filename}.pkl"
    
    def save_user_data(self, user_id: str, data: Any):
        """保存用户级数据"""
        path = self._get_user_path(user_id)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load_user_data(self, user_id: str) -> Optional[Any]:
        """加载用户级数据"""
        path = self._get_user_path(user_id)
        if path.exists():
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save_conversation_data(self, user_id: str, conversation_id: str, data: Any):
        """保存会话级数据"""
        path = self._get_conversation_path(user_id, conversation_id)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load_conversation_data(self, user_id: str, conversation_id: str) -> Optional[Any]:
        """加载会话级数据"""
        path = self._get_conversation_path(user_id, conversation_id)
        if path.exists():
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def delete_conversation(self, user_id: str, conversation_id: str):
        """删除会话数据"""
        path = self._get_conversation_path(user_id, conversation_id)
        if path.exists():
            path.unlink()
    
    def delete_user(self, user_id: str):
        """删除用户所有数据"""
        # 删除用户数据文件
        user_path = self._get_user_path(user_id)
        if user_path.exists():
            user_path.unlink()
        
        # 删除该用户的所有会话文件
        pattern = f"conv_*"
        for conv_file in self.conversations_dir.glob(pattern):
            # 这里需要更精确的匹配逻辑
            pass
    
    def list_user_conversations(self, user_id: str) -> List[str]:
        """列出用户的所有会话ID"""
        user_data = self.load_user_data(user_id)
        if user_data and "conversations" in user_data:
            return list(user_data["conversations"].keys())
        return []


class ContextMemoryManager:
    """支持会话级别的上下文记忆管理器"""
    
    def __init__(self, cache_dir: str = "./memory_cache", 
                 config: Optional[Dict] = None,
                 enable_mem0: bool = True):
        """
        初始化记忆管理器
        
        Args:
            cache_dir: 本地缓存目录
            config: mem0配置选项
            enable_mem0: 是否启用mem0（用于测试时可以禁用）
        """
        self.storage = LocalCacheStorage(cache_dir)
        self.enable_mem0 = enable_mem0 and Memory is not None
        
        if self.enable_mem0:
            # mem0配置
            simple_config = config or {"version": "v1.1"}
            self.memory = Memory.from_config(simple_config)
        else:
            self.memory = None
        
        # 内存缓存：用户 -> 会话 -> 记忆列表
        self.cache: Dict[str, Dict[str, List[MemoryRecord]]] = {}
        
        # 会话信息缓存
        self.conversations: Dict[Tuple[str, str], ConversationInfo] = {}
    
    def create_conversation(self, user_id: str, conversation_id: str,
                          metadata: Optional[Dict] = None) -> ConversationInfo:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            metadata: 会话元数据
            
        Returns:
            会话信息对象
        """
        now = datetime.now().isoformat()
        conv_info = ConversationInfo(
            conversation_id=conversation_id,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            status=ConversationStatus.ACTIVE,
            metadata=metadata or {},
            message_count=0
        )
        
        # 存储到缓存
        key = (user_id, conversation_id)
        self.conversations[key] = conv_info
        
        # 初始化内存缓存结构
        if user_id not in self.cache:
            self.cache[user_id] = {}
        if conversation_id not in self.cache[user_id]:
            self.cache[user_id][conversation_id] = []
        
        # 更新用户级数据
        self._update_user_conversations(user_id, conversation_id, conv_info)
        
        return conv_info
    
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
        # 确保会话存在
        key = (user_id, conversation_id)
        if key not in self.conversations:
            self.create_conversation(user_id, conversation_id)
        
        # 生成记忆ID
        timestamp = datetime.now().isoformat()
        memory_id = self._generate_memory_id(user_id, conversation_id, timestamp)
        
        # 创建记忆记录
        record = MemoryRecord(
            id=memory_id,
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            role=role,
            timestamp=timestamp,
            metadata=metadata or {}
        )
        
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
                record.memory_id = mem0_id
            except Exception as e:
                print(f"mem0添加失败: {e}")
        
        # 添加到内存缓存
        if user_id not in self.cache:
            self.cache[user_id] = {}
        if conversation_id not in self.cache[user_id]:
            self.cache[user_id][conversation_id] = []
        
        self.cache[user_id][conversation_id].append(record)
        
        # 更新会话信息
        conv_info = self.conversations[key]
        conv_info.message_count += 1
        conv_info.updated_at = timestamp
        
        # 持久化到本地缓存
        self._save_conversation(user_id, conversation_id)
        
        return {
            "status": "success",
            "memory_id": memory_id,
            "mem0_id": mem0_id,
            "record": asdict(record)
        }
    
    def get_conversation_memories(self, user_id: str, conversation_id: str,
                                 limit: Optional[int] = None) -> List[Dict]:
        """
        获取特定会话的记忆历史
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            limit: 返回的记忆条数限制
            
        Returns:
            记忆列表
        """
        # 尝试从缓存加载
        if user_id not in self.cache or conversation_id not in self.cache[user_id]:
            self._load_conversation(user_id, conversation_id)
        
        memories = self.cache.get(user_id, {}).get(conversation_id, [])
        
        if limit:
            memories = memories[-limit:]
        
        return [asdict(m) for m in memories]
    
    def get_user_conversations(self, user_id: str, 
                              include_archived: bool = False) -> List[ConversationInfo]:
        """
        获取用户的所有会话
        
        Args:
            user_id: 用户ID
            include_archived: 是否包含已归档的会话
            
        Returns:
            会话信息列表
        """
        user_data = self.storage.load_user_data(user_id)
        if not user_data:
            return []
        
        conversations = []
        for conv_id, conv_data in user_data.get("conversations", {}).items():
            conv_info = ConversationInfo(**conv_data)
            if include_archived or conv_info.status == ConversationStatus.ACTIVE:
                conversations.append(conv_info)
        
        # 按更新时间倒序排序
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations
    
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
        memories = self.get_conversation_memories(user_id, conversation_id)
        
        # 简单的关键词搜索
        query_lower = query.lower()
        matched = []
        
        for memory in memories:
            if query_lower in memory["message"].lower():
                matched.append(memory)
                if len(matched) >= limit:
                    break
        
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
    
    def search_across_user(self, user_id: str, query: str, 
                          limit: int = 10) -> List[Dict]:
        """
        跨用户所有会话搜索
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            limit: 返回结果数量限制
            
        Returns:
            匹配的记忆列表，包含会话ID信息
        """
        all_results = []
        conversations = self.get_user_conversations(user_id, include_archived=True)
        
        for conv_info in conversations:
            conv_results = self.search_in_conversation(
                user_id, conv_info.conversation_id, query, limit
            )
            
            # 添加会话信息到结果
            for result in conv_results:
                result["conversation_info"] = asdict(conv_info)
                all_results.append(result)
        
        # 按时间戳排序并限制数量
        all_results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_results[:limit]
    
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
        memories = self.get_conversation_memories(user_id, conversation_id, limit=max_messages)
        
        if not memories:
            return "No conversation history."
        
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
    
    def archive_conversation(self, user_id: str, conversation_id: str) -> Dict:
        """
        归档会话
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            
        Returns:
            操作结果
        """
        key = (user_id, conversation_id)
        if key in self.conversations:
            self.conversations[key].status = ConversationStatus.ARCHIVED
            self.conversations[key].updated_at = datetime.now().isoformat()
            self._save_conversation(user_id, conversation_id)
            return {"status": "success", "message": "Conversation archived"}
        
        return {"status": "error", "message": "Conversation not found"}
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> Dict:
        """
        删除会话及其所有记忆
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            
        Returns:
            操作结果
        """
        # 从内存缓存删除
        if user_id in self.cache and conversation_id in self.cache[user_id]:
            del self.cache[user_id][conversation_id]
        
        # 从会话缓存删除
        key = (user_id, conversation_id)
        if key in self.conversations:
            del self.conversations[key]
        
        # 从存储删除
        self.storage.delete_conversation(user_id, conversation_id)
        
        # 更新用户数据
        user_data = self.storage.load_user_data(user_id) or {"conversations": {}}
        if conversation_id in user_data.get("conversations", {}):
            del user_data["conversations"][conversation_id]
            self.storage.save_user_data(user_id, user_data)
        
        # 如果启用mem0，删除mem0中的记忆
        if self.enable_mem0 and self.memory:
            try:
                self.memory.delete_all(user_id=f"{user_id}_{conversation_id}")
            except Exception as e:
                print(f"mem0删除失败: {e}")
        
        return {"status": "success", "message": "Conversation deleted"}
    
    def export_conversation(self, user_id: str, conversation_id: str,
                           format: str = "json") -> str:
        """
        导出会话数据
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            format: 导出格式 (json/markdown/text)
            
        Returns:
            导出的数据字符串
        """
        memories = self.get_conversation_memories(user_id, conversation_id)
        key = (user_id, conversation_id)
        conv_info = self.conversations.get(key)
        
        if format == "json":
            export_data = {
                "conversation_info": asdict(conv_info) if conv_info else None,
                "memories": memories
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            lines = []
            if conv_info:
                lines.append(f"# Conversation: {conv_info.conversation_id}")
                lines.append(f"**User:** {conv_info.user_id}")
                lines.append(f"**Created:** {conv_info.created_at}")
                lines.append(f"**Messages:** {conv_info.message_count}")
                lines.append("\n---\n")
            
            for memory in memories:
                role = memory.get("role", "user").capitalize()
                message = memory.get("message", "")
                timestamp = memory.get("timestamp", "")
                lines.append(f"### {role} ({timestamp})")
                lines.append(f"{message}\n")
            
            return "\n".join(lines)
        
        else:  # text format
            lines = []
            if conv_info:
                lines.append(f"Conversation: {conv_info.conversation_id}")
                lines.append(f"User: {conv_info.user_id}")
                lines.append(f"Created: {conv_info.created_at}")
                lines.append("=" * 50)
            
            for memory in memories:
                role = memory.get("role", "user").upper()
                message = memory.get("message", "")
                timestamp = memory.get("timestamp", "")
                lines.append(f"[{timestamp}] {role}:")
                lines.append(f"{message}")
                lines.append("-" * 30)
            
            return "\n".join(lines)
    
    def _generate_memory_id(self, user_id: str, conversation_id: str, 
                           timestamp: str) -> str:
        """生成记忆ID"""
        combined = f"{user_id}_{conversation_id}_{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _update_user_conversations(self, user_id: str, conversation_id: str,
                                  conv_info: ConversationInfo):
        """更新用户的会话列表"""
        user_data = self.storage.load_user_data(user_id) or {}
        if "conversations" not in user_data:
            user_data["conversations"] = {}
        
        user_data["conversations"][conversation_id] = asdict(conv_info)
        self.storage.save_user_data(user_id, user_data)
    
    def _save_conversation(self, user_id: str, conversation_id: str):
        """保存会话数据到本地缓存"""
        if user_id in self.cache and conversation_id in self.cache[user_id]:
            memories = self.cache[user_id][conversation_id]
            # 转换为可序列化格式
            serializable_memories = [asdict(m) for m in memories]
            self.storage.save_conversation_data(user_id, conversation_id, serializable_memories)
        
        # 同时更新用户级数据
        key = (user_id, conversation_id)
        if key in self.conversations:
            self._update_user_conversations(user_id, conversation_id, self.conversations[key])
    
    def _load_conversation(self, user_id: str, conversation_id: str):
        """从本地缓存加载会话数据"""
        data = self.storage.load_conversation_data(user_id, conversation_id)
        
        if user_id not in self.cache:
            self.cache[user_id] = {}
        
        if data:
            # 转换为MemoryRecord对象
            memories = [MemoryRecord(**record) for record in data]
            self.cache[user_id][conversation_id] = memories
        else:
            self.cache[user_id][conversation_id] = []
        
        # 加载会话信息
        user_data = self.storage.load_user_data(user_id)
        if user_data and conversation_id in user_data.get("conversations", {}):
            conv_data = user_data["conversations"][conversation_id]
            # 处理枚举类型
            if "status" in conv_data and isinstance(conv_data["status"], str):
                conv_data["status"] = ConversationStatus(conv_data["status"])
            key = (user_id, conversation_id)
            self.conversations[key] = ConversationInfo(**conv_data)


# 使用示例
if __name__ == "__main__":
    # 创建记忆管理器
    memory_manager = ContextMemoryManager(
        cache_dir="./conversation_memory_cache",
        enable_mem0=False  # 演示时可以禁用mem0
    )
    
    # 用户和会话ID
    user_id = "user123"
    conversation_id_1 = "conv_001"
    conversation_id_2 = "conv_002"
    
    print("=== 创建第一个会话 ===")
    conv1 = memory_manager.create_conversation(
        user_id, 
        conversation_id_1,
        metadata={"topic": "Python学习", "channel": "web"}
    )
    print(f"会话创建成功: {conv1.conversation_id}")
    
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
    
    # 创建第二个会话
    print("\n=== 创建第二个会话 ===")
    conv2 = memory_manager.create_conversation(
        user_id,
        conversation_id_2,
        metadata={"topic": "数据分析", "channel": "mobile"}
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
    
    # 获取会话1的记忆
    print("\n=== 会话1的对话历史 ===")
    conv1_memories = memory_manager.get_conversation_memories(user_id, conversation_id_1)
    for memory in conv1_memories:
        print(f"[{memory['role']}]: {memory['message'][:50]}...")
    
    # 获取会话2的记忆
    print("\n=== 会话2的对话历史 ===")
    conv2_memories = memory_manager.get_conversation_memories(user_id, conversation_id_2)
    for memory in conv2_memories:
        print(f"[{memory['role']}]: {memory['message'][:50]}...")
    
    # 获取用户的所有会话
    print("\n=== 用户的所有会话 ===")
    user_conversations = memory_manager.get_user_conversations(user_id)
    for conv in user_conversations:
        print(f"- {conv.conversation_id}: {conv.metadata.get('topic', 'Unknown')} "
              f"(消息数: {conv.message_count})")
    
    # 搜索功能
    print("\n=== 在会话1中搜索 'async' ===")
    search_results = memory_manager.search_in_conversation(
        user_id, conversation_id_1, "async"
    )
    for result in search_results:
        print(f"- {result['message'][:60]}...")
    
    # 跨会话搜索
    print("\n=== 跨所有会话搜索 '数据' ===")
    cross_search = memory_manager.search_across_user(user_id, "数据")
    for result in cross_search:
        conv_id = result.get("conversation_id", "unknown")
        print(f"- [{conv_id}]: {result['message'][:50]}...")
    
    # 获取会话上下文（用于LLM）
    print("\n=== 会话1的上下文摘要 ===")
    context = memory_manager.get_conversation_context(
        user_id, conversation_id_1,
        max_messages=5,
        max_tokens=500
    )
    print(context)
    
    # 导出会话数据
    print("\n=== 导出会话1数据 (Markdown) ===")
    exported = memory_manager.export_conversation(
        user_id, conversation_id_1,
        format="markdown"
    )
    print(exported[:500] + "..." if len(exported) > 500 else exported)
    
    # 归档会话
    print("\n=== 归档会话1 ===")
    result = memory_manager.archive_conversation(user_id, conversation_id_1)
    print(result)
    
    # 演示另一个用户的独立会话
    print("\n=== 另一个用户的会话 ===")
    user_id_2 = "user456"
    conversation_id_3 = "conv_003"
    
    memory_manager.create_conversation(
        user_id_2, conversation_id_3,
        metadata={"topic": "机器学习"}
    )
    
    memory_manager.add_memory(
        user_id_2, conversation_id_3,
        "什么是神经网络？",
        role="user"
    )
    
    user2_memories = memory_manager.get_conversation_memories(user_id_2, conversation_id_3)
    print(f"用户2的会话记忆数: {len(user2_memories)}")