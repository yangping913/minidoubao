import streamlit as st
import time
from typing import Dict, Any, List, Optional


class AppState:
    """应用状态管理类"""

    def __init__(self):
        self._init_session_state()

    def _init_session_state(self):
        """初始化会话状态"""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "model_status" not in st.session_state:
            st.session_state.model_status = {
                "deepseek": False,
                "ollama": False,
                "preference": "auto",
                "request_count": 0,
                "uptime": 0
            }

        if "processing" not in st.session_state:
            st.session_state.processing = False

        if "last_model_check" not in st.session_state:
            st.session_state.last_model_check = 0

        if "connection_error" not in st.session_state:
            st.session_state.connection_error = None

        if "user_settings" not in st.session_state:
            st.session_state.user_settings = {
                "auto_refresh": True,
                "show_timestamps": True,
                "theme": "default"
            }

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取消息列表"""
        return st.session_state.messages

    def add_message(self, role: str, content: str):
        """添加消息"""
        st.session_state.messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        # 限制消息数量
        if len(st.session_state.messages) > 50:
            st.session_state.messages = st.session_state.messages[-50:]

    def clear_messages(self):
        """清空消息"""
        st.session_state.messages = []

    def update_model_status(self, status: Dict[str, Any]):
        """更新模型状态"""
        st.session_state.model_status.update(status)
        st.session_state.last_model_check = time.time()

    def get_model_status(self) -> Dict[str, Any]:
        """获取模型状态"""
        return st.session_state.model_status.copy()

    def set_processing(self, processing: bool):
        """设置处理状态"""
        st.session_state.processing = processing

    def is_processing(self) -> bool:
        """检查是否正在处理"""
        return st.session_state.processing

    def set_connection_error(self, error: Optional[str]):
        """设置连接错误"""
        st.session_state.connection_error = error

    def get_connection_error(self) -> Optional[str]:
        """获取连接错误"""
        return st.session_state.connection_error

    def should_check_status(self) -> bool:
        """检查是否需要刷新状态"""
        current_time = time.time()
        return (current_time - st.session_state.last_model_check > 5 or
                st.session_state.last_model_check == 0)

    def get_user_settings(self) -> Dict[str, Any]:
        """获取用户设置"""
        return st.session_state.user_settings.copy()