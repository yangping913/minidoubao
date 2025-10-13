import streamlit as st
import time


class SidebarComponent:
    """侧边栏组件"""

    def __init__(self, state, api_manager):
        self.state = state
        self.api_manager = api_manager

    def render_model_status(self):
        """渲染模型状态部分"""
        st.subheader("模型状态")

        col1, col2 = st.columns(2)

        with col1:
            deepseek_status = self._get_status_display("deepseek")
            st.metric("DeepSeek", deepseek_status)

        with col2:
            ollama_status = self._get_status_display("ollama")
            st.metric("Ollama", ollama_status)

        # 请求计数和运行时间
        model_status = self.state.get_model_status()
        st.metric("请求次数", model_status.get("request_count", 0))

        uptime = model_status.get('uptime', 0)
        uptime_display = f"{uptime}秒" if uptime < 60 else f"{uptime // 60}分{uptime % 60}秒"
        st.metric("运行时间", uptime_display)

    def _get_status_display(self, model_name: str) -> str:
        """获取状态显示文本"""
        status = self.state.get_model_status()
        if status.get(model_name):
            return "🟢 在线"
        else:
            return "🔴 离线"

    def render_model_selector(self):
        """渲染模型选择器"""
        st.divider()
        st.subheader("模型选择")

        model_status = self.state.get_model_status()
        current_model = model_status.get("preference", "auto")

        model_options = ["auto", "deepseek", "ollama"]
        selected_model = st.radio(
            "选择模型",
            options=model_options,
            index=model_options.index(current_model) if current_model in model_options else 0,
            help="auto: 自动选择可用模型\ndeepseek: 优先使用DeepSeek\nollama: 优先使用Ollama"
        )

        # 只有当选择的模型与当前模型不同时才显示切换按钮
        if selected_model != current_model:
            if st.button("应用选择", use_container_width=True, key="apply_model"):
                if self._switch_model(selected_model):
                    st.rerun()

    def _switch_model(self, model: str) -> bool:
        """切换模型"""
        try:
            result = self.api_manager.client.switch_model(model)
            if result and result.get("status") == "success":
                # 强制刷新状态
                new_status = self.api_manager.get_model_status_cached(force=True)
                if new_status:
                    self.state.update_model_status(new_status)
                st.success(f"已切换到 {model} 模式")
                return True
            else:
                error_msg = result.get('error', '未知错误') if result else '切换失败'
                st.error(f"切换失败: {error_msg}")
        except Exception as e:
            st.error(f"切换模型失败: {str(e)}")
        return False

    def render_controls(self):
        """渲染控制按钮"""
        st.divider()
        st.subheader("其他选项")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 刷新状态", use_container_width=True, key="refresh_status"):
                new_status = self.api_manager.get_model_status_cached(force=True)
                if new_status:
                    self.state.update_model_status(new_status)
                    st.success("状态已刷新")
                else:
                    st.error("刷新失败")

        with col2:
            if st.button("🗑️ 清空对话", use_container_width=True, key="clear_chat",
                         type="secondary"):
                self._clear_conversation()

        if st.button("🐛 调试信息", use_container_width=True, key="debug_info"):
            self._show_debug_info()

    def _clear_conversation(self):
        """清空对话"""
        try:
            result = self.api_manager.client.clear_context()
            if result and result.get("status") == "success":
                self.state.clear_messages()
                st.success("对话历史已清空")
            else:
                st.error("清空对话失败")
        except Exception as e:
            st.error(f"清空对话失败: {str(e)}")

    def _show_debug_info(self):
        """显示调试信息"""
        try:
            debug_info = self.api_manager.client.get_debug_info()
            if debug_info:
                st.write("调试信息:", debug_info)
            else:
                st.error("获取调试信息失败")
        except Exception as e:
            st.error(f"获取调试信息失败: {str(e)}")

    def render(self):
        """渲染完整侧边栏"""
        st.title("控制面板")

        # 显示连接状态
        error = self.state.get_connection_error()
        if error:
            st.error(f"连接错误: {error}")
        else:
            st.success("后端连接正常")

        st.divider()

        # 渲染各个部分
        self.render_model_status()
        self.render_model_selector()
        self.render_controls()