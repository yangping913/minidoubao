import os


class Config:
    """统一配置管理类"""

    # API配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '').strip()
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
    OLLAMA_MODEL_NAME = os.getenv('OLLAMA_MODEL_NAME', 'qwen:0.5b').strip()

    # 应用配置
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'minidoubao-secret-key')
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', '10'))
    STREAMLIT_FRONTEND_URL = os.getenv('STREAMLIT_FRONTEND_URL', 'http://localhost:8501')

    # 模型偏好默认值
    DEFAULT_MODEL_PREFERENCE = 'auto'

    @classmethod
    def validate(cls):
        """验证配置"""
        if cls.DEEPSEEK_API_KEY and len(cls.DEEPSEEK_API_KEY) != 51:
            print("⚠️  警告: DeepSeek API密钥格式异常")
            return False
        return True