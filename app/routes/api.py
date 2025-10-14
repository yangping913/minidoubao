from flask import Blueprint, request, jsonify, Response, current_app
import json
import logging
import time
from functools import wraps

# 创建蓝图
api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """自定义API异常"""

    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


def error_handler(f):
    """统一错误处理装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API错误: {e.message}")
            return jsonify({
                "error": e.message,
                "error_code": e.error_code,
                "status": "error"
            }), e.status_code
        except Exception as e:
            logger.error(f"未处理异常: {str(e)}")
            return jsonify({
                "error": "内部服务器错误",
                "error_code": "INTERNAL_ERROR",
                "status": "error"
            }), 500

    return decorated_function


def validate_json(required_fields=None):
    """简化的JSON验证装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                raise APIError("请求必须为JSON格式", 400, "INVALID_JSON")

            data = request.get_json() or {}

            # 验证必需字段
            if required_fields:
                for field in required_fields:
                    if field not in data:
                        raise APIError(f"缺少必要参数: {field}", 400, "MISSING_FIELD")

            kwargs['validated_data'] = data
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@api_bp.route('/health', methods=['GET'])
@error_handler
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "success",
        "message": "服务运行正常",
        "timestamp": time.time()
    })


@api_bp.route('/chat', methods=['POST'])
@error_handler
@validate_json(['message'])
def chat(validated_data: dict):
    """聊天接口（非流式）"""
    message = validated_data['message'].strip()

    if not message:
        raise APIError("消息内容不能为空", 400, "EMPTY_MESSAGE")

    if len(message) > 2000:
        raise APIError("消息过长", 400, "MESSAGE_TOO_LONG")

    # 调用模型处理
    try:
        response = current_app.model_manager.chat(message)
        return jsonify({
            "status": "success",
            "response": response,
            "timestamp": time.time()
        })
    except Exception as e:
        logger.error(f"聊天处理失败: {str(e)}")
        raise APIError("处理消息时发生错误", 500, "PROCESSING_ERROR")


@api_bp.route('/chat/stream', methods=['POST'])
@error_handler
@validate_json(['message'])
def stream_chat(validated_data: dict):
    """流式聊天接口"""
    message = validated_data['message'].strip()

    if not message:
        raise APIError("消息内容不能为空", 400, "EMPTY_MESSAGE")

    if len(message) > 2000:
        raise APIError("消息过长", 400, "MESSAGE_TOO_LONG")

    def generate():
        """生成流式响应"""
        try:
            # 调用流式处理
            for chunk in current_app.model_manager.stream_chat(message):
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'timestamp': time.time()})}\n\n"

        except Exception as e:
            logger.error(f"流式处理失败: {str(e)}")
            error_data = json.dumps({
                "error": "流式处理失败",
                "error_code": "STREAM_ERROR",
                "done": True
            })
            yield f"data: {error_data}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@api_bp.route('/models', methods=['GET'])
@error_handler
def get_models():
    """获取可用模型列表"""
    models = current_app.model_manager.get_available_models()
    return jsonify({
        "status": "success",
        "models": models,
        "current_model": current_app.model_manager.current_model,
        "timestamp": time.time()
    })


@api_bp.route('/models/switch', methods=['POST'])
@error_handler
@validate_json(['model'])
def switch_model(validated_data: dict):
    """切换模型"""
    model_name = validated_data['model']

    success = current_app.model_manager.switch_model(model_name)
    if not success:
        available_models = current_app.model_manager.get_available_models()
        raise APIError(
            f"模型不存在，可用模型: {', '.join(available_models)}",
            400,
            "INVALID_MODEL"
        )

    return jsonify({
        "status": "success",
        "message": f"已切换到 {model_name}",
        "current_model": model_name,
        "timestamp": time.time()
    })


@api_bp.route('/context', methods=['GET'])
@error_handler
def get_context():
    """获取对话上下文"""
    context = current_app.context_manager.get_conversation_history()
    return jsonify({
        "status": "success",
        "context": context,
        "count": len(context),
        "timestamp": time.time()
    })


@api_bp.route('/context/clear', methods=['POST'])
@error_handler
def clear_context():
    """清空对话上下文"""
    current_app.context_manager.clear_history()
    return jsonify({
        "status": "success",
        "message": "对话历史已清空",
        "timestamp": time.time()
    })