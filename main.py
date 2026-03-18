import sys
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com" # 解决国内访问 Hugging Face API 慢的问题
# 必须先 import，才能打印它的 __file__ 属性
try:
    import ai_tutor_agent
    print(f"📍 正在加载的代码路径: {os.path.abspath(ai_tutor_agent.__file__)}")
except ImportError:
    print("❌ 无法导入 ai_tutor_agent，请检查当前目录下是否有该文件夹")
    
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        from ai_tutor_agent.cli import run_cli
        run_cli()
    else:
        from ai_tutor_agent.interfaces.api.app import run_api
        run_api()
