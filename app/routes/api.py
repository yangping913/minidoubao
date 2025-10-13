from flask import Blueprint, request, jsonify, Response, current_app
import json
import logging

# 创建蓝图
api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


@api_bp.route('/models/status', methods=['GET'])
def get_model_status():
    """获取模型状态"""
    try:
        current_app.model_manager.update_status()
        return jsonify(current_app.model_manager.get_status())
    except Exception as e:
        logger.error(f"获取模型状态失败: {str(e)}")
        return jsonify({"error": "获取模型状态失败"}), 500


@api_bp.route('/models/switch', methods=['POST'])
def switch_model():
    """切换模型偏好"""
    try:
        data = request.get_json()
        if not data or 'model' not in data:
            return jsonify({"error": "缺少模型参数"}), 400

        model = data['model']
        if current_app.model_manager.set_preference(model):
            return jsonify({
                "status": "success",
                "preference": model,
                "message": f"已切换到{model}模式"
            })
        return jsonify({"error": "无效的模型选择"}), 400
    except Exception as e:
        logger.error(f"切换模型失败: {str(e)}")
        return jsonify({"error": "切换模型失败"}), 500


@api_bp.route('/stream-chat', methods=['POST'])
def stream_chat():
    """处理流式聊天请求"""
    # 验证请求数据
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体必须为JSON格式"}), 400

        if 'message' not in data:
            return jsonify({"error": "缺少消息内容"}), 400

        message = data['message'].strip()
        if not message:
            return jsonify({"error": "消息不能为空"}), 400
    except Exception as e:
        logger.error(f"请求数据解析失败: {str(e)}")
        return jsonify({"error": "请求数据格式错误"}), 400

    # 检查系统状态
    if getattr(current_app.model_manager, 'is_processing', False):
        return jsonify({"error": "系统忙，请稍后重试"}), 429

    # 初始化处理状态
    try:
        current_app.model_manager.is_processing = True
        current_app.model_manager.increment_count()
        current_app.context_manager.add_message("user", message)
    except Exception as e:
        current_app.model_manager.is_processing = False
        logger.error(f"初始化聊天状态失败: {str(e)}")
        return jsonify({"error": "系统初始化失败"}), 500

    def generate():
        """生成流式响应"""
        full_response = ""
        try:
            # 选择模型
            selected_model = current_app.model_manager.select_model()
            if not selected_model:
                error_data = json.dumps({"error": "无可用模型", "done": True})
                yield f"data: {error_data}\n\n"
                return

            # 构建上下文提示
            context_prompt = current_app.context_manager.build_context_prompt(message)

            # 获取模型提供商
            provider = current_app.model_manager.get_provider(selected_model)
            if not provider:
                error_data = json.dumps({"error": "模型提供商未找到", "done": True})
                yield f"data: {error_data}\n\n"
                return

            # 调用模型
            if selected_model == 'deepseek':
                messages = [{"role": "system", "content": context_prompt}]
                for response in provider.stream_chat(messages=messages):
                    yield response.to_sse_format()
                    if response.content and not response.done:
                        full_response += response.content
                    if response.done:
                        break  # 确保在完成后退出循环
            else:  # ollama
                for response in provider.stream_chat(prompt=context_prompt):
                    yield response.to_sse_format()
                    if response.content and not response.done:
                        full_response += response.content
                    if response.done:
                        break  # 确保在完成后退出循环

            # 添加助手回复到对话历史
            if full_response.strip():
                current_app.context_manager.add_message("assistant", full_response)

            # 发送完成信号
            done_data = json.dumps({"done": True})
            yield f"data: {done_data}\n\n"

        except Exception as e:
            logger.error(f"流式聊天处理失败: {str(e)}")
            error_data = json.dumps({"error": f"请求失败: {str(e)}", "done": True})
            yield f"data: {error_data}\n\n"
        finally:
            # 确保处理状态被重置
            try:
                current_app.model_manager.is_processing = False
                logger.info("处理状态已重置")
            except Exception as e:
                logger.error(f"重置处理状态失败: {str(e)}")

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
        }
    )


@api_bp.route('/debug/context', methods=['GET'])
def debug_context():
    """调试端点：查看当前对话历史"""
    try:
        return jsonify({
            "conversation_count": len(current_app.context_manager.conversation_history),
            "recent_messages": current_app.context_manager.get_recent_messages(5),
            "is_processing": getattr(current_app.model_manager, 'is_processing', False)
        })
    except Exception as e:
        logger.error(f"获取对话上下文失败: {str(e)}")
        return jsonify({"error": "获取对话上下文失败"}), 500


@api_bp.route('/context/clear', methods=['POST'])
def clear_context():
    """清空对话历史"""
    try:
        current_app.context_manager.clear_history()
        return jsonify({"status": "success", "message": "对话历史已清空"})
    except Exception as e:
        logger.error(f"清空对话历史失败: {str(e)}")
        return jsonify({"error": "清空对话历史失败"}), 500


@api_bp.route('/reset-processing', methods=['POST'])
def reset_processing():
    """强制重置处理状态（用于调试）"""
    try:
        was_processing = getattr(current_app.model_manager, 'is_processing', False)
        current_app.model_manager.is_processing = False
        return jsonify({
            "status": "success",
            "message": "处理状态已重置",
            "was_processing": was_processing
        })
    except Exception as e:
        logger.error(f"强制重置处理状态失败: {str(e)}")
        return jsonify({"error": "重置失败"}), 500