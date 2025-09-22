# from flask import Flask, render_template, request, jsonify, session
# import requests
# import os
# import redis  # 新增：用于服务器端session存储
# from datetime import timedelta
#
# app = Flask(__name__)
#
# # ===== 关键修复1：使用固定密钥 =====
# # 从环境变量获取固定密钥（避免每次重启变化）
# app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_fixed_secret_key_here")
#
# # ===== 关键修复2：使用Redis存储session =====
# # 配置Redis存储session
# app.config.update({
#     'SESSION_TYPE': 'redis',
#     'SESSION_REDIS': redis.Redis(host='localhost', port=6379),
#     'SESSION_PERMANENT': True,
#     'PERMANENT_SESSION_LIFETIME': timedelta(days=1)
# })
#
# # 初始化Redis session（需要安装flask-session）
# from flask_session import Session
#
# Session(app)
#
# # ===== 其他配置保持不变 =====
# api_key = os.getenv("DEEPSEEK_API_KEY", "sk-292e49bc1acd4eb789c0ccb89e4cb562")
# api_url = "https://api.deepseek.com/v1/chat/completions"
#
#
# @app.route('/')
# def index():
#     session.permanent = True
#     # 确保history存在
#     if 'history' not in session:
#         session['history'] = []
#     return render_template('index.html')
#
#
# @app.route('/api/chat', methods=['POST'])
# def chat():
#     # 确保session已初始化
#     if 'history' not in session:
#         session['history'] = []
#
#     # 获取用户消息
#     user_message = request.json.get('message')
#
#     # 添加到历史记录
#     session['history'].append({"role": "user", "content": user_message})
#
#     # ===== 关键修复3：智能历史管理 =====
#     # 基于token数量管理历史记录
#     max_tokens = 3000  # 预留空间给新回复
#     current_tokens = sum(len(msg["content"]) for msg in session['history']) // 4  # 简单估算
#
#     # 如果token超限，移除最旧的消息
#     while current_tokens > max_tokens and len(session['history']) > 1:
#         removed = session['history'].pop(0)
#         removed_tokens = len(removed["content"]) // 4
#         current_tokens -= removed_tokens
#
#     # 准备API请求
#     headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
#     data = {
#         "model": "deepseek-chat",
#         "messages": session['history'],
#         "stream": False
#     }
#
#     try:
#         # 发送请求
#         response = requests.post(api_url, json=data, headers=headers)
#         response.raise_for_status()  # 检查HTTP错误
#
#         response_data = response.json()
#         ai_response = response_data['choices'][0]['message']['content']
#
#         # 将AI回复添加到历史记录
#         session['history'].append({"role": "assistant", "content": ai_response})
#
#         # 再次检查token数量
#         ai_tokens = len(ai_response) // 4
#         if current_tokens + ai_tokens > max_tokens * 1.1:  # 超过10%缓冲
#             # 移除最旧的一对对话（用户+AI）
#             if len(session['history']) > 2:
#                 session['history'] = session['history'][2:]
#
#         return jsonify({'response': ai_response})
#
#     except Exception as e:
#         print(f"API调用错误: {str(e)}")
#         # 出错时移除最后一条用户消息
#         if session['history'] and session['history'][-1]['role'] == 'user':
#             session['history'].pop()
#         return jsonify({'error': '抱歉，AI大脑开小差了...'}), 500
#
#
# @app.route('/api/clear_history', methods=['POST'])
# def clear_history():
#     session['history'] = []
#     return jsonify({'status': '历史记录已清除'})
#
#
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5001)
# from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
# import requests
# import os
# import redis
# import json
# from datetime import timedelta
#
# app = Flask(__name__)
#
# # ===== 关键修复1：使用固定密钥 =====
# app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_fixed_secret_key_here")
#
# # ===== 关键修复2：使用Redis存储session =====
# # 建议修改SESSION_REDIS配置，增加连接池和错误处理
# app.config.update({
#     'SESSION_TYPE': 'redis',
#     'SESSION_REDIS': redis.Redis(
#         host='localhost',
#         port=6379,
#         db=0,
#         socket_connect_timeout=5,  # 增加超时设置
#         retry_on_timeout=True     # 超时重试
#     ),
#     'SESSION_PERMANENT': True,
#     'PERMANENT_SESSION_LIFETIME': timedelta(days=1),
#     'SESSION_USE_SIGNER': True,   # 增加签名验证
# })
#
# # 初始化Redis session
# from flask_session import Session
#
# Session(app)
#
# # ===== 其他配置保持不变 =====
# api_key = os.getenv("DEEPSEEK_API_KEY", "sk-292e49bc1acd4eb789c0ccb89e4cb562")
# api_url = "https://api.deepseek.com/v1/chat/completions"
#
#
# @app.route('/')
# def index():
#     session.permanent = True
#     if 'history' not in session:
#         session['history'] = []
#     return render_template('index.html')
#
#
# @app.route('/api/chat', methods=['POST'])
# def chat():
#     # 确保session已初始化
#     if 'history' not in session:
#         session['history'] = []
#
#     # 获取用户消息
#     user_message = request.json.get('message')
#
#     # 添加到历史记录
#     session['history'].append({"role": "user", "content": user_message})
#
#     # ===== 关键修复3：智能历史管理 =====
#     max_tokens = 3000
#     current_tokens = sum(len(msg["content"]) for msg in session['history']) // 4
#
#     # 如果token超限，移除最旧的消息
#     while current_tokens > max_tokens and len(session['history']) > 1:
#         removed = session['history'].pop(0)
#         removed_tokens = len(removed["content"]) // 4
#         current_tokens -= removed_tokens
#
#     # 准备API请求
#     headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
#     data = {
#         "model": "deepseek-chat",
#         "messages": session['history'],
#         "stream": False
#     }
#
#     try:
#         # 发送请求
#         response = requests.post(api_url, json=data, headers=headers)
#         response.raise_for_status()
#
#         response_data = response.json()
#         ai_response = response_data['choices'][0]['message']['content']
#
#         # 将AI回复添加到历史记录
#         session['history'].append({"role": "assistant", "content": ai_response})
#
#         # 再次检查token数量
#         ai_tokens = len(ai_response) // 4
#         if current_tokens + ai_tokens > max_tokens * 1.1:
#             if len(session['history']) > 2:
#                 session['history'] = session['history'][2:]
#
#         return jsonify({'response': ai_response})
#
#     except Exception as e:
#         print(f"API调用错误: {str(e)}")
#         if session['history'] and session['history'][-1]['role'] == 'user':
#             session['history'].pop()
#         return jsonify({'error': '抱歉，AI大脑开小差了...'}), 500
#
#
# # ===== 新增：流式聊天接口 =====
# @app.route('/api/stream-chat', methods=['POST'])
# def stream_chat():
#     """流式聊天接口，支持实时输出"""
#     if 'history' not in session:
#         session['history'] = []
#
#     user_message = request.json.get('message')
#     session['history'].append({"role": "user", "content": user_message})
#
#     # 智能历史管理（与普通接口相同）
#     max_tokens = 3000
#     current_tokens = sum(len(msg["content"]) for msg in session['history']) // 4
#
#     while current_tokens > max_tokens and len(session['history']) > 1:
#         removed = session['history'].pop(0)
#         removed_tokens = len(removed["content"]) // 4
#         current_tokens -= removed_tokens
#
#     def generate():
#         headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
#         data = {
#             "model": "deepseek-chat",
#             "messages": session['history'],
#             "stream": True  # 启用流式
#         }
#
#         try:
#             full_response = ""
#             response = requests.post(api_url, json=data, headers=headers, stream=True)
#
#             for line in response.iter_lines():
#                 if line:
#                     line_text = line.decode('utf-8')
#                     if line_text.startswith('data:'):
#                         try:
#                             json_data = json.loads(line_text[5:])
#                             if (json_data.get('choices') and
#                                     len(json_data['choices']) > 0 and
#                                     'delta' in json_data['choices'][0] and
#                                     'content' in json_data['choices'][0]['delta']):
#                                 content = json_data['choices'][0]['delta']['content']
#                                 full_response += content
#                                 yield f"data: {json.dumps({'content': content})}\n\n"
#
#                         except json.JSONDecodeError:
#                             continue
#
#             # 流式完成后保存完整响应到session
#             session['history'].append({"role": "assistant", "content": full_response})
#
#             # 再次检查token数量
#             ai_tokens = len(full_response) // 4
#             if current_tokens + ai_tokens > max_tokens * 1.1:
#                 if len(session['history']) > 2:
#                     session['history'] = session['history'][2:]
#
#         except Exception as e:
#             print(f"流式API调用错误: {str(e)}")
#             yield f"data: {json.dumps({'error': '流式请求失败'})}\n\n"
#             if session['history'] and session['history'][-1]['role'] == 'user':
#                 session['history'].pop()
#
#     return Response(generate(), mimetype='text/event-stream')
#
#
# @app.route('/api/clear_history', methods=['POST'])
# def clear_history():
#     session['history'] = []
#     return jsonify({'status': '历史记录已清除'})
#
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5001)


from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
import requests
import os
import redis
import json
import logging
from datetime import timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DeepSeekChat')

app = Flask(__name__)

# 使用固定密钥
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_fixed_secret_key_here")

# 配置Redis存储session
app.config.update({
    'SESSION_TYPE': 'redis',
    'SESSION_REDIS': redis.Redis(host='localhost', port=6379, db=0),
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': timedelta(days=1)
})

# 初始化Redis session
from flask_session import Session

Session(app)

# API配置 - 使用已验证的API密钥
api_url = "https://api.deepseek.com/v1/chat/completions"


@app.route('/')
def index():
    session.permanent = True
    if 'history' not in session:
        session['history'] = []
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    if 'history' not in session:
        session['history'] = []

    user_message = request.json.get('message')
    logger.info(f"收到用户消息: {user_message}")
    session['history'].append({"role": "user", "content": user_message})

    # 智能历史管理
    max_tokens = 3000
    current_tokens = sum(len(msg["content"]) for msg in session['history']) // 4
    logger.debug(f"当前token数: {current_tokens}/{max_tokens}")

    # 如果token超限，移除最旧的消息
    while current_tokens > max_tokens and len(session['history']) > 1:
        removed = session['history'].pop(0)
        removed_tokens = len(removed["content"]) // 4
        current_tokens -= removed_tokens
        logger.debug(f"移除旧消息: {removed['content'][:20]}... (节省{removed_tokens} tokens)")

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = {
        "model": "deepseek-chat",
        "messages": session['history'],
        "stream": False,
        "max_tokens": 1000
    }

    try:
        logger.info("发送API请求...")
        response = requests.post(api_url, json=data, headers=headers, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        logger.debug(f"API响应: {response_data}")

        ai_response = response_data['choices'][0]['message']['content']
        logger.info(f"AI响应: {ai_response[:50]}...")

        session['history'].append({"role": "assistant", "content": ai_response})

        # 再次检查token数量
        ai_tokens = len(ai_response) // 4
        if current_tokens + ai_tokens > max_tokens * 1.1:
            if len(session['history']) > 2:
                logger.debug("清理历史记录")
                session['history'] = session['history'][2:]

        return jsonify({'response': ai_response})

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        error_msg = "API请求失败"
        if e.response.status_code == 401:
            error_msg = "API密钥无效"
        elif e.response.status_code == 429:
            error_msg = "请求过于频繁，请稍后再试"
        return jsonify({'error': error_msg}), e.response.status_code

    except requests.exceptions.Timeout:
        logger.error("API请求超时")
        return jsonify({'error': 'API请求超时，请稍后重试'}), 504

    except requests.exceptions.RequestException as e:
        logger.error(f"网络错误: {str(e)}")
        return jsonify({'error': '网络连接失败，请检查网络设置'}), 503

    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        return jsonify({'error': '系统内部错误'}), 500


@app.route('/api/stream-chat', methods=['POST'])
def stream_chat():
    if 'history' not in session:
        session['history'] = []

    user_message = request.json.get('message')
    logger.info(f"收到流式请求: {user_message}")
    session['history'].append({"role": "user", "content": user_message})

    max_tokens = 3000
    current_tokens = sum(len(msg["content"]) for msg in session['history']) // 4

    # 如果token超限，移除最旧的消息
    while current_tokens > max_tokens and len(session['history']) > 1:
        removed = session['history'].pop(0)
        removed_tokens = len(removed["content"]) // 4
        current_tokens -= removed_tokens

    # 使用stream_with_context包装生成器函数，保持请求上下文
    @stream_with_context
    def generate():
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        data = {
            "model": "deepseek-chat",
            "messages": session['history'],  # 现在可以安全访问session
            "stream": True,
            "max_tokens": 1000
        }

        full_response = ""

        try:
            logger.info("发送流式API请求...")
            with requests.post(api_url, json=data, headers=headers, stream=True, timeout=30) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data:'):
                            try:
                                json_data = json.loads(line_text[5:])
                                if (json_data.get('choices') and
                                        len(json_data['choices']) > 0 and
                                        'delta' in json_data['choices'][0] and
                                        'content' in json_data['choices'][0]['delta']):
                                    content = json_data['choices'][0]['delta']['content']
                                    full_response += content
                                    logger.debug(f"发送内容块: {content}")
                                    yield f"data: {json.dumps({'content': content})}\n\n"

                            except json.JSONDecodeError:
                                logger.warning("JSON解析错误")
                                continue

            logger.info(f"完整响应: {full_response[:50]}...")
            # 在请求上下文中更新session
            session['history'].append({"role": "assistant", "content": full_response})

            # 再次检查token数量
            ai_tokens = len(full_response) // 4
            if current_tokens + ai_tokens > max_tokens * 1.1:
                if len(session['history']) > 2:
                    session['history'] = session['history'][2:]

        except requests.exceptions.HTTPError as e:
            logger.error(f"流式HTTP错误: {e.response.status_code} - {e.response.text}")
            yield f"data: {json.dumps({'error': 'API请求失败'})}\n\n"

        except requests.exceptions.Timeout:
            logger.error("流式请求超时")
            yield f"data: {json.dumps({'error': '请求超时'})}\n\n"

        except requests.exceptions.RequestException as e:
            logger.error(f"流式网络错误: {str(e)}")
            yield f"data: {json.dumps({'error': '网络连接失败'})}\n\n"

        except Exception as e:
            logger.error(f"流式未知错误: {str(e)}")
            yield f"data: {json.dumps({'error': '系统内部错误'})}\n\n"

        finally:
            # 确保关闭流
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    logger.info("清除历史记录")
    session['history'] = []
    return jsonify({'status': '历史记录已清除'})


if __name__ == '__main__':
    # 设置详细日志级别
    logger.setLevel(logging.DEBUG)

    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)