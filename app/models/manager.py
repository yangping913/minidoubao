import time
import threading
from app.config import Config
from app.models.deepseek import DeepSeekProvider
from app.models.ollama import OllamaProvider


class ModelManager:
    """模型状态与偏好管理器"""

    def __init__(self):
        self.model_status = {'deepseek': False, 'ollama': False}
        self.preference = Config.DEFAULT_MODEL_PREFERENCE
        self.request_count = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.is_processing = False

        # 初始化模型提供商
        self.providers = {
            'deepseek': DeepSeekProvider(),
            'ollama': OllamaProvider()
        }

    def update_status(self):
        """更新模型状态"""
        with self.lock:
            for name, provider in self.providers.items():
                self.model_status[name] = provider.is_available()
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

    def get_provider(self, name):
        """获取指定的模型提供商"""
        return self.providers.get(name)