from flask import Flask, render_template_string, request, redirect, url_for, abort, make_response
import requests
from telegram import Bot
import ipinfo
from threading import Thread
import os
from collections import OrderedDict

app = Flask(__name__)

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = '7502616150:AAG-biBErcrZmHsrJ0JH-j83jNoaBtkvnKk'
TELEGRAM_ADMIN_ID = '7627713755'
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# IP info configuration
IPINFO_TOKEN = 'YOUR_IPINFO_TOKEN'  # You need to get this from ipinfo.io
handler = ipinfo.getHandler(IPINFO_TOKEN)

# User database with max users limit
users = OrderedDict({
    'admin': {'password': 'password123', 'max_users': 100}
})
max_total_users = 100  # Maximum total users allowed

# أحاديث عن الردة وعقوباتها (60 حديث)
hadeeth_collection = [
    {
        'arabic': 'قال رسول الله صلى الله عليه وسلم: "من بدل دينه فاقتلوه"',
        'english': 'The Prophet (peace be upon him) said: "Whoever changes his religion, kill him." (Bukhari)'
    },
    {
        'arabic': 'قال رسول الله صلى الله عليه وسلم: "لا يحل دم امرئ مسلم إلا بإحدى ثلاث: الثيب الزاني، والنفس بالنفس، والتارك لدينه المفارق للجماعة"',
        'english': 'The Prophet (peace be upon him) said: "It is not permissible to spill the blood of a Muslim except in three cases: the married adulterer, life for life, and the one who leaves his religion and separates from the community." (Bukhari)'
    },
    # ... (سأضيف 58 حديثاً أخرى هنا)
    # يمكنك إضافة المزيد من الأحاديث بنفس الهيكل
]

# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Khalifa Souda</title>
    <style>
        body { background-color: #000; color: #fff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background-color: #111; padding: 40px; border-radius: 10px; box-shadow: 0 0 20px rgba(255, 255, 255, 0.1); width: 350px; text-align: center; }
        .login-logo { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 20px; border: 3px solid #333; }
        h1 { color: #fff; margin-bottom: 30px; font-weight: bold; }
        .form-group { margin-bottom: 20px; text-align: left; }
        label { display: block; margin-bottom: 5px; color: #ccc; }
        input { width: 100%; padding: 10px; border: 1px solid #333; border-radius: 5px; background-color: #222; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background-color: #000; color: #fff; border: 1px solid #333; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background-color 0.3s; }
        button:hover { background-color: #222; }
        .error { color: #ff4444; font-weight: bold; margin-bottom: 15px; }
        .success { color: #44ff44; font-weight: bold; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-container">
        <img src="https://images.app.goo.gl/2jJEE5kpxy8wJ8Sc9" alt="Khalifa Souda" class="login-logo">
        <h1>Khalifa Souda</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" value="{{ username or '' }}" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <p style="margin-top: 20px;"><a href="/create_user" style="color: #ccc;">Create new account</a></p>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Khalifa Souda</title>
    <style>
        body { background-color: #000; color: #fff; font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .header { background-color: #111; padding: 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; }
        .logo-container { display: flex; align-items: center; }
        .logo { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; margin-right: 15px; border: 2px solid #333; }
        .verified-badge { color: #333; font-size: 12px; margin-top: 5px; display: flex; align-items: center; justify-content: center; }
        .nav { display: flex; background-color: #111; padding: 10px 0; border-bottom: 1px solid #333; }
        .nav-item { padding: 10px 20px; cursor: pointer; border-right: 1px solid #333; }
        .nav-item:hover { background-color: #222; }
        .content { padding: 30px; }
        .hadith-container { background-color: #111; padding: 20px; margin-bottom: 20px; border-radius: 5px; border-left: 4px solid #333; }
        .hadith-arabic { font-family: 'Traditional Arabic', Arial, sans-serif; font-size: 24px; color: #fff; text-align: right; margin-bottom: 15px; line-height: 1.6; }
        .hadith-english { font-size: 16px; color: #ccc; line-height: 1.5; }
        .logout-btn { background-color: #111; color: #fff; border: 1px solid #333; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
        .logout-btn:hover { background-color: #222; }
        .user-info { color: #ccc; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-container">
            <img src="https://images.app.goo.gl/zKeS4e9VVQKkkLi88" alt="Khalifa Souda" class="logo">
            <div>
                <h2>Khalifa Souda</h2>
                <div class="verified-badge">
                    <span>Verified</span>
                </div>
            </div>
        </div>
        <div>
            <span class="user-info">Logged in as: {{ username }}</span>
            <button class="logout-btn" onclick="window.location.href='/logout'">Logout</button>
        </div>
    </div>
    
    <div class="nav">
        <div class="nav-item" onclick="window.location.href='/Dash'">Religious Rulings</div>
        <div class="nav-item" onclick="window.location.href='/hadeeth'">Hadeeth Collection</div>
        {% if is_admin %}
        <div class="nav-item" onclick="window.location.href='/create_user'">Create User</div>
        {% endif %}
    </div>
    
    <div class="content">
        {% for hadith in hadeeths %}
        <div class="hadith-container">
            <div class="hadith-arabic">
                {{ hadith.arabic }}
            </div>
            <div class="hadith-english">
                {{ hadith.english }}
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
'''

CREATE_USER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create User - Khalifa Souda</title>
    <style>
        body { background-color: #000; color: #fff; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .user-container { background-color: #111; padding: 40px; border-radius: 10px; box-shadow: 0 0 20px rgba(255, 255, 255, 0.1); width: 350px; text-align: center; }
        h1 { color: #fff; margin-bottom: 30px; font-weight: bold; }
        .form-group { margin-bottom: 20px; text-align: left; }
        label { display: block; margin-bottom: 5px; color: #ccc; }
        input, select { width: 100%; padding: 10px; border: 1px solid #333; border-radius: 5px; background-color: #222; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background-color: #000; color: #fff; border: 1px solid #333; border-radius: 5px; cursor: pointer; font-weight: bold; transition: background-color 0.3s; }
        button:hover { background-color: #222; }
        .error { color: #ff4444; font-weight: bold; margin-bottom: 15px; }
        .success { color: #44ff44; font-weight: bold; margin-bottom: 15px; }
        .back-link { color: #ccc; margin-top: 20px; display: inline-block; }
    </style>
</head>
<body>
    <div class="user-container">
        <h1>Create New User</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
        <div class="success">{{ success }}</div>
        {% endif %}
        
        <form method="POST" action="/create_user">
            <div class="form-group">
                <label for="new_username">Username</label>
                <input type="text" id="new_username" name="new_username" required>
            </div>
            <div class="form-group">
                <label for="new_password">Password</label>
                <input type="password" id="new_password" name="new_password" required>
            </div>
            <div class="form-group">
                <label for="max_users">Max Allowed Users</label>
                <input type="number" id="max_users" name="max_users" min="1" max="100" value="5" required>
            </div>
            <button type="submit">Create User</button>
        </form>
        <a href="/login" class="back-link">Back to Login</a>
    </div>
</body>
</html>
'''

def send_telegram_alert(message):
    try:
        bot.send_message(chat_id=TELEGRAM_ADMIN_ID, text=message)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_ip_info(ip_address):
    try:
        details = handler.getDetails(ip_address)
        return {
            'ip': ip_address,
            'city': details.city,
            'region': details.region,
            'country': details.country_name,
            'org': details.org,
            'hostname': details.hostname
        }
    except Exception as e:
        print(f"Error getting IP info: {e}")
        return {'ip': ip_address, 'error': 'Could not fetch details'}

@app.route('/shutdown')
def shutdown():
    if not request.cookies.get('logged_in') == 'true' or not request.args.get('username') == 'admin':
        abort(403)
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Server is shutting down..."

@app.route('/Dash')
def dash():
    if not request.cookies.get('logged_in') == 'true':
        return redirect(url_for('login'))
    
    username = request.cookies.get('username')
    is_admin = username == 'admin'
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                               username=username,
                               is_admin=is_admin,
                               hadeeths=hadeeth_collection[:5])

@app.route('/hadeeth')
def hadeeth():
    if not request.cookies.get('logged_in') == 'true':
        return redirect(url_for('login'))
    
    username = request.cookies.get('username')
    is_admin = username == 'admin'
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                               username=username,
                               is_admin=is_admin,
                               hadeeths=hadeeth_collection)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            resp = make_response(redirect(url_for('dash')))
            resp.set_cookie('logged_in', 'true')
            resp.set_cookie('username', username)
            
            ip_address = request.remote_addr
            ip_info = get_ip_info(ip_address)
            message = f"✅ Successful login:\nUser: {username}\nIP: {ip_address}\n"
            message += f"Location: {ip_info.get('city', 'N/A')}, {ip_info.get('country', 'N/A')}\n"
            message += f"ISP: {ip_info.get('org', 'N/A')}"
            
            Thread(target=send_telegram_alert, args=(message,)).start()
            
            return resp
        else:
            ip_address = request.remote_addr
            ip_info = get_ip_info(ip_address)
            message = f"⚠️ Failed login attempt:\nUsername tried: {username}\nIP: {ip_address}\n"
            message += f"Location: {ip_info.get('city', 'N/A')}, {ip_info.get('country', 'N/A')}\n"
            message += f"ISP: {ip_info.get('org', 'N/A')}"
            
            Thread(target=send_telegram_alert, args=(message,)).start()
            
            return render_template_string(LOGIN_TEMPLATE, 
                                      error="Invalid username or password", 
                                      username=username)
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        admin_username = request.cookies.get('username')
        if admin_username != 'admin':
            return render_template_string(CREATE_USER_TEMPLATE, 
                                        error="Only admin can create users")
        
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        max_users = int(request.form.get('max_users'))
        
        if new_username in users:
            return render_template_string(CREATE_USER_TEMPLATE, 
                                      error="Username already exists")
        
        if len(users) >= max_total_users:
            return render_template_string(CREATE_USER_TEMPLATE, 
                                      error="Maximum user limit reached")
        
        users[new_username] = {'password': new_password, 'max_users': max_users}
        
        return render_template_string(CREATE_USER_TEMPLATE, 
                                    success=f"User {new_username} created successfully")
    
    return render_template_string(CREATE_USER_TEMPLATE)

@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('logged_in', '', expires=0)
    resp.set_cookie('username', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run(debug=True)
