import streamlit as st


class StatusBarComponent:
    """状态栏组件"""

    def __init__(self, state):
        self.state = state

    def render(self):
        """渲染状态栏"""
        st.divider()

        # 获取状态信息
        model_status = self.state.get_model_status()
        processing = self.state.is_processing()
        error = self.state.get_connection_error()

        # 状态文本
        status_text = "🟢 就绪" if not processing else "🟡 正在处理请求..."
        if error:
            status_text = "🔴 连接错误"

        # 使用列布局
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            st.caption(f"状态: {status_text}")

        with col2:
            current_mode = model_status.get("preference", "auto")
            st.caption(f"模式: {current_mode}")

        with col3:
            from ..core.config import FrontendConfig
            st.caption(f"后端: {FrontendConfig.FLASK_BACKEND_URL}")