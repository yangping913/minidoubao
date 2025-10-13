# # minidoubao_streamlit.py
# import streamlit as st
# import requests
# import json
# import time
# import os
#
# # 直接从环境变量获取后端地址
# FLASK_BACKEND_URL = os.getenv("FLASK_BACKEND_URL", "http://localhost:5000")
#
# # 页面设置
# st.set_page_config(
#     page_title="迷你豆包 AI 助手",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )
#
# # 初始化会话状态
# if "messages" not in st.session_state:
#     st.session_state.messages = []
#
# if "model_status" not in st.session_state:
#     st.session_state.model_status = {
#         "deepseek": False,
#         "ollama": False,
#         "preference": "auto",
#         "request_count": 0,
#         "uptime": 0
#     }
#
# if "processing" not in st.session_state:
#     st.session_state.processing = False
#
# if "last_model_check" not in st.session_state:
#     st.session_state.last_model_check = 0
#
#
# # 工具函数
# def get_model_status(force=False):
#     """获取模型状态，带缓存机制"""
#     current_time = time.time()
#     # 5秒缓存，避免频繁请求
#     if not force and current_time - st.session_state.last_model_check < 5:
#         return True
#
#     try:
#         response = requests.get(f"{FLASK_BACKEND_URL}/api/models/status", timeout=5)
#         if response.status_code == 200:
#             new_status = response.json()
#             st.session_state.model_status = new_status
#             st.session_state.last_model_check = current_time
#             return True
#     except Exception as e:
#         st.error(f"获取模型状态失败: {str(e)}")
#     return False
#
#
# def switch_model_preference(model):
#     """切换模型偏好"""
#     try:
#         response = requests.post(
#             f"{FLASK_BACKEND_URL}/api/models/switch",
#             json={"model": model},
#             timeout=5
#         )
#         if response.status_code == 200:
#             result = response.json()
#             # 强制刷新模型状态
#             get_model_status(force=True)
#             st.success(f"已切换到 {model} 模式")
#             return True
#         else:
#             st.error(f"切换失败: {response.json().get('error', '未知错误')}")
#     except Exception as e:
#         st.error(f"切换模型失败: {str(e)}")
#     return False
#
#
# def clear_conversation():
#     """清空对话历史"""
#     try:
#         response = requests.post(f"{FLASK_BACKEND_URL}/api/context/clear", timeout=5)
#         if response.status_code == 200:
#             st.session_state.messages = []
#             st.success("对话历史已清空")
#             return True
#     except Exception as e:
#         st.error(f"清空对话失败: {str(e)}")
#     return False
#
#
# def send_message(message):
#     """发送消息到后端并处理流式响应"""
#     st.session_state.processing = True
#
#     try:
#         # 准备请求
#         response = requests.post(
#             f"{FLASK_BACKEND_URL}/api/stream-chat",
#             json={"message": message},
#             stream=True,
#             timeout=30
#         )
#
#         # 检查响应状态
#         if response.status_code != 200:
#             st.error(f"请求失败: HTTP {response.status_code}")
#             st.session_state.processing = False
#             return
#
#         # 添加用户消息到界面
#         st.session_state.messages.append({"role": "user", "content": message})
#
#         # 创建占位符用于流式显示
#         assistant_placeholder = st.empty()
#         full_response = ""
#
#         # 处理流式响应
#         for line in response.iter_lines():
#             if line:
#                 line_str = line.decode('utf-8')
#                 if line_str.startswith('data:'):
#                     data_str = line_str[5:].strip()
#                     if data_str == '[DONE]':
#                         break
#
#                     try:
#                         data = json.loads(data_str)
#                         if 'content' in data:
#                             full_response += data['content']
#                             assistant_placeholder.markdown(full_response + "▌")
#                         elif 'error' in data:
#                             st.error(f"API错误: {data['error']}")
#                             break
#                     except json.JSONDecodeError:
#                         continue
#
#         # 更新最终响应
#         if full_response:
#             assistant_placeholder.markdown(full_response)
#             st.session_state.messages.append({"role": "assistant", "content": full_response})
#
#         # 刷新模型状态
#         get_model_status(force=True)
#
#     except Exception as e:
#         st.error(f"请求失败: {str(e)}")
#     finally:
#         st.session_state.processing = False
#
#
# # 侧边栏 - 模型状态和控制
# with st.sidebar:
#     st.title("控制面板")
#     st.divider()
#
#     # 模型状态
#     st.subheader("模型状态")
#     if st.button("刷新状态", use_container_width=True):
#         get_model_status(force=True)
#
#     col1, col2 = st.columns(2)
#     with col1:
#         deepseek_status = "🟢 在线" if st.session_state.model_status.get("deepseek") else "🔴 离线"
#         st.metric("DeepSeek", deepseek_status)
#     with col2:
#         ollama_status = "🟢 在线" if st.session_state.model_status.get("ollama") else "🔴 离线"
#         st.metric("Ollama", ollama_status)
#
#     st.metric("请求次数", st.session_state.model_status.get("request_count", 0))
#     uptime = st.session_state.model_status.get('uptime', 0)
#     st.metric("运行时间", f"{uptime}秒")
#
#     # 显示当前选择的模型
#     current_model = st.session_state.model_status.get("preference", "auto")
#     st.info(f"当前模式: {current_model}")
#
#     # 模型选择
#     st.divider()
#     st.subheader("模型选择")
#
#     # 使用单选按钮选择模型
#     model_options = ["auto", "deepseek", "ollama"]
#     selected_model = st.radio(
#         "选择模型",
#         options=model_options,
#         index=model_options.index(current_model) if current_model in model_options else 0,
#         help="auto: 自动选择可用模型\ndeepseek: 优先使用DeepSeek\nollama: 优先使用Ollama"
#     )
#
#     # 只有当选择的模型与当前模型不同时才显示切换按钮
#     if selected_model != current_model:
#         if st.button("应用选择", use_container_width=True):
#             if switch_model_preference(selected_model):
#                 # 成功切换后，重新运行以更新界面
#                 st.rerun()
#
#     # 其他控制
#     st.divider()
#     st.subheader("其他选项")
#     if st.button("清空对话", use_container_width=True, type="secondary"):
#         clear_conversation()
#
#     if st.button("调试信息", use_container_width=True, type="secondary"):
#         try:
#             response = requests.get(f"{FLASK_BACKEND_URL}/api/debug/context", timeout=5)
#             if response.status_code == 200:
#                 debug_info = response.json()
#                 st.write("调试信息:", debug_info)
#         except Exception as e:
#             st.error(f"获取调试信息失败: {str(e)}")
#
# # 主界面 - 聊天区域
# st.title("迷你豆包 AI 助手")
# st.caption("基于 Flask + Streamlit 的智能聊天助手")
#
# # 显示聊天消息
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#
# # 用户输入
# if prompt := st.chat_input("请输入您的问题...", disabled=st.session_state.processing):
#     send_message(prompt)
#
# # 底部状态栏
# st.divider()
# status_text = "就绪"
# if st.session_state.processing:
#     status_text = "正在处理请求..."
#
# col1, col2, col3 = st.columns([1, 1, 2])
# with col1:
#     st.caption(f"状态: {status_text}")
# with col2:
#     st.caption(f"模式: {st.session_state.model_status.get('preference', 'auto')}")
# with col3:
#     st.caption(f"后端: {FLASK_BACKEND_URL}")
#
# # 初始加载时获取模型状态
# if not st.session_state.model_status.get("request_count", 0) > 0:
#     get_model_status(force=True)