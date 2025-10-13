#!/usr/bin/env python3
"""
前端启动脚本 - 确保正确设置Python路径
"""

import sys
import os
import subprocess


def main():
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(project_root, "frontend")

    # 切换到frontend目录
    os.chdir(frontend_dir)

    # 添加当前目录到Python路径
    sys.path.insert(0, frontend_dir)

    # 启动Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8501", "--server.address=0.0.0.0"
    ])


if __name__ == "__main__":
    main()