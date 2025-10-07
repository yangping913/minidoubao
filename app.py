from flask import Flask, request, jsonify, Response, render_template
import time
import threading
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'minidoubao-secret-key')

# ===== 配置信息 =====
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '').strip()
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_NAME = os.getenv('OLLAMA_MODEL_NAME', 'qwen:0.5b').strip()  # 关键新增行


# ===== 跨域支持 =====
@app.after_request
def add_cors_headers(response):
    """添加CORS头信息"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response


# ===== 核心业务模块 =====
class ModelManager:
    """模型状态与偏好管理器"""

    def __init__(self):
        self.model_status = {'deepseek': False, 'ollama': False}
        self.preference = 'auto'
        self.request_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.is_processing = False

    def update_status(self):
        """更新模型状态"""
        with self.lock:
            # 检查DeepSeek状态
            try:
                if DEEPSEEK_API_KEY:
                    headers = {'Authorization': f'Bearer {DEEPSEEK_API_KEY}'}
                    response = requests.get(
                        "https://api.deepseek.com/v1/models",
                        headers=headers,
                        timeout=5
                    )
                    self.model_status['deepseek'] = response.status_code == 200
                else:
                    self.model_status['deepseek'] = False
            except:
                self.model_status['deepseek'] = False

            # 检查Ollama状态
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                self.model_status['ollama'] = response.status_code == 200
            except:
                self.model_status['ollama'] = False

            return self.model_status

    def get_status(self):
        """获取完整状态信息"""
        return {
            "deepseek": self.model_status['deepseek'],
            "ollama": self.model_status['ollama'],
            "preference": self.preference,
            "request_count": self.request_count,
            "uptime": int(time.time() - self.start_time)
        }

    def set_preference(self, model):
        """设置模型偏好"""
        if model in ['auto', 'deepseek', 'ollama']:
            self.preference = model
            return True
        return False

    def select_model(self):
        """智能选择当前活跃模型"""
        if self.preference == 'deepseek' and self.model_status['deepseek']:
            return 'deepseek'
        elif self.preference == 'ollama' and self.model_status['ollama']:
            return 'ollama'
        elif self.preference == 'auto':
            if self.model_status['deepseek']:
                return 'deepseek'
            elif self.model_status['ollama']:
                return 'ollama'
        return None

    def increment_count(self):
        """增加请求计数"""
        with self.lock:
            self.request_count += 1


class NaturalContextManager:
    """自然语言上下文管理器 - 完全无硬编码"""

    def __init__(self):
        self.conversation_history = []
        self.max_history = 10

    def add_message(self, role, content):
        """添加消息到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 保持历史记录长度
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def build_context_prompt(self, current_message):
        """构建上下文提示词 - 完全无硬编码"""
        # 基础系统提示
        system_prompt = """你是一个有帮助的AI助手。请根据完整的对话历史提供准确、连贯的回答。

对话指南：
1. 仔细阅读和理解整个对话历史
2. 如果用户提到过个人信息（如名字、地点、偏好等），请自然地使用这些信息
3. 保持回答与之前对话的一致性
4. 如果用户的问题需要上下文信息，请参考历史对话

当前对话历史："""

        # 添加对话历史（无关键词过滤）
        for i, msg in enumerate(self.conversation_history[-5:]):  # 最近5条消息
            system_prompt += f"\n{msg['role']}: {msg['content']}"

        system_prompt += f"\n\n当前用户消息: {current_message}"
        system_prompt += "\n\n请基于以上完整对话历史提供有帮助的回答。"

        return system_prompt

    def get_recent_messages(self, count=3):
        """获取最近的对话消息"""
        return self.conversation_history[-count:] if self.conversation_history else []


# ===== 全局初始化 =====
model_manager = ModelManager()
context_manager = NaturalContextManager()


# ===== 路由实现 =====
@app.route('/')
def index():
    """根路由 - 返回前端页面"""
    return render_template('index.html')


@app.route('/api/models/status', methods=['GET'])
def get_model_status():
    """获取模型状态"""
    model_manager.update_status()
    return jsonify(model_manager.get_status())


@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    """切换模型偏好"""
    data = request.get_json()
    if not data or 'model' not in data:
        return jsonify({"error": "缺少模型参数"}), 400

    model = data['model']
    if model_manager.set_preference(model):
        return jsonify({
            "status": "success",
            "preference": model,
            "message": f"已切换到{model}模式"
        })
    return jsonify({"error": "无效的模型选择"}), 400


@app.route('/api/stream-chat', methods=['POST'])
def stream_chat():
    """处理流式聊天请求 - 无硬编码版本"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "缺少消息内容"}), 400

    message = data['message'].strip()
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    if model_manager.is_processing:
        return jsonify({"error": "系统忙，请稍后重试"}), 429

    model_manager.is_processing = True
    model_manager.increment_count()

    # 添加用户消息到对话历史
    context_manager.add_message("user", message)

    def generate():
        """生成流式响应"""
        try:
            # 选择模型
            selected_model = model_manager.select_model()
            if not selected_model:
                yield f"data: {json.dumps({'error': '无可用模型'})}\n\n"
                return

            # 构建自然语言上下文提示
            context_prompt = context_manager.build_context_prompt(message)

            # 根据选择的模型调用API
            if selected_model == 'deepseek' and DEEPSEEK_API_KEY:
                # DeepSeek API调用 - 保持不变
                headers = {
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                }

                # 使用自然语言上下文提示
                messages = [{"role": "system", "content": context_prompt}]

                data = {
                    "model": "deepseek-chat",
                    "messages": messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }

                response = requests.post(
                    DEEPSEEK_API_URL,
                    json=data,
                    headers=headers,
                    stream=True,
                    timeout=30
                )

                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'API错误: {response.status_code}'})}\n\n"
                    return

                # 处理DeepSeek流式响应 - 保持不变
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data:'):
                            data_str = line_str[5:].strip()
                            if data_str == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and chunk['choices']:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_response += content
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue

                # 添加助手回复到对话历史
                if full_response.strip():
                    context_manager.add_message("assistant", full_response)

                yield "data: [DONE]\n\n"

            else:
                # Ollama模型处理 - 实现真正的流式响应
                context_prompt = context_manager.build_context_prompt(message)

                # 构建Ollama API请求
                # 修改后代码（读取配置，无硬编码）
                ollama_data = {
                    "model": OLLAMA_MODEL_NAME,  # 替换为配置变量，后续换模型改环境变量即可
                    "prompt": context_prompt + "\n\n用户消息: " + message,
                    "stream": True
                }

                try:
                    # 调用Ollama API
                    response = requests.post(
                        OLLAMA_API_URL,
                        json=ollama_data,
                        stream=True,
                        timeout=30
                    )

                    if response.status_code != 200:
                        yield f"data: {json.dumps({'error': f'Ollama API错误: {response.status_code}'})}\n\n"
                        return

                    # 处理Ollama流式响应
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if 'response' in chunk:
                                    content = chunk['response']
                                    if content:
                                        full_response += content
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue

                    # 添加助手回复到对话历史
                    if full_response.strip():
                        context_manager.add_message("assistant", full_response)

                    yield "data: [DONE]\n\n"

                except Exception as e:
                    yield f"data: {json.dumps({'error': f'Ollama请求失败: {str(e)}'})}\n\n"

        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        finally:
            model_manager.is_processing = False

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/debug/context', methods=['GET'])
def debug_context():
    """调试端点：查看当前对话历史"""
    return jsonify({
        "conversation_count": len(context_manager.conversation_history),
        "recent_messages": context_manager.get_recent_messages(5)
    })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "deepseek_configured": bool(DEEPSEEK_API_KEY),
        "conversation_count": len(context_manager.conversation_history)
    })


# ===== 后台任务 =====
def background_status_updater():
    """后台状态更新线程"""
    while True:
        time.sleep(30)
        model_manager.update_status()


# ===== 错误处理 =====
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "端点不存在"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "服务器内部错误"}), 500


# ===== 启动应用 =====
if __name__ == '__main__':
    # 启动后台线程
    threading.Thread(target=background_status_updater, daemon=True).start()

    # 配置验证
    if not DEEPSEEK_API_KEY:
        print("⚠️  警告: DEEPSEEK_API_KEY 环境变量未设置")
    elif len(DEEPSEEK_API_KEY) != 51:
        print("⚠️  警告: DeepSeek API密钥格式异常")
    else:
        print("✅ API密钥配置正常")

    print("🚀 迷你豆包后端服务启动成功")
    print("📡 服务地址: http://localhost:5000")
    print("🧠 上下文记忆: 自然语言模式（无硬编码）")
    print("🔧 可用API端点:")
    print("   GET  /              - 前端界面")
    print("   GET  /api/models/status    - 获取模型状态")
    print("   GET  /health        - 健康检查")
    print("   GET  /api/debug/context - 调试对话历史")
    print("   POST /api/models/switch   - 切换模型偏好")
    print("   POST /api/stream-chat     - 流式聊天接口")

    app.run(host='0.0.0.0', port=5000, debug=False)