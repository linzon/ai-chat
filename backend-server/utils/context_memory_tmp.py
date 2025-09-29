import time
import threading
from collections import OrderedDict
import hashlib

class ConversationCache:
    def __init__(self, max_size=1000, ttl=24*3600, max_context_length=10000):
        """
        初始化对话缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间（秒），默认1天
            max_context_length: 最大上下文长度（字符数）
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.max_context_length = max_context_length
        self.lock = threading.RLock()
    
    def _get_key(self, user_id, conversation_id):
        """生成缓存键"""
        key_str = f"{user_id}_{conversation_id}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _trim_context(self, context):
        """修剪上下文，确保不超过最大长度"""
        if len(context) <= self.max_context_length:
            return context
        
        # 从开头删除多余字符，保留最新的内容
        return context[-self.max_context_length:]
    
    def _clean_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, value in self.cache.items():
            if current_time - value['last_access'] > self.ttl:
                expired_keys.append(key)
            else:
                # 因为是有序字典，遇到第一个未过期的就可以停止
                break
        
        for key in expired_keys:
            del self.cache[key]
    
    def add_message(self, user_id, conversation_id, role, content):
        """
        添加消息到对话上下文
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
        """
        key = self._get_key(user_id, conversation_id)
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time()
        }
        
        with self.lock:
            # 清理过期缓存
            self._clean_expired()
            
            if key in self.cache:
                # 更新现有对话
                self.cache[key]['messages'].append(message)
                # 修剪上下文
                context_str = self._messages_to_string(self.cache[key]['messages'])
                self.cache[key]['context'] = self._trim_context(context_str)
                self.cache[key]['last_access'] = time.time()
                # 移动到最新位置
                self.cache.move_to_end(key)
            else:
                # 创建新对话
                context_str = self._messages_to_string([message])
                self.cache[key] = {
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'messages': [message],
                    'context': self._trim_context(context_str),
                    'last_access': time.time(),
                    'created_at': time.time()
                }
                
                # 如果超过最大大小，删除最旧的
                if len(self.cache) > self.max_size:
                    self.cache.popitem(last=False)
    
    def _messages_to_string(self, messages):
        """将消息列表转换为字符串"""
        context_parts = []
        for msg in messages:
            context_parts.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(context_parts)
    
    def get_context(self, user_id, conversation_id):
        """
        获取对话上下文
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            
        Returns:
            str: 对话上下文字符串，如果不存在或过期返回None
        """
        key = self._get_key(user_id, conversation_id)
        
        with self.lock:
            if key in self.cache:
                data = self.cache[key]
                current_time = time.time()
                
                # 检查是否过期
                if current_time - data['last_access'] > self.ttl:
                    del self.cache[key]
                    return None
                
                # 更新访问时间并移动到最新位置
                data['last_access'] = current_time
                self.cache.move_to_end(key)
                return data['context']
            
            return None
    
    def get_messages(self, user_id, conversation_id):
        """
        获取原始消息列表
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            
        Returns:
            list: 消息列表，如果不存在或过期返回None
        """
        key = self._get_key(user_id, conversation_id)
        
        with self.lock:
            if key in self.cache:
                data = self.cache[key]
                current_time = time.time()
                
                # 检查是否过期
                if current_time - data['last_access'] > self.ttl:
                    del self.cache[key]
                    return None
                
                # 更新访问时间并移动到最新位置
                data['last_access'] = current_time
                self.cache.move_to_end(key)
                return data['messages']
            
            return None
    
    def clear_conversation(self, user_id, conversation_id):
        """清除特定对话"""
        key = self._get_key(user_id, conversation_id)
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear_expired(self):
        """清除所有过期缓存"""
        with self.lock:
            self._clean_expired()
    
    def get_stats(self):
        """获取缓存统计信息"""
        with self.lock:
            current_time = time.time()
            active_count = 0
            total_messages = 0
            total_chars = 0
            
            for data in self.cache.values():
                if current_time - data['last_access'] <= self.ttl:
                    active_count += 1
                    total_messages += len(data['messages'])
                    total_chars += len(data['context'])
            
            return {
                'total_conversations': len(self.cache),
                'active_conversations': active_count,
                'total_messages': total_messages,
                'total_chars': total_chars
            }

# 使用示例
if __name__ == "__main__":
    # 创建缓存实例
    cache = ConversationCache(max_size=1000, ttl=24*3600, max_context_length=10000)
    
    # 模拟对话
    user_id = "user123"
    conversation_id = "conv456"
    
    # 添加用户消息
    cache.add_message(user_id, conversation_id, "user", "你好，我想了解AI技术")
    
    # 添加助手回复
    cache.add_message(user_id, conversation_id, "assistant", "你好！我很乐意帮助你了解AI技术。AI是人工智能的缩写，它涵盖了很多领域...")
    
    # 继续对话
    cache.add_message(user_id, conversation_id, "user", "能具体讲讲机器学习吗？")
    cache.add_message(user_id, conversation_id, "assistant", "机器学习是AI的一个重要分支，它让计算机能够从数据中学习而无需显式编程...")
    
    # 获取上下文
    context = cache.get_context(user_id, conversation_id)
    print("当前对话上下文：")
    print(context)
    print("\n" + "="*50 + "\n")
    
    # 获取统计信息
    stats = cache.get_stats()
    print("缓存统计：")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 清除对话
    # cache.clear_conversation(user_id, conversation_id)