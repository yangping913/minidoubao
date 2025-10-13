import streamlit as st
import time


class ChatInterfaceComponent:
    """聊天界面组件"""

    def __init__(self, state, api_manager):
        self.state = state
        self.api_manager = api_manager

    def render_messages(self):
        """渲染消息历史"""
        messages = self.state.get_messages()

        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 可选：显示时间戳
                if self.state.get_user_settings().get("show_timestamps", True):
                    if "timestamp" in message:
                        timestamp = time.strftime(
                            "%H:%M:%S",
                            time.localtime(message["timestamp"])
                        )
                        st.caption(timestamp)

    def render_input(self):
        """渲染输入区域"""
        if prompt := st.chat_input("请输入您的问题...",
                                   disabled=self.state.is_processing(),
                                   key="chat_input"):
            self._handle_user_input(prompt)

    def _handle_user_input(self, prompt: str):
        """处理用户输入"""
        # 设置处理状态
        self.state.set_processing(True)

        try:
            # 发送消息
            self._send_message(prompt)
        except Exception as e:
            st.error(f"发送消息失败: {str(e)}")
        finally:
            # 确保处理状态被重置
            self.state.set_processing(False)

    def _send_message(self, message: str):
        """发送消息到后端"""
        # 添加用户消息到状态
        self.state.add_message("user", message)

        # 创建占位符用于流式显示
        assistant_placeholder = st.empty()
        full_response = ""

        # 处理流式响应
        for chunk in self.api_manager.client.stream_chat(message):
            if "error" in chunk:
                st.error(f"API错误: {chunk['error']}")
                break
            elif "content" in chunk:
                content = chunk["content"]
                if content:
                    full_response += content
                    # 更新显示，带光标效果
                    assistant_placeholder.markdown(full_response + "▌")

        # 更新最终显示
        if full_response.strip():
            assistant_placeholder.markdown(full_response)
            self.state.add_message("assistant", full_response)
        else:
            assistant_placeholder.empty()

        # 刷新模型状态
        try:
            new_status = self.api_manager.get_model_status_cached(force=True)
            if new_status:
                self.state.update_model_status(new_status)
        except:
            pass  # 状态刷新失败不影响主流程

    def render(self):
        """渲染完整聊天界面"""
        st.title("迷你豆包 AI 助手")
        st.caption("基于 Flask + Streamlit 的智能聊天助手")

        # 渲染消息历史
        self.render_messages()

        # 渲染输入区域
        self.render_input()