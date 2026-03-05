# testapi.py 完整版本
import os
from dotenv import load_dotenv
import dashscope
from dashscope import Generation
from http import HTTPStatus

# ⭐ 关键：先加载 .env 文件
load_dotenv()  # 默认加载当前目录的 .env

# 验证是否加载成功
api_key = os.getenv("DASHSCOPE_API_KEY")
print(f"🔍 API Key 加载状态：{'✅ 已加载' if api_key else '❌ 未加载'}")
print(f"🔍 API Key 前缀：{api_key[:10]}..." if api_key else "")

# 设置到 dashscope
if api_key:
    dashscope.api_key = api_key
else:
    print("⚠️ 警告：未找到 API Key，请检查 .env 文件")
    exit(1)

# 调用 API
response = Generation.call(
    model="qwen-flash",
    prompt="智能制造专业介绍"
)

if response.status_code == HTTPStatus.OK:
    print("✅ Success:", response.output.text)
else:
    print(f"❌ Error {response.code}: {response.message}")