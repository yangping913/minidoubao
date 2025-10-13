import sys
import os
import streamlit as st

# 设置正确的Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_root = current_dir
sys.path.insert(0, frontend_root)

# 导入核心模块
try:
    from core.config import FrontendConfig
    from core.state import AppState
    from core.api_client import APIManager
    from components.sidebar import SidebarComponent
    from components.chat_interface import ChatInterfaceComponent
    from components.status_bar import StatusBarComponent
except ImportError as e:
    st.error(f"导入错误: {e}")
    st.error("请确保所有模块文件存在且路径正确")
    st.stop()

# 设置页面配置
FrontendConfig.setup_page_config()


class MiniDoubaoApp:
    """迷你豆包主应用类"""

    def __init__(self):
        # 初始化核心组件
        self.state = AppState()
        self.api_manager = APIManager()

        # 初始化UI组件
        self.sidebar = SidebarComponent(self.state, self.api_manager)
        self.chat_interface = ChatInterfaceComponent(self.state, self.api_manager)
        self.status_bar = StatusBarComponent(self.state)

    def _auto_refresh_status(self):
        """自动刷新状态"""
        if self.state.should_check_status():
            try:
                new_status = self.api_manager.get_model_status_cached(force=True)
                if new_status:
                    self.state.update_model_status(new_status)
                    self.state.set_connection_error(None)
                else:
                    self.state.set_connection_error("无法获取后端状态")
            except Exception as e:
                self.state.set_connection_error(str(e))

    def setup_auto_refresh(self):
        """设置自动刷新"""
        if self.state.get_user_settings().get("auto_refresh", True):
            self._auto_refresh_status()

    def render(self):
        """渲染完整应用"""
        # 设置自动刷新
        self.setup_auto_refresh()

        # 侧边栏
        with st.sidebar:
            self.sidebar.render()

        # 主内容区
        self.chat_interface.render()

        # 状态栏
        self.status_bar.render()


def main():
    """主函数"""
    try:
        app = MiniDoubaoApp()
        app.render()
    except Exception as e:
        st.error(f"应用初始化失败: {str(e)}")
        st.info("请确保后端服务正在运行")


if __name__ == "__main__":
    main()