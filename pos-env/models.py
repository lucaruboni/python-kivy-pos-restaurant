import sqlite3

# Connetti al database
conn = sqlite3.connect("pos_pizzeria.db")
cursor = conn.cursor()

# Inserisci l'utente admin
query = """
INSERT INTO users (username, password)
VALUES ('admin', 'b830e5b4effe494b9b86c9b07a77136165d43c6ea53be3c1dddda483b50526d0');
"""
cursor.execute(query)
conn.commit()

# Verifica l'inserimento
cursor.execute("SELECT * FROM users")
print("Utenti nel database:", cursor.fetchall())

# Chiudi la connessione
conn.close()
