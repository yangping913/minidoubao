from .base import BaseModelProvider, ModelResponse
from app.config import Config
import requests
import json


class DeepSeekProvider(BaseModelProvider):
    """DeepSeek模型提供商"""

    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL

    def is_available(self):
        """检查DeepSeek是否可用"""
        if not self.api_key:
            return False

        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get(
                "https://api.deepseek.com/v1/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def stream_chat(self, messages, **kwargs):
        """DeepSeek流式聊天"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2000)
        }

        try:
            response = requests.post(
                self.api_url,
                json=data,
                headers=headers,
                stream=True,
                timeout=30
            )

            if response.status_code != 200:
                yield ModelResponse(error=f'API错误: {response.status_code}')
                return

            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        if data_str == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    yield ModelResponse(content=content)
                        except json.JSONDecodeError:
                            continue

            # 返回完整响应用于历史记录
            yield ModelResponse(content=full_response, done=True)

        except Exception as e:
            yield ModelResponse(error=f'DeepSeek请求失败: {str(e)}')