# import json
# import faiss
# import numpy as np
# from datetime import datetime
# from dateparser import parse
# from sentence_transformers import SentenceTransformer
# from sklearn.cluster import KMeans
# import requests
# from typing import List, Dict, Any
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# class UniversalMemorySystem:
#     def __init__(self):
#         self.memory_store = []
#         self.memory_embeddings = None
#         self.index = None
#         self.last_accessed = {}
#
#         # Ollama 配置
#         self.ollama_url = "http://localhost:11434/api"
#         self.ollama_embedding_model = "nomic-embed-text"  # 推荐用于嵌入的模型
#         self.ollama_chat_model = "llama2"  # 默认聊天模型
#         self.ollama_timeout = 10  # 请求超时时间
#
#         # 初始化嵌入模型
#         try:
#             # 使用清华镜像源加载模型
#             self.model = SentenceTransformer(
#                 'paraphrase-multilingual-MiniLM-L12-v2',
#                 cache_folder='./models',
#                 mirror='https://mirrors.tuna.tsinghua.edu.cn/huggingface-models'
#             )
#             logger.info("✅  SentenceTransformer 模型加载成功")
#         except Exception as e:
#             logger.error(f"❌  SentenceTransformer 模型加载失败: {e}")
#             # 使用备用模型
#             try:
#                 self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
#                 logger.info("✅  使用备用嵌入模型")
#             except Exception as e2:
#                 logger.error(f"❌  备用模型也加载失败: {e2}")
#                 self.model = None
#
#     def add_memory(self, content, source="user", timestamp=None, importance=1.0):
#         """添加新记忆到记忆系统
#
#         Args:
#             content (str): 记忆内容
#             source (str): 记忆来源，默认为"user"
#             timestamp (str): 时间戳，默认为当前时间
#             importance (float): 记忆重要性权重，范围0.1-3.0
#
#         Returns:
#             dict: 添加的记忆对象
#         """
#         if not timestamp:
#             timestamp = datetime.now().isoformat()
#
#         memory = {
#             "id": len(self.memory_store),
#             "content": content,
#             "source": source,
#             "timestamp": timestamp,
#             "last_accessed": timestamp,
#             "access_count": 0,
#             "importance": max(0.1, min(3.0, importance)),  # 限制重要性范围
#             "cluster": -1,
#             "embedding_type": "unknown"  # 标记嵌入生成方式
#         }
#
#         self.memory_store.append(memory)
#         self._update_index(memory)
#         return memory
#
#     def _update_index(self, memory):
#         """更新FAISS索引，优先使用Ollama生成嵌入
#
#         Args:
#             memory (dict): 要索引的记忆对象
#         """
#         try:
#             # 优先尝试使用Ollama生成嵌入
#             embedding = None
#             if self._check_ollama_available():
#                 embeddings = self.ollama_embed([memory["content"]])
#                 if embeddings and embeddings[0]:
#                     embedding = embeddings[0]
#                     memory["embedding_type"] = "ollama"
#                     logger.info("✅  使用Ollama生成嵌入")
#
#             # 如果Ollama不可用或失败，使用原模型
#             if embedding is None and self.model:
#                 embedding = self.model.encode([memory["content"]])[0]
#                 memory["embedding_type"] = "sentence_transformer"
#                 logger.info("✅  使用SentenceTransformer生成嵌入")
#
#             # 如果都失败，使用降级方案
#             if embedding is None:
#                 embedding = self._fallback_embedding(memory["content"])
#                 memory["embedding_type"] = "fallback"
#                 logger.warning("⚠️  使用降级嵌入方案")
#
#             # 更新索引
#             if self.memory_embeddings is None:
#                 self.memory_embeddings = np.array([embedding])
#                 self.index = faiss.IndexFlatL2(embedding.shape[0])
#                 self.index.add(self.memory_embeddings.astype('float32'))
#             else:
#                 new_embedding = np.array([embedding]).astype('float32')
#                 self.memory_embeddings = np.vstack([self.memory_embeddings, embedding])
#                 self.index.add(new_embedding)
#
#         except Exception as e:
#             logger.error(f"❌  更新索引失败: {e}")
#
#     def get_ollama_models(self) -> List[str]:
#         """获取本地可用的Ollama模型列表
#
#         Returns:
#             List[str]: 可用的模型名称列表
#         """
#         try:
#             response = requests.get(
#                 f"{self.ollama_url}/tags",
#                 timeout=self.ollama_timeout
#             )
#             if response.status_code == 200:
#                 models = [model['name'] for model in response.json().get('models', [])]
#                 logger.info(f"✅  获取到 {len(models)} 个Ollama模型")
#                 return models
#             return []
#         except requests.exceptions.RequestException as e:
#             logger.warning(f"⚠️  获取Ollama模型列表失败: {e}")
#             return []
#         except Exception as e:
#             logger.error(f"❌  获取Ollama模型列表异常: {e}")
#             return []
#
#     def _check_ollama_available(self) -> bool:
#         """检查Ollama服务是否可用
#
#         Returns:
#             bool: Ollama服务是否可用
#         """
#         try:
#             response = requests.get(
#                 f"{self.ollama_url}/tags",
#                 timeout=3
#             )
#             return response.status_code == 200
#         except:
#             return False
#
#     def ollama_embed(self, texts: List[str]) -> List[List[float]]:
#         """使用Ollama生成嵌入向量
#
#         Args:
#             texts (List[str]): 要嵌入的文本列表
#
#         Returns:
#             List[List[float]]: 嵌入向量列表
#         """
#         if not self._check_ollama_available():
#             logger.warning("⚠️  Ollama服务不可用")
#             return []
#
#         embeddings = []
#         for text in texts:
#             try:
#                 data = {
#                     "model": self.ollama_embedding_model,
#                     "prompt": text
#                 }
#                 response = requests.post(
#                     f"{self.ollama_url}/embeddings",
#                     json=data,
#                     timeout=self.ollama_timeout
#                 )
#
#                 if response.status_code == 200:
#                     embedding_data = response.json()
#                     embedding = embedding_data.get('embedding', [])
#                     if embedding:
#                         embeddings.append(embedding)
#                     else:
#                         logger.warning("⚠️  Ollama返回空嵌入")
#                         embeddings.append(self._fallback_embedding(text))
#                 else:
#                     logger.warning(f"⚠️  Ollama嵌入请求失败: {response.status_code}")
#                     embeddings.append(self._fallback_embedding(text))
#
#             except requests.exceptions.Timeout:
#                 logger.warning("⚠️  Ollama嵌入请求超时")
#                 embeddings.append(self._fallback_embedding(text))
#             except requests.exceptions.RequestException as e:
#                 logger.warning(f"⚠️  Ollama网络错误: {e}")
#                 embeddings.append(self._fallback_embedding(text))
#             except Exception as e:
#                 logger.error(f"❌  Ollama嵌入异常: {e}")
#                 embeddings.append(self._fallback_embedding(text))
#
#         return embeddings
#
#     def _fallback_embedding(self, text: str) -> List[float]:
#         """简单的降级嵌入方案
#
#         Args:
#             text (str): 输入文本
#
#         Returns:
#             List[float]: 降级嵌入向量
#         """
#         # 基于文本长度和字符分布的简单嵌入
#         text_length = len(text)
#         word_count = len(text.split())
#         char_diversity = len(set(text)) / max(1, len(text))
#
#         # 生成384维的嵌入（与常见嵌入维度匹配）
#         embedding = []
#         np.random.seed(hash(text) % 10000)  # 基于文本内容的确定性随机
#
#         # 前10维基于文本特征
#         embedding.append(text_length / 1000.0)  # 归一化长度
#         embedding.append(word_count / 200.0)  # 归一化词数
#         embedding.append(char_diversity)  # 字符多样性
#         embedding.append(sum(1 for c in text if c.isdigit()) / max(1, text_length))  # 数字比例
#         embedding.append(sum(1 for c in text if c.isalpha()) / max(1, text_length))  # 字母比例
#
#         # 剩余维度使用随机值（但保持确定性）
#         for i in range(379):
#             embedding.append(np.random.uniform(-0.1, 0.1))
#
#         return embedding
#
#     def should_use_local_model(self, query: str) -> bool:
#         """判断是否应该使用本地模型处理查询
#
#         Args:
#             query (str): 用户查询内容
#
#         Returns:
#             bool: 是否推荐使用本地模型
#         """
#         if not query or not isinstance(query, str):
#             return False
#
#         query_lower = query.lower()
#         query_length = len(query)
#
#         # 定义关键词规则
#         local_keywords = ["你好", "请问", "介绍", "解释", "什么是", "怎么样",
#                           "告诉我", "建议", "推荐", "如何", "怎样", "能不能"]
#         remote_keywords = ["最新", "2024", "2025", "新闻", "更新", "最近",
#                            "实时", "当前", "现在", "今天", "本周", "本月"]
#
#         complex_keywords = ["代码", "编程", "算法", "数学", "计算", "理论",
#                             "研究", "分析", "比较", "评估", "总结", "论述"]
#
#         # 包含远程关键词则使用DeepSeek（需要最新知识）
#         for keyword in remote_keywords:
#             if keyword in query_lower:
#                 logger.info(f"🔍  检测到远程关键词 '{keyword}'，推荐使用DeepSeek")
#                 return False
#
#         # 非常短的查询优先使用本地
#         if query_length < 10:
#             logger.info("🔍  短查询，推荐使用本地模型")
#             return True
#
#         # 中等长度查询（10-50字符）根据关键词判断
#         if 10 <= query_length <= 50:
#             for keyword in local_keywords:
#                 if keyword in query_lower:
#                     logger.info(f"🔍  检测到本地关键词 '{keyword}'，推荐使用本地模型")
#                     return True
#
#             for keyword in complex_keywords:
#                 if keyword in query_lower:
#                     logger.info(f"🔍  检测到复杂关键词 '{keyword}'，推荐使用DeepSeek")
#                     return False
#
#         # 长查询（>50字符）通常需要更强的模型
#         if query_length > 50:
#             logger.info("🔍  长查询，推荐使用DeepSeek")
#             return False
#
#         # 默认使用本地模型（节省API调用）
#         logger.info("🔍  默认推荐使用本地模型")
#         return True
#
#     def retrieve_memories(self, query, top_k=5, recency_weight=0.3, importance_weight=0.5):
#         """检索相关记忆，支持多种权重平衡
#
#         Args:
#             query (str): 查询文本
#             top_k (int): 返回最多记忆数量
#             recency_weight (float): 时效性权重
#             importance_weight (float): 重要性权重
#
#         Returns:
#             List[dict]: 相关记忆列表，按相关性排序
#         """
#         if not self.memory_store or not query:
#             return []
#
#         # 确保权重总和不超过1.0
#         similarity_weight = 1.0 - recency_weight - importance_weight
#         if similarity_weight < 0:
#             similarity_weight = 0.5
#             recency_weight = 0.25
#             importance_weight = 0.25
#             logger.warning("⚠️  权重调整，使用默认权重配置")
#
#         try:
#             # 生成查询嵌入（优先使用Ollama）
#             query_embedding = None
#             if self._check_ollama_available():
#                 ollama_embeddings = self.ollama_embed([query])
#                 if ollama_embeddings and ollama_embeddings[0]:
#                     query_embedding = ollama_embeddings[0]
#
#             if query_embedding is None and self.model:
#                 query_embedding = self.model.encode([query])[0]
#
#             if query_embedding is None:
#                 query_embedding = self._fallback_embedding(query)
#
#             # 搜索相似记忆
#             distances, indices = self.index.search(
#                 np.array([query_embedding]).astype('float32'),
#                 min(top_k * 2, len(self.memory_store))  # 多检索一些用于后续筛选
#             )
#
#             # 计算综合分数
#             results = []
#             for i, idx in enumerate(indices[0]):
#                 if idx < len(self.memory_store):
#                     memory = self.memory_store[idx].copy()
#
#                     # 计算时效性分数
#                     try:
#                         last_accessed_dt = parse(memory["last_accessed"])
#                         if isinstance(last_accessed_dt, datetime):
#                             days_since_access = (datetime.now() - last_accessed_dt).days
#                             recency = 1.0 / (1.0 + days_since_access)
#                         else:
#                             recency = 0.5
#                     except:
#                         recency = 0.5
#
#                     # 计算相似性分数（距离转换为相似度）
#                     similarity_score = 1.0 / (1.0 + distances[0][i])
#
#                     # 计算综合分数
#                     memory["score"] = (
#                             similarity_score * similarity_weight +
#                             recency * recency_weight +
#                             memory["importance"] * importance_weight
#                     )
#
#                     # 添加详细评分信息（用于调试）
#                     memory["score_breakdown"] = {
#                         "similarity": similarity_score,
#                         "recency": recency,
#                         "importance": memory["importance"],
#                         "weights": {
#                             "similarity": similarity_weight,
#                             "recency": recency_weight,
#                             "importance": importance_weight
#                         }
#                     }
#
#                     results.append(memory)
#
#             # 按分数排序并返回前top_k个
#             results.sort(key=lambda x: x["score"], reverse=True)
#
#             # 更新访问信息
#             for memory in results[:top_k]:
#                 self.update_memory_access(memory["id"])
#
#             return results[:top_k]
#
#         except Exception as e:
#             logger.error(f"❌  记忆检索失败: {e}")
#             # 降级处理：返回最近的重要记忆
#             return self._fallback_retrieve(top_k)
#
#     def _fallback_retrieve(self, top_k=5):
#         """降级记忆检索方案"""
#         recent_memories = sorted(
#             self.memory_store,
#             key=lambda x: (x["importance"], parse(x["last_accessed"])),
#             reverse=True
#         )
#         return recent_memories[:top_k]
#
#     def update_memory_access(self, memory_id):
#         """更新记忆访问信息"""
#         if memory_id < len(self.memory_store):
#             memory = self.memory_store[memory_id]
#             memory["last_accessed"] = datetime.now().isoformat()
#             memory["access_count"] += 1
#
#     def cluster_memories(self, n_clusters=5):
#         """聚类相关记忆"""
#         if len(self.memory_store) < n_clusters or self.memory_embeddings is None:
#             for memory in self.memory_store:
#                 memory["cluster"] = -1
#             return
#
#         try:
#             kmeans = KMeans(
#                 n_clusters=min(n_clusters, len(self.memory_store)),
#                 random_state=0,
#                 n_init=10  # 明确设置n_init以避免警告
#             )
#             clusters = kmeans.fit_predict(self.memory_embeddings)
#
#             for i, label in enumerate(clusters):
#                 self.memory_store[i]["cluster"] = int(label)
#
#         except Exception as e:
#             logger.error(f"❌  记忆聚类失败: {e}")
#             for memory in self.memory_store:
#                 memory["cluster"] = -1
#
#     def summarize_context(self, query, max_tokens=500):
#         """生成上下文摘要"""
#         relevant_memories = self.retrieve_memories(query, top_k=10)
#
#         if not relevant_memories:
#             return "暂无相关记忆"
#
#         # 按主题分组记忆
#         topics = {}
#         for memory in relevant_memories:
#             cluster = memory["cluster"]
#             if cluster not in topics:
#                 topics[cluster] = []
#             topics[cluster].append(memory)
#
#         # 生成主题摘要
#         summaries = []
#         for cluster, memories in topics.items():
#             memories.sort(key=lambda x: x["importance"] * x["access_count"], reverse=True)
#             cluster_summary = "、".join([m["content"][:50] + "..." for m in memories[:3]])
#             cluster_label = f"主题{cluster + 1}" if cluster >= 0 else "未分类主题"
#             summaries.append(f"{cluster_label}: {cluster_summary}")
#
#         full_summary = "\n".join(summaries)[:max_tokens]
#         logger.info(f"📝  生成上下文摘要，长度: {len(full_summary)}")
#         return full_summary
#
#     def extract_key_info(self, text):
#         """从文本中提取关键信息（用户名、AI名称等）"""
#         key_info = {}
#
#         if not text or not isinstance(text, str):
#             return key_info
#
#         # 提取用户姓名
#         name_keywords = ["我叫", "我是", "你可以叫我", "我的名字是", "称呼我"]
#         for keyword in name_keywords:
#             if keyword in text:
#                 start_index = text.index(keyword) + len(keyword)
#                 rest_text = text[start_index:]
#
#                 # 查找结束位置
#                 end_chars = ["。", "，", "！", "？", "；", "：", ".", ",", "!", "?", ";", ":", " "]
#                 end_index = len(rest_text)
#                 for char in end_chars:
#                     if char in rest_text:
#                         char_index = rest_text.index(char)
#                         if char_index < end_index:
#                             end_index = char_index
#
#                 name = rest_text[:end_index].strip()
#                 if 2 <= len(name) <= 4 and all(c.isalpha() or c.isspace() for c in name):
#                     key_info["user_name"] = name
#                     logger.info(f"👤  提取到用户名: {name}")
#                     break
#
#         # 提取AI名称
#         ai_name_keywords = ["你就叫", "你的名字是", "我称你为", "你就称呼", "你的名称"]
#         for keyword in ai_name_keywords:
#             if keyword in text:
#                 start_index = text.index(keyword) + len(keyword)
#                 rest_text = text[start_index:]
#
#                 end_chars = ["。", "，", "！", "？", "；", "：", ".", ",", "!", "?", ";", ":", " "]
#                 end_index = len(rest_text)
#                 for char in end_chars:
#                     if char in rest_text:
#                         char_index = rest_text.index(char)
#                         if char_index < end_index:
#                             end_index = char_index
#
#                 name = rest_text[:end_index].strip()
#                 if 2 <= len(name) <= 6:
#                     key_info["ai_name"] = name
#                     logger.info(f"🤖  提取到AI名称: {name}")
#                     break
#
#         return key_info
#
#     def get_memory_stats(self):
#         """获取记忆系统统计信息"""
#         if not self.memory_store:
#             return {
#                 "total_memories": 0,
#                 "embedding_types": {},
#                 "avg_importance": 0,
#                 "avg_access_count": 0
#             }
#
#         embedding_types = {}
#         total_importance = 0
#         total_access = 0
#
#         for memory in self.memory_store:
#             embed_type = memory.get("embedding_type", "unknown")
#             embedding_types[embed_type] = embedding_types.get(embed_type, 0) + 1
#             total_importance += memory.get("importance", 1.0)
#             total_access += memory.get("access_count", 0)
#
#         return {
#             "total_memories": len(self.memory_store),
#             "embedding_types": embedding_types,
#             "avg_importance": total_importance / len(self.memory_store),
#             "avg_access_count": total_access / len(self.memory_store)
#         }
#
#     def clear_memories(self):
#         """清空所有记忆（用于测试或重置）"""
#         self.memory_store = []
#         self.memory_embeddings = None
#         self.index = None
#         logger.warning("⚠️  已清空所有记忆")