from flask import Flask, request, session, send_file, redirect, url_for
from telethon import TelegramClient
import os, uuid, shutil, threading, time, asyncio

app = Flask(__name__)
app.secret_key = 'supewwahpdxxptku'

SESSION_DIR = 'sessions'
SESSION_FILENAME = 'aayco.session'

def schedule_cleanup(path, delay=600):
    def delete_later():
        time.sleep(delay)
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    threading.Thread(target=delete_later, daemon=True).start()

# Async functions for Telethon
async def send_code_request_async(session_path, api_id, api_hash, phone):
    client = TelegramClient(f"{session_path}/{SESSION_FILENAME}", api_id, api_hash)
    await client.connect()
    await client.send_code_request(phone)
    await client.disconnect()

async def sign_in_async(session_path, api_id, api_hash, phone, code):
    client = TelegramClient(f"{session_path}/{SESSION_FILENAME}", api_id, api_hash)
    await client.connect()
    await client.sign_in(phone, code)
    await client.disconnect()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        step = request.form.get('step')

        if step == 'api':
            session['api_id'] = int(request.form['api_id'])
            session['api_hash'] = request.form['api_hash']
            return phone_form()

        elif step == 'phone':
            session['phone'] = request.form['phone']
            unique_folder = f"{SESSION_DIR}/{uuid.uuid4().hex}"
            os.makedirs(unique_folder, exist_ok=True)
            session['session_path'] = unique_folder
            asyncio.run(send_code_request_async(unique_folder, session['api_id'], session['api_hash'], session['phone']))
            return code_form()

        elif step == 'code':
            code = request.form['code']
            session_path = session.get('session_path')
            asyncio.run(sign_in_async(session_path, session['api_id'], session['api_hash'], session['phone'], code))
            schedule_cleanup(session_path)
            return redirect(url_for('done'))

    return api_form()

@app.route('/done')
def done():
    session_file = f"{session.get('session_path')}/{SESSION_FILENAME}"
    return f"""
        <h2>You're logged in!</h2>
        <a href="/download/{session_file}">Download session file</a>
    """

@app.route('/download/<path:filename>')
def download_session(filename):
    return send_file(filename, as_attachment=True)

# HTML forms as string responses
def api_form():
    return '''
        <h2>Step 1: Enter API ID and Hash</h2>
        <form method="POST">
            <input type="hidden" name="step" value="api">
            API ID: <input name="api_id"><br>
            API Hash: <input name="api_hash"><br>
            <button type="submit">Next</button>
        </form>
    '''

def phone_form():
    return '''
        <h2>Step 2: Enter Phone Number</h2>
        <form method="POST">
            <input type="hidden" name="step" value="phone">
            Phone: <input name="phone"><br>
            <button type="submit">Send Code</button>
        </form>
    '''

def code_form():
    return '''
        <h2>Step 3: Enter Code</h2>
        <form method="POST">
            <input type="hidden" name="step" value="code">
            Code: <input name="code"><br>
            <button type="submit">Login</button>
        </form>
    '''

if __name__ == '__main__':
    os.makedirs(SESSION_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
