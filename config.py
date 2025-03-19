import os

# 从环境变量获取API密钥，如果不存在则使用空字符串
MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY', '')

# 如果没有设置API密钥，可以在这里手动设置
MISTRAL_API_KEY = ""

# Mistral API 配置
MISTRAL_MODEL = "mistral-small-latest"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# Jina API 配置
JINA_API_URL = "https://deepsearch.jina.ai/v1/chat/completions" 