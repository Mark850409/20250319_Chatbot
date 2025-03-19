#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mistral AI 聊天应用启动脚本
"""

import os
import webbrowser
from app import app

def main():
    # 检查配置是否完成
    from config import MISTRAL_API_KEY
    
    if not MISTRAL_API_KEY:
        print("="*60)
        print("警告: 未检测到Mistral API密钥！")
        print("请先在config.py文件中设置您的API密钥，或者设置MISTRAL_API_KEY环境变量。")
        print("="*60)
        key = input("如果您想现在输入API密钥，请输入(或按回车跳过): ")
        if key.strip():
            # 更新config.py文件
            with open('config.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = content.replace('# MISTRAL_API_KEY = "your-api-key-here"', f'MISTRAL_API_KEY = "{key.strip()}"')
            
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("API密钥已更新！")
    
    # 启动服务器
    port = 5000
    url = f"http://127.0.0.1:{port}/"
    
    print(f"正在启动Mistral AI聊天应用...")
    print(f"应用将在浏览器中打开: {url}")
    
    # 尝试打开浏览器
    try:
        webbrowser.open(url)
    except:
        print("无法自动打开浏览器，请手动访问上面的链接。")
    
    # 启动Flask应用
    app.run(debug=True, port=port)

if __name__ == "__main__":
    main() 