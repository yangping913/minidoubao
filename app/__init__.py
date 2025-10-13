from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.models.manager import ModelManager
from app.context.manager import NaturalContextManager


def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    CORS(app)
    app.secret_key = Config.FLASK_SECRET_KEY

    # 全局初始化
    app.model_manager = ModelManager()
    app.context_manager = NaturalContextManager()

    # 注册路由
    from app.routes.api import api_bp
    from app.routes.health import health_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(health_bp)

    return app