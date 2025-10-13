import requests
import json
import streamlit as st
import time
from typing import Dict, Any, Optional, Generator


class APIClient:
    """API客户端封装类"""

    def __init__(self, base_url: str = None):
        from .config import FrontendConfig
        self.base_url = base_url or FrontendConfig.FLASK_BACKEND_URL
        self.timeout = 30

    def _handle_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """统一处理请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"API错误: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', error_msg)
                    except:
                        error_msg = response.text[:100]
                raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络连接失败: {str(e)}")

    def get_model_status(self) -> Optional[Dict[str, Any]]:
        """获取模型状态"""
        return self._handle_request('GET', '/api/models/status')

    def switch_model(self, model: str) -> Optional[Dict[str, Any]]:
        """切换模型"""
        return self._handle_request('POST', '/api/models/switch',
                                    json={"model": model})

    def clear_context(self) -> Optional[Dict[str, Any]]:
        """清空对话上下文"""
        return self._handle_request('POST', '/api/context/clear')

    def get_debug_info(self) -> Optional[Dict[str, Any]]:
        """获取调试信息"""
        return self._handle_request('GET', '/api/debug/context')

    def health_check(self) -> Optional[Dict[str, Any]]:
        """健康检查"""
        return self._handle_request('GET', '/health')

    def stream_chat(self, message: str) -> Generator[Dict[str, Any], None, None]:
        """流式聊天"""
        url = f"{self.base_url}/api/stream-chat"

        try:
            response = requests.post(
                url,
                json={"message": message},
                stream=True,
                timeout=self.timeout
            )

            if response.status_code != 200:
                yield {"error": f"请求失败: HTTP {response.status_code}"}
                return

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        if data_str == '[DONE]':
                            break

                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            yield {"error": f"请求失败: {str(e)}"}


class APIManager:
    """API管理器"""

    def __init__(self):
        self.client = APIClient()
        self._cache = {}
        self._cache_ttl = 5  # 缓存5秒

    def get_model_status_cached(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """带缓存的获取模型状态"""
        cache_key = "model_status"
        current_time = time.time()

        if not force and cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                return cached_data

        try:
            status = self.client.get_model_status()
            self._cache[cache_key] = (status, current_time)
            return status
        except Exception as e:
            # 错误处理，可以记录日志或设置错误状态
            return None