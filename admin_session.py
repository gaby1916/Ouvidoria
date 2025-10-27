from flask import session
import hashlib
from init_db import get_db

def is_logged_in():
    return 'user_id' in session

def is_admin_session():
    return session.get('is_admin') is True

def ensure_admin_exists():
    conn = get_db()
    c = conn.cursor()
    admin_email = 'admin@admin.local'
    admin_password = 'admin123' 
    admin_hash = hashlib.md5(admin_password.encode()).hexdigest()
    c.execute('SELECT id FROM users WHERE email = ?', (admin_email,))
    if not c.fetchone():
        c.execute('INSERT INTO users (name,email,senha_md5,phone,cpf,role) VALUES (?,?,?,?,?,?)',
                  ('Administrador', admin_email, admin_hash, '0000000000', '00000000000', 'admin'))
        conn.commit()
    conn.close()
    
ensure_admin_exists()
