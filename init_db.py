import sqlite3
import hashlib
import os

DB = os.path.join(os.path.dirname(__file__), 'ouvidoria.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    create_schema = not os.path.exists(DB)

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if create_schema:
        print("Criando novo banco de dados...")
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_md5 TEXT NOT NULL,
            phone TEXT,
            cpf TEXT,
            role TEXT DEFAULT 'user'
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            body TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        ''')

        users = [
            ('Alice Silva', 'alice@gmail.com', 'password123', '(93)99177-9966', '939.713.414-03', 'user'),
            ('Bruno Costa', 'bruno@example.com', '12345678', '(93)99187-3576', '156.398.024-05', 'user'),
            ('Carla Souza', 'carla@icloud.com', 'senhafoda', '(93)99155-4433', '752.198.654-71', 'user'),
        ]

        for name, email, pw, phone, cpf, role in users:
            h = hashlib.md5(pw.encode()).hexdigest()
            c.execute(
                'INSERT INTO users (name,email,senha_md5,phone,cpf,role) VALUES (?,?,?,?,?,?)',
                (name, email, h, phone, cpf, role)
            )

        messages = [
            (1, 'Elogio', 'Ótimo atendimento!', '2025-10-10 10:00:00'),
            (2, 'Reclamação', 'Demora no retorno', '2025-10-09 09:30:00'),
        ]

        for user_id, subject, body, created_at in messages:
            c.execute(
                'INSERT INTO messages (user_id,subject,body,created_at) VALUES (?,?,?,?)',
                (user_id, subject, body, created_at)
            )

        print("Banco inicializado com dados de exemplo.")
    else:
        print("Banco já existente. Mantendo os dados atuais.")

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
