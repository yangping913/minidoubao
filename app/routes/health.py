from flask import Blueprint, jsonify, current_app
import logging
import time
import os

# 创建蓝图
health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """综合健康检查"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }

    # 检查模型管理器
    try:
        model_status = "healthy"
        if not hasattr(current_app, 'model_manager'):
            model_status = "unavailable"
        elif not current_app.model_manager.get_available_models():
            model_status = "degraded"

        health_status["services"]["model_manager"] = model_status
    except Exception as e:
        logger.error(f"模型管理器检查失败: {str(e)}")
        health_status["services"]["model_manager"] = "error"

    # 检查上下文管理器
    try:
        context_status = "healthy"
        if not hasattr(current_app, 'context_manager'):
            context_status = "unavailable"

        health_status["services"]["context_manager"] = context_status
    except Exception as e:
        logger.error(f"上下文管理器检查失败: {str(e)}")
        health_status["services"]["context_manager"] = "error"

    # 检查系统资源（简化版，不使用psutil）
    try:
        # 检查磁盘空间（使用os模块）
        disk_info = os.statvfs('/') if hasattr(os, 'statvfs') else None
        if disk_info:
            total_space = disk_info.f_frsize * disk_info.f_blocks
            free_space = disk_info.f_frsize * disk_info.f_bavail
            disk_usage_percent = 100 - (free_space / total_space * 100)

            health_status["system"] = {
                "disk_usage_percent": round(disk_usage_percent, 2)
            }

            # 如果磁盘使用率过高，标记为降级
            if disk_usage_percent > 90:
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"系统资源检查失败: {str(e)}")
        health_status["system"] = {"error": str(e)}

    # 如果有任何服务不可用，标记为不健康
    if "unavailable" in health_status["services"].values() or "error" in health_status["services"].values():
        health_status["status"] = "unhealthy"

    # 设置HTTP状态码
    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 206

    return jsonify(health_status), status_code


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """就绪检查（简化版）"""
    try:
        # 检查关键服务是否就绪
        critical_services = {
            "model_manager": hasattr(current_app, 'model_manager') and current_app.model_manager is not None,
            "context_manager": hasattr(current_app, 'context_manager') and current_app.context_manager is not None
        }

        all_ready = all(critical_services.values())

        response = {
            "status": "ready" if all_ready else "not_ready",
            "timestamp": time.time(),
            "services": critical_services
        }

        return jsonify(response), 200 if all_ready else 503

    except Exception as e:
        logger.error(f"就绪检查失败: {str(e)}")
        return jsonify({
            "status": "not_ready",
            "error": str(e),
            "timestamp": time.time()
        }), 503


@health_bp.route('/info', methods=['GET'])
def system_info():
    """系统信息"""
    info = {
        "name": "AI Chat API",
        "version": "1.0.0",
        "timestamp": time.time(),
        "features": ["chat", "stream_chat", "model_management", "context_management"]
    }

    # 添加模型信息
    if hasattr(current_app, 'model_manager'):
        try:
            info["models"] = current_app.model_manager.get_available_models()
            info["current_model"] = current_app.model_manager.current_model
        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            info["models_error"] = str(e)

    return jsonify(info)


@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """基础监控指标"""
    metrics_data = {
        "timestamp": time.time(),
        "application": {}
    }

    # 应用指标
    if hasattr(current_app, 'context_manager'):
        metrics_data["application"]["conversation_count"] = len(
            current_app.context_manager.get_conversation_history()
        )

    if hasattr(current_app, 'model_manager'):
        metrics_data["application"]["current_model"] = getattr(
            current_app.model_manager, 'current_model', 'unknown'
        )
        metrics_data["application"]["request_count"] = getattr(
            current_app.model_manager, 'request_count', 0
        )

    # 系统指标（简化版）
    try:
        # 使用os模块获取基本信息
        metrics_data["system"] = {
            "current_working_directory": os.getcwd(),
            "process_id": os.getpid()
        }
    except Exception as e:
        metrics_data["system_error"] = str(e)

    return jsonify(metrics_data)