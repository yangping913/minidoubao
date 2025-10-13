from .base import BaseModelProvider, ModelResponse
from app.config import Config
import requests
import json


class OllamaProvider(BaseModelProvider):
    """Ollama模型提供商"""

    def __init__(self):
        self.api_url = Config.OLLAMA_API_URL
        self.model_name = Config.OLLAMA_MODEL_NAME

    def is_available(self):
        """检查Ollama是否可用"""
        try:
            response = requests.get(
                f"{self.api_url.replace('/api/generate', '')}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def stream_chat(self, prompt, **kwargs):
        """Ollama流式聊天"""
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True
        }

        try:
            response = requests.post(
                self.api_url,
                json=data,
                stream=True,
                timeout=30
            )

            if response.status_code != 200:
                yield ModelResponse(error=f'Ollama API错误: {response.status_code}')
                return

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if 'response' in chunk:
                            content = chunk['response']
                            if content:
                                full_response += content
                                yield ModelResponse(content=content)
                        if chunk.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue

            # 返回完整响应用于历史记录
            yield ModelResponse(content=full_response, done=True)

        except Exception as e:
            yield ModelResponse(error=f'Ollama请求失败: {str(e)}')