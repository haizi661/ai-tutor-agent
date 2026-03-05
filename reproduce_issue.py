import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage

# 加载 .env
load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"API Key prefix: {api_key[:10] if api_key else 'None'}")

try:
    llm = ChatTongyi(
        model_name="qwen-max",
        dashscope_api_key=api_key,
        temperature=0.7
    )
    print("Initiating test call...")
    response = llm.invoke([HumanMessage(content="Hello, are you working?")])
    print("Response received:")
    print(response.content)

except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
