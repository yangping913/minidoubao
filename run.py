from app import create_app
from app.config import Config
import threading
import time

app = create_app()


def background_status_updater():
    """后台状态更新线程"""
    while True:
        time.sleep(30)
        app.model_manager.update_status()


if __name__ == '__main__':
    # 启动后台线程
    threading.Thread(target=background_status_updater, daemon=True).start()

    # 配置验证
    if not Config.validate():
        print("⚠️  配置验证失败")

    print("🚀🚀🚀🚀 迷你豆包后端服务启动成功")
    print("📡📡📡📡 服务地址: http://localhost:5000")
    print("🎨🎨🎨🎨 前端框架: Streamlit")
    print("🧠🧠🧠🧠 上下文记忆: 自然语言模式")
    print("🔧🔧🔧🔧 可用API端点:")
    print("   GET  /              - API信息")
    print("   GET  /api/models/status    - 获取模型状态")
    print("   GET  /health        - 健康检查")
    print("   GET  /api/debug/context - 调试对话历史")
    print("   POST /api/models/switch   - 切换模型偏好")
    print("   POST /api/stream-chat     - 流式聊天接口")
    print("   POST /api/context/clear   - 清空对话历史")

    app.run(host='0.0.0.0', port=5000, debug=False)