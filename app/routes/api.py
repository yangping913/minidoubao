from flask import Blueprint, request, jsonify, Response, current_app
import json
import threading
import queue

# 创建蓝图
api_bp = Blueprint('api', __name__)


@api_bp.route('/')
def api_root():
    """API根端点 - 返回服务信息"""
    return jsonify({
        "service": "MiniDoubao Backend API",
        "version": "1.0.0",
        "frontend": "Streamlit",
        "endpoints": {
            "GET /api/models/status": "获取模型状态",
            "POST /api/models/switch": "切换模型偏好",
            "POST /api/stream-chat": "流式聊天接口",
            "GET /api/debug/context": "调试对话历史",
            "GET /health": "健康检查"
        }
    })


@api_bp.route('/models/status', methods=['GET'])
def get_model_status():
    """获取模型状态"""
    app = current_app._get_current_object()
    app.model_manager.update_status()
    return jsonify(app.model_manager.get_status())


@api_bp.route('/models/switch', methods=['POST'])
def switch_model():
    """切换模型偏好"""
    app = current_app._get_current_object()
    data = request.get_json()
    if not data or 'model' not in data:
        return jsonify({"error": "缺少模型参数"}), 400

    model = data['model']
    if app.model_manager.set_preference(model):
        return jsonify({
            "status": "success",
            "preference": model,
            "message": f"已切换到{model}模式"
        })
    return jsonify({"error": "无效的模型选择"}), 400


@api_bp.route('/stream-chat', methods=['POST'])
def stream_chat():
    """处理流式聊天请求"""
    app = current_app._get_current_object()

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "缺少消息内容"}), 400

    message = data['message'].strip()
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    if app.model_manager.is_processing:
        return jsonify({"error": "系统忙，请稍后重试"}), 429

    # 预先获取所有需要的数据，避免在生成器中访问应用上下文
    selected_model = app.model_manager.select_model()
    if not selected_model:
        return jsonify({"error": "无可用模型"}), 500

    context_prompt = app.context_manager.build_context_prompt(message)
    provider = app.model_manager.get_provider(selected_model)

    if not provider:
        return jsonify({"error": "模型提供商未找到"}), 500

    # 使用队列在线程间传递数据
    response_queue = queue.Queue()

    def process_chat():
        """在单独线程中处理聊天请求"""
        try:
            app.model_manager.is_processing = True
            app.model_manager.increment_count()

            # 添加用户消息到对话历史
            app.context_manager.add_message("user", message)

            full_response = ""

            # 调用模型
            if selected_model == 'deepseek':
                messages = [{"role": "system", "content": context_prompt}]
                for response in provider.stream_chat(messages=messages):
                    response_queue.put(response)
                    if response.content and not response.done:
                        full_response += response.content
            else:  # ollama
                for response in provider.stream_chat(prompt=context_prompt):
                    response_queue.put(response)
                    if response.content and not response.done:
                        full_response += response.content

            # 添加助手回复到对话历史
            if full_response.strip():
                app.context_manager.add_message("assistant", full_response)

            # 发送结束信号
            response_queue.put(None)

        except Exception as e:
            response_queue.put({"error": f"请求失败: {str(e)}"})
        finally:
            app.model_manager.is_processing = False

    def generate():
        """生成流式响应"""
        # 启动处理线程
        thread = threading.Thread(target=process_chat)
        thread.daemon = True
        thread.start()

        while True:
            try:
                # 从队列获取响应，设置超时避免永久阻塞
                item = response_queue.get(timeout=30)

                if item is None:  # 结束信号
                    break
                elif isinstance(item, dict) and 'error' in item:
                    yield f"data: {json.dumps(item)}\n\n"
                    break
                else:
                    yield item.to_sse_format()

            except queue.Empty:
                yield f"data: {json.dumps({'error': '响应超时'})}\n\n"
                break
            except Exception as e:
                yield f"data: {json.dumps({'error': f'生成响应时出错: {str(e)}'})}\n\n"
                break

    return Response(generate(), mimetype='text/event-stream')


@api_bp.route('/debug/context', methods=['GET'])
def debug_context():
    """调试端点：查看当前对话历史"""
    app = current_app._get_current_object()
    return jsonify({
        "conversation_count": len(app.context_manager.conversation_history),
        "recent_messages": app.context_manager.get_recent_messages(5)
    })


@api_bp.route('/context/clear', methods=['POST'])
def clear_context():
    """清空对话历史"""
    app = current_app._get_current_object()
    app.context_manager.clear_history()
    return jsonify({"status": "success", "message": "对话历史已清空"})