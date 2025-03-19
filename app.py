from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response, stream_with_context
import os
import json
import uuid
import requests
from datetime import datetime
import base64
from werkzeug.utils import secure_filename
from PIL import Image
from dotenv import load_dotenv


# 載入環境變數
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['CONVERSATIONS_FOLDER'] = 'data/conversations'

# 確保上傳和會話目錄存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CONVERSATIONS_FOLDER'], exist_ok=True)

# 允許的圖片類型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_image_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_conversation(conversation_id, messages):
    # 建立一個可以儲存的訊息版本，移除大型base64資料但保留前端顯示所需資訊
    storable_messages = []
    for msg in messages:
        if msg['role'] == 'user' and isinstance(msg.get('content'), list):
            # 處理包含圖片的訊息
            new_msg = {'role': 'user', 'content': []}
            
            # 查找訊息中的文字和圖片
            text_content = None
            image_path = None
            
            for item in msg['content']:
                if item.get('type') == 'text':
                    text_content = item.get('text', '')
                    new_msg['content'].append(item)
                elif item.get('type') == 'image_url':
                    # 從訊息物件中獲取圖片路徑
                    if '_image_path' in msg:
                        image_path = msg['_image_path']
                        # 保留圖片引用而不是base64資料
                        new_msg['content'].append({
                            'type': 'image_url',
                            'image_url': {
                                'url': f"/static/{image_path.replace('static/', '')}"
                            }
                        })
                    else:
                        # 移除圖片的base64資料，避免JSON過大
                        new_msg['content'].append({
                            'type': 'image_url',
                            'image_url': {
                                'url': '/static/img/placeholder.png'  # 使用佔位圖
                            }
                        })
            
            if text_content:
                # 儲存欄位用底線前綴，表示僅用於前端顯示，不發送到API
                new_msg['_display_content'] = text_content
                
            if image_path:
                # 儲存欄位用底線前綴，表示僅用於前端顯示，不發送到API
                new_msg['_image_path'] = image_path.replace('static/', '')
                
            storable_messages.append(new_msg)
        else:
            # 保留其他類型的訊息不變
            storable_messages.append(msg)
    
    filepath = os.path.join(app.config['CONVERSATIONS_FOLDER'], f"{conversation_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'messages': storable_messages
        }, f, ensure_ascii=False)

def load_conversation(conversation_id):
    filepath = os.path.join(app.config['CONVERSATIONS_FOLDER'], f"{conversation_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_all_conversations():
    conversations = []
    for filename in os.listdir(app.config['CONVERSATIONS_FOLDER']):
        if filename.endswith('.json'):
            filepath = os.path.join(app.config['CONVERSATIONS_FOLDER'], filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 获取首条消息的预览
                preview = ""
                if data['messages']:
                    first_msg = data['messages'][0]
                    if isinstance(first_msg['content'], list):
                        for content_item in first_msg['content']:
                            if content_item.get('type') == 'text':
                                preview = content_item.get('text', '')
                                break
                    else:
                        preview = first_msg['content']
                
                conversations.append({
                    'id': data['id'],
                    'timestamp': data['timestamp'],
                    'preview': preview or "空对话"
                })
    return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)

def call_mistral_api(messages):
    if not os.getenv("MISTRAL_API_KEY"):
        return "未設置Mistral API金鑰。請在.env文件中設置MISTRAL_API_KEY。"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"
    }
    
    data = {
        "model": os.getenv("MISTRAL_MODEL"),
        "messages": messages
    }
    
    try:
        # 打印请求信息（不包含敏感的图片base64数据）
        import copy
        debug_data = copy.deepcopy(data)  # 使用深拷贝而不是浅拷贝
        for msg in debug_data['messages']:
            if msg['role'] == 'user' and isinstance(msg.get('content'), list):
                for item in msg['content']:
                    if item.get('type') == 'image_url' and item.get('image_url', {}).get('url', '').startswith('data:'):
                        item['image_url']['url'] = '[BASE64_IMAGE_DATA]'
        
        print(f"API請求: {json.dumps(debug_data, ensure_ascii=False, indent=2)}")
        
        # 发送实际请求，使用原始数据
        response = requests.post(os.getenv("MISTRAL_API_URL"), headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"API回應: 狀態碼 {response.status_code}")
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"API錯誤: 狀態碼 {response.status_code}, 回應: {response.text}")
            return f"API錯誤: {response.status_code}, {response.text}"
    except Exception as e:
        print(f"請求異常: {str(e)}")
        return f"請求錯誤: {str(e)}"

def call_jina_api(user_message, messages):
    headers = {
        "Content-Type": "application/json"
    }
    
    api_messages = []
    
    # 處理歷史消息
    for msg in messages:
        if msg['role'] == 'user':
            if isinstance(msg.get('content'), list):
                # 對於包含圖片的消息，只使用文字部分
                text_content = None
                for item in msg['content']:
                    if item.get('type') == 'text':
                        text_content = item.get('text', '')
                        break
                if text_content:
                    api_messages.append({
                        "role": "user",
                        "content": text_content
                    })
            else:
                # 純文字消息
                api_messages.append({
                    "role": "user",
                    "content": msg['content']
                })
        elif msg['role'] == 'assistant':
            api_messages.append({
                "role": "assistant",
                "content": msg['content']
            })
    
    # 添加當前用戶消息
    api_messages.append({
        "role": "user",
        "content": user_message
    })
    
    data = {
        "model": "jina-deepsearch-v1",
        "messages": api_messages,
        "stream": True,
        "reasoning_effort": "low",
        "no_direct_answer": False
    }
    
    try:
        print(f"Jina API 請求: {json.dumps(data, ensure_ascii=False, indent=2)}")
        response = requests.post(os.getenv("JINA_API_URL"), headers=headers, json=data, stream=True)
        
        if response.status_code == 200:
            thinking_content = ""
            final_answer = ""
            
            for line in response.iter_lines():
                if not line:
                    continue
                    
                try:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        line_text = line_text[5:]
                    
                    json_response = json.loads(line_text)
                    
                    if 'choices' in json_response:
                        delta = json_response['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        msg_type = delta.get('type', '')
                        
                        if msg_type == 'think':
                            if content:
                                content = content.replace('<think>', '').replace('</think>', '').replace('\n\n', '')
                                thinking_content += content
                                yield {
                                    "thinking": thinking_content,
                                    "answer": None
                                }
                        elif msg_type == 'text':
                            if content:
                                final_answer += content
                                if json_response['choices'][0].get('finish_reason') == 'stop':
                                    yield {
                                        "thinking": thinking_content,
                                        "answer": final_answer.strip()
                                    }
                                    
                except Exception as e:
                    print(f"處理回應行時出錯: {str(e)}")
                    continue
                    
        else:
            print(f"Jina API 錯誤: {response.status_code}, {response.text}")
            yield {
                "thinking": "處理請求時發生錯誤",
                "answer": f"API錯誤: {response.status_code}, {response.text}"
            }
            
    except Exception as e:
        print(f"請求錯誤: {str(e)}")
        yield {
            "thinking": "處理請求時發生錯誤",
            "answer": f"請求錯誤: {str(e)}"
        }

# 添加图片处理函数
def process_image(image_path, image_size='small', image_quality='medium'):
    """處理圖片：調整尺寸和優化品質"""
    try:
        img = Image.open(image_path)
        
        # 獲取原始圖片格式
        img_format = img.format
        
        # 根據選擇的尺寸設置最大寬高
        if image_size == 'original':
            max_width, max_height = img.size  # 保持原始尺寸
        elif image_size == 'small':
            max_width, max_height = 800, 800
        elif image_size == 'medium':
            max_width, max_height = 1200, 1200
        elif image_size == 'large':
            max_width, max_height = 1600, 1600
        else:
            max_width, max_height = 800, 800  # 預設值
        
        # 根據選擇的品質設置
        if image_quality == 'low':
            quality = 60
        elif image_quality == 'medium':
            quality = 85
        elif image_quality == 'high':
            quality = 95
        else:
            quality = 85  # 預設值
        
        # 調整圖片尺寸
        width, height = img.size
        if image_size != 'original' and (width > max_width or height > max_height):
            # 計算縮放比例
            ratio = min(max_width/width, max_height/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 儲存優化後的圖片
        if img_format in ['JPEG', 'JPG']:
            img.save(image_path, format=img_format, quality=quality, optimize=True)
        elif img_format == 'PNG':
            img.save(image_path, format=img_format, optimize=True)
        elif img_format in ['WEBP', 'GIF']:
            img.save(image_path, format=img_format)
        else:
            # 其他格式轉換為JPEG
            rgb_img = img.convert('RGB')
            rgb_img.save(image_path, format='JPEG', quality=quality, optimize=True)
            
        return True
    except Exception as e:
        print(f"圖片處理錯誤: {str(e)}")
        return False

@app.route('/')
def index():
    # 初始化或获取会话ID
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    conversation_id = session['conversation_id']
    conversation = load_conversation(conversation_id)
    
    if conversation and 'messages' in conversation:
        messages = conversation['messages']
    else:
        messages = []
    
    return render_template('index.html', 
                          messages=messages,
                          conversation_id=conversation_id)

@app.route('/stream_response', methods=['GET'])
def stream_response():
    user_message = request.args.get('message', '')
    messages = json.loads(request.args.get('messages', '[]'))
    
    def generate():
        response_generator = call_jina_api(user_message, messages)
        for response in response_generator:
            if response["thinking"] and not response["answer"]:
                # 只返回思考過程
                yield f"data: {json.dumps({'type': 'thinking', 'content': response['thinking']})}\n\n"
            elif response["answer"]:
                # 返回最終答案
                yield f"data: {json.dumps({'type': 'answer', 'content': response['answer']})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message', '')
    use_deep_reasoning = request.form.get('deep_reasoning') == 'true'
    
    if not user_message and 'image' not in request.files:
        return jsonify({"error": "請輸入消息或上傳圖片"}), 400
    
    # 添加會話ID
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    # 獲取當前會話的消息
    conversation_id = session['conversation_id']
    conversation = load_conversation(conversation_id)
    
    if conversation and 'messages' in conversation:
        messages = conversation['messages'].copy()
    else:
        messages = []
    
    # 處理圖片上傳
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
            file.save(image_path)
            
            # 獲取圖片處理選項
            image_size = request.form.get('image_size', 'small')
            image_quality = request.form.get('image_quality', 'medium')
            
            # 處理圖片：調整大小和優化質量
            process_image(image_path, image_size, image_quality)
            
            # 添加帶圖片的消息 - 正確格式化API消息
            api_message = {"role": "user", "content": []}
            
            if user_message:
                api_message["content"].append({"type": "text", "text": user_message})
            
            # 添加圖片內容 - 按照API文檔格式
            relative_path = image_path.replace('\\', '/')
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{get_image_base64(image_path)}"
                }
            }
            api_message["content"].append(image_content)
            
            # 為存儲保存原始路徑
            image_path_for_storage = relative_path
            
            # 添加到前端顯示消息
            display_message = {"role": "user", "content": user_message, "image": relative_path.replace('static/', '')}
            
        else:
            return jsonify({"error": "不支持的文件類型"}), 400
    else:
        # 純文本消息
        api_message = {"role": "user", "content": user_message}
        display_message = {"role": "user", "content": user_message}
    
    # 添加用戶消息到歷史
    messages.append(api_message)
    
    # 如果存在圖片路徑，為存儲目的添加
    if 'image' in request.files and image_path:
        messages[-1]["_image_path"] = image_path_for_storage
    
    # 準備用於API調用的消息列表
    max_context_messages = 10
    api_messages = messages[-max_context_messages:] if len(messages) > max_context_messages else messages
    
    # 移除任何不應該發送到API的字段
    api_messages_clean = []
    for msg in api_messages:
        if msg['role'] == 'user' and isinstance(msg.get('content'), list):
            # 對於包含圖片的複雜消息，需要特別處理
            clean_msg = {"role": "user", "content": []}
            
            # 只保留符合API格式的內容項
            for item in msg['content']:
                if item.get('type') == 'text':
                    clean_msg["content"].append({"type": "text", "text": item.get('text', '')})
                elif item.get('type') == 'image_url':
                    # 確保圖片URL格式正確
                    image_url = item.get('image_url', {}).get('url', '')
                    if image_url.startswith('data:') or image_url.startswith('http'):
                        clean_msg["content"].append({
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        })
            
            api_messages_clean.append(clean_msg)
        elif msg['role'] == 'user':
            api_messages_clean.append({"role": "user", "content": msg.get('content', '')})
        else:
            api_messages_clean.append({"role": "assistant", "content": msg.get('content', '')})
    
    print(f"清理後的API訊息數量: {len(api_messages_clean)}")
    
    # 根據是否使用深度推理選擇不同的API
    if use_deep_reasoning:
        return jsonify({
            "user_message": display_message,
            "stream": True,
            "messages": api_messages_clean
        })
    else:
        response = call_mistral_api(api_messages_clean)
        if not response:
            response = "抱歉，我現在無法提供有效的回答。"
        
        assistant_message = {"role": "assistant", "content": response}
        messages.append(assistant_message)
        
        # 保存對話到文件
        save_conversation(conversation_id, messages)
        
        return jsonify({
            "user_message": display_message,
            "assistant_message": assistant_message,
            "stream": False
        })

@app.route('/history')
def history():
    conversations = get_all_conversations()
    return render_template('history.html', conversations=conversations)

@app.route('/conversation/<conversation_id>')
def view_conversation(conversation_id):
    conversation = load_conversation(conversation_id)
    if conversation:
        session['conversation_id'] = conversation_id
        return redirect(url_for('index'))
    return redirect(url_for('history'))

@app.route('/new_conversation')
def new_conversation():
    session['conversation_id'] = str(uuid.uuid4())
    return redirect(url_for('index'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        # 獲取所有對話文件
        for filename in os.listdir(app.config['CONVERSATIONS_FOLDER']):
            if filename.endswith('.json'):
                file_path = os.path.join(app.config['CONVERSATIONS_FOLDER'], filename)
                os.remove(file_path)
        
        # 清除當前會話ID
        session.pop('conversation_id', None)
        
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"清空歷史記錄時出錯: {str(e)}")
        return jsonify({"error": "清空歷史記錄失敗"}), 500

if __name__ == '__main__':
    if not os.getenv("MISTRAL_API_KEY"):
        print("警告: 未設置 Mistral API 金鑰。請在 .env 檔案中設置 MISTRAL_API_KEY。")
    app.run(debug=True) 