from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
from functools import wraps
import openai

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# تكوين Gemini
my_api_key_gemini = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=my_api_key_gemini)
model_gemini = genai.GenerativeModel('gemini-pro')

# تكوين OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# رمز التفعيل
ACTIVATION_CODE = os.getenv('ACTIVATION_CODE', 'Admin2024')

app = Flask(__name__)
app.secret_key = os.urandom(24)

# دالة للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def format_response(text):
    # معالجة النص العريض مع الأحجام المختلفة
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # معالجة النص العريض في بداية السطر
        if line.strip().startswith('**') and line.strip().endswith('**'):
            text = line.strip()[2:-2]  # إزالة النجمتين
            formatted_lines.append(f'<h2 class="bold-heading">{text}</h2>')
            continue
            
        # معالجة النص العريض في وسط السطر
        while '**' in line:
            start = line.find('**')
            end = line.find('**', start + 2)
            if start != -1 and end != -1:
                text = line[start+2:end]
                line = line[:start] + f'<span class="inline-bold">{text}</span>' + line[end+2:]
            else:
                break
                
        formatted_lines.append(f'<p class="response-paragraph">{line}</p>')
    
    return '\n'.join(formatted_lines)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        activation_code = request.form.get('activation_code')
        if activation_code == ACTIVATION_CODE:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='رمز التفعيل غير صحيح')
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        model_type = data.get('model', 'gemini')

        if model_type == 'gemini':
            response = model_gemini.generate_content(user_input)
            response_text = response.text
        else:  # OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "أنت مساعد مفيد يجيب باللغة العربية."},
                    {"role": "user", "content": user_input}
                ]
            )
            response_text = response.choices[0].message.content

        formatted_response = format_response(response_text)
        return jsonify({"response": formatted_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
