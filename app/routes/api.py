from flask import Blueprint, request, jsonify, Response
import json
from app import create_app

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 获取应用实例以访问全局对象
app = create_app()

@api_bp.route('/models/status', methods=['GET'])
def get_model_status():
    """获取模型状态"""
    app.model_manager.update_status()
    return jsonify(app.model_manager.get_status())

@api_bp.route('/models/switch', methods=['POST'])
def switch_model():
    """切换模型偏好"""
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
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "缺少消息内容"}), 400

    message = data['message'].strip()
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    if app.model_manager.is_processing:
        return jsonify({"error": "系统忙，请稍后重试"}), 429

    app.model_manager.is_processing = True
    app.model_manager.increment_count()

    # 添加用户消息到对话历史
    app.context_manager.add_message("user", message)

    def generate():
        """生成流式响应"""
        try:
            # 选择模型
            selected_model = app.model_manager.select_model()
            if not selected_model:
                yield f"data: {json.dumps({'error': '无可用模型'})}\n\n"
                return

            # 构建自然语言上下文提示
            context_prompt = app.context_manager.build_context_prompt(message)

            # 获取模型提供商
            provider = app.model_manager.get_provider(selected_model)
            if not provider:
                yield f"data: {json.dumps({'error': '模型提供商未找到'})}\n\n"
                return

            # 调用模型
            full_response = ""
            if selected_model == 'deepseek':
                messages = [{"role": "system", "content": context_prompt}]
                for response in provider.stream_chat(messages=messages):
                    yield response.to_sse_format()
                    if response.content and not response.done:
                        full_response += response.content
            else:  # ollama
                for response in provider.stream_chat(prompt=context_prompt):
                    yield response.to_sse_format()
                    if response.content and not response.done:
                        full_response += response.content

            # 添加助手回复到对话历史
            if full_response.strip():
                app.context_manager.add_message("assistant", full_response)

        except Exception as e:
            error_msg = f"请求失败: {str(e)}"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        finally:
            app.model_manager.is_processing = False

    return Response(generate(), mimetype='text/event-stream')

@api_bp.route('/debug/context', methods=['GET'])
def debug_context():
    """调试端点：查看当前对话历史"""
    return jsonify({
        "conversation_count": len(app.context_manager.conversation_history),
        "recent_messages": app.context_manager.get_recent_messages(5)
    })

@api_bp.route('/context/clear', methods=['POST'])
def clear_context():
    """清空对话历史"""
    app.context_manager.clear_history()
    return jsonify({"status": "success", "message": "对话历史已清空"})