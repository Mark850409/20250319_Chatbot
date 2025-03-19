#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mistral AI 聊天應用啟動腳本
"""

import os
import webbrowser
from app import app

def main():   
    # 啟動伺服器
    port = 5000
    url = f"http://127.0.0.1:{port}/"
    
    print(f"正在啟動 Mistral AI 聊天應用...")
    print(f"應用將在瀏覽器中開啟: {url}")
    
    # 嘗試開啟瀏覽器
    try:
        webbrowser.open(url)
    except:
        print("無法自動開啟瀏覽器，請手動訪問上面的連結。")
    
    # 啟動 Flask 應用
    app.run(debug=True, port=port)

if __name__ == "__main__":
    main() 