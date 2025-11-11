from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify, make_response
from datetime import datetime
from init_db import get_db
from auth_utils import make_mini_token
from admin_session import is_logged_in, is_admin_session
import hashlib, os

#Descomente caso queira utilizar ferramentas como BURPSUITE E CAIDO
#os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8080'
#os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8080'

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-key') 

@app.route('/')
def home():
    return render_template('index.html', logged_in=is_logged_in(), is_admin=is_admin_session())

@app.route('/api/login', methods=['GET'])
def login():
    return render_template('login.html', logged_in=is_logged_in(), is_admin=is_admin_session())

@app.route('/api/users/autenticar', methods=['POST'])
def users_authenticate():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    senha_md5 = hashlib.md5(password.encode()).hexdigest()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id,name,role FROM users WHERE email = ? AND senha_md5 = ?', (email, senha_md5))
    user = c.fetchone()
    conn.close()
    if not user:
        return make_response(jsonify({'error': 'Credenciais inválidas'}), 401)

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['is_admin'] = (user['role'] == 'admin') 
    token_payload = {
        'user_id': user['id'],
        'user_name': user['name'],
        'is_admin': session['is_admin'],
        'iat': datetime.utcnow().isoformat()
    }
    token = make_mini_token(token_payload)
    if session['is_admin']:
        redirect_url = url_for('admin_panel')
    else:
        redirect_url = url_for('dashboard')
    resp = make_response(redirect(redirect_url))
    resp.headers['X-Auth-Token'] = token
    return resp

@app.route('/api/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha_md5 = hashlib.md5(password.encode()).hexdigest()

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            flash('E-mail já cadastrado!')
            return redirect(url_for('register'))

        c.execute(
            'INSERT INTO users (name, email, senha_md5, phone, cpf, role) VALUES (?, ?, ?, ?, ?, ?)',
            (name, email, senha_md5, phone, cpf, 'user')
        )
        conn.commit()
        conn.close()
        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('login'))
    return render_template('register.html', logged_in=is_logged_in(), is_admin=is_admin_session())


@app.route('/api/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, subject, body, created_at FROM messages WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    messages = c.fetchall()
    conn.close()

    return render_template('dashboard.html', name=session.get('user_name'), messages=messages, logged_in=True, is_admin=is_admin_session())

@app.route('/api/ouvidoria', methods=['GET', 'POST'])
def ouvidoria():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject = request.form.get('subject', '')
        body = request.form.get('body', '')
        # VULNERABILIDADE INTENCIONAL: aceita um field user_id no form.
        # Se user_id fornecido, usaremos aquele ID sem verificar se o session user tem permissão.
        # Isso demonstra como passar ID no body pode permitir ação em outra conta.
        victim_user_id = request.form.get('user_id')
        if victim_user_id:
            try:
                user_id = int(victim_user_id)
            except ValueError:
                user_id = session['user_id']
        else:
            user_id = session['user_id']

        conn = get_db()
        c = conn.cursor()
        c.execute(
            'INSERT INTO messages (user_id,subject,body,created_at) VALUES (?,?,?,?)',
            (user_id, subject, body, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('ouvidoria.html', logged_in=True, is_admin=is_admin_session())

@app.route('/api/delete_message/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    if not is_logged_in():
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE id = ? AND user_id = ?', (msg_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/api/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not is_logged_in():
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        # VULNERABILIDADE INTENCIONAL: se o corpo contiver user_id, ele será usado sem checar privilégios.
        # Isso permite alterar o perfil de outro usuário se o atacante fornecer user_id.
        target_id = request.form.get('user_id')
        if target_id:
            try:
                target_id = int(target_id)
            except ValueError:
                target_id = session['user_id']
        else:
            target_id = session['user_id']

        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        cpf = request.form.get('cpf', '').strip()
        new_password = request.form.get('password', '')
        if new_password:
            senha_md5 = hashlib.md5(new_password.encode()).hexdigest()
        else:
            c.execute('SELECT senha_md5 FROM users WHERE id = ?', (target_id,))
            row = c.fetchone()
            senha_md5 = row['senha_md5'] if row else ''
        c.execute('UPDATE users SET name=?, phone=?, cpf=?, senha_md5=? WHERE id=?',
                  (name, phone, cpf, senha_md5, target_id))
        conn.commit()
        if target_id == session['user_id']:
            session['user_name'] = name
        conn.close()
        flash('Perfil atualizado com sucesso!')
        return redirect(url_for('dashboard'))
    user_id = session['user_id']
    c.execute('SELECT name,email,phone,cpf FROM users WHERE id=?', (user_id,))
    user = c.fetchone()
    conn.close()
    return render_template('edit_profile.html', user=user, logged_in=True, is_admin=is_admin_session())

@app.route('/api/delete_account', methods=['POST'])
def delete_account():
    if not is_logged_in():
        return redirect(url_for('login'))
    # VULNERABILIDADE INTENCIONAL: se o corpo contiver user_id, ele será usado sem checar privilégios.
    # Isso permite deletar o perfil de outro usuário
    target_id = request.form.get('user_id')
    if target_id:
        try:
            target_id = int(target_id)
        except ValueError:
            target_id = session['user_id']
    else:
        target_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE user_id = ?', (target_id,))
    c.execute('DELETE FROM users WHERE id = ?', (target_id,))
    conn.commit()
    conn.close()
    if target_id == session['user_id']:
        session.clear()
        return redirect(url_for('home'))
    return redirect(url_for('dashboard'))

@app.route('/api/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/users', strict_slashes=False)
def api_users():
    if not is_logged_in():
        return render_template('admin_unauthorized.html'), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id,name,email,phone,cpf,senha_md5,role FROM users WHERE role != 'admin'")
    rows = c.fetchall()
    users = [dict(r) for r in rows]
    conn.close()
    return jsonify(users)

@app.route('/api/messages', strict_slashes=False)
def api_messages():
    if not is_logged_in():
       return render_template('admin_unauthorized.html'), 401
    conn = get_db()
    c = conn.cursor()
    c.execute(
        'SELECT m.id,m.user_id,m.subject,m.body,m.created_at,u.name,u.email '
        'FROM messages m JOIN users u ON m.user_id=u.id ORDER BY m.created_at DESC'
    )
    rows = c.fetchall()
    msgs = [{
        'id': r[0],
        'user_id': r[1],
        'subject': r[2],
        'body': r[3],
        'created_at': r[4],
        'user_name': r[5],
        'user_email': r[6],
    } for r in rows]
    conn.close()
    return jsonify(msgs)

@app.route('/api/painel')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'")
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM messages')
    total_messages = c.fetchone()[0]
    c.execute("SELECT id, name, email FROM users WHERE role != 'admin'")
    users = [dict(r) for r in c.fetchall()]
    conn.close()
    return render_template('admin.html',
        users=users,
        total_users=total_users,
        total_messages=total_messages,
        logged_in=True,
        is_admin=True
    )

@app.route('/api/painel/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE user_id = ?', (user_id,))
    c.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
