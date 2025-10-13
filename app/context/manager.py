import os
from datetime import datetime
from app.config import Config

class NaturalContextManager:
    """自然语言上下文管理器"""

    def __init__(self):
        self.conversation_history = []
        self.max_history = Config.MAX_CONVERSATION_HISTORY

    def add_message(self, role, content):
        """添加消息到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 保持历史记录长度
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def build_context_prompt(self, current_message):
        """构建上下文提示词"""
        # 基础系统提示
        system_prompt = """你是一个有帮助的AI助手。请根据完整的对话历史提供准确、连贯的回答。

对话指南：
1. 仔细阅读和理解整个对话历史
2. 如果用户提到过个人信息，请自然地使用这些信息
3. 保持回答与之前对话的一致性
4. 如果用户的问题需要上下文信息，请参考历史对话

当前对话历史："""

        # 添加对话历史
        for i, msg in enumerate(self.conversation_history[-5:]):
            system_prompt += f"\n{msg['role']}: {msg['content']}"

        system_prompt += f"\n\n当前用户消息: {current_message}"
        system_prompt += "\n\n请基于以上完整对话历史提供有帮助的回答。"

        return system_prompt

    def get_recent_messages(self, count=3):
        """获取最近的对话消息"""
        return self.conversation_history[-count:] if self.conversation_history else []

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []