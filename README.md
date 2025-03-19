# Mistral AI 聊天應用

這是一個基於 Flask 的聊天應用，使用 Mistral AI 的模型提供智能對話功能，支援文字和圖片互動。

## 功能特點

- 與 Mistral AI 模型進行文字對話
- 支援上傳圖片進行視覺分析和對話
- 支援多種圖片格式：PNG, JPG, JPEG, GIF, WEBP, BMP, TIFF, SVG
- 圖片自動調整尺寸和優化品質，提供多種尺寸和品質選項
- 儲存對話歷史記錄到本地
- 查看和恢復歷史對話
- 美觀的使用者介面，回應式設計

## 安裝

1. 克隆儲存庫或下載原始碼
2. 安裝相依套件
```bash
pip install -r requirements.txt
```

## 設定

在執行應用前，需要設定 Mistral AI 的 API 金鑰。您可以在 https://console.mistral.ai/home 註冊並獲取 API 金鑰。

有兩種方式設定 API 金鑰:

1. 設定環境變數:
```bash
export MISTRAL_API_KEY=your_api_key_here
```

2. 在 `config.py` 檔案中直接設定:
```python 
MISTRAL_API_KEY = "your_api_key_here"
```

## 執行應用

```bash
cd mistral-flask-app
python run.py
```

應用將在本地執行，訪問 http://127.0.0.1:5000/ 開始使用。

## 目錄結構

```
mistral-flask-app/
├── app.py            # Flask應用主文件
├── run.py            # 啟動腳本
├── config.py         # 配置文件
├── requirements.txt  # 依賴列表
├── static/           # 靜態資源
│   ├── css/          # CSS樣式文件
│   ├── js/           # JavaScript文件
│   └── uploads/      # 上傳的圖片儲存
├── templates/        # HTML模板
│   ├── index.html    # 主聊天頁面
│   └── history.html  # 歷史記錄頁面
└── data/             # 數據儲存
    └── conversations/ # 對話歷史記錄
```

## 使用方法

1. 在聊天輸入框中輸入文字進行對話
2. 點擊圖片按鈕上傳圖片進行視覺分析
3. 上傳圖片時可以選擇圖片尺寸（原始、小、中、大）和品質（低、中、高）
4. 點擊"歷史記錄"按鈕查看過去的對話
5. 點擊"新對話"按鈕開始一個新的對話

## 注意事項

- 對話歷史記錄保存在本地 `data/conversations` 目錄中
- 上傳的圖片暫存在 `static/uploads` 目錄中 

## 許可證

本項目採用MIT許可證。詳情請見LICENSE文件。 