from abc import ABC, abstractmethod
import json
import requests


class BaseModelProvider(ABC):
    """模型提供商基类"""

    @abstractmethod
    def is_available(self):
        """检查模型是否可用"""
        pass

    @abstractmethod
    def stream_chat(self, messages, **kwargs):
        """流式聊天接口"""
        pass


class ModelResponse:
    """统一模型响应类"""

    def __init__(self, content=None, error=None, done=False):
        self.content = content
        self.error = error
        self.done = done

    def to_sse_format(self):
        """转换为SSE格式"""
        if self.error:
            return f"data: {json.dumps({'error': self.error})}\n\n"
        elif self.done:
            return "data: [DONE]\n\n"
        else:
            return f"data: {json.dumps({'content': self.content})}\n\n"