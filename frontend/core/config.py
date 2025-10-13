import os
import streamlit as st


class FrontendConfig:
    """前端配置管理"""

    # 后端API配置
    FLASK_BACKEND_URL = os.getenv("FLASK_BACKEND_URL", "http://localhost:5000")

    # 应用配置
    PAGE_TITLE = "迷你豆包 AI 助手"
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    SIDEBAR_STATE = "expanded"

    # 状态检查间隔（秒）
    STATUS_CHECK_INTERVAL = 5
    STATUS_CACHE_DURATION = 5

    # UI配置
    MAX_MESSAGES_DISPLAY = 100
    MESSAGE_HISTORY_LIMIT = 50

    @classmethod
    def setup_page_config(cls):
        """设置页面配置"""
        st.set_page_config(
            page_title=cls.PAGE_TITLE,
            page_icon=cls.PAGE_ICON,
            layout=cls.LAYOUT,
            initial_sidebar_state=cls.SIDEBAR_STATE
        )