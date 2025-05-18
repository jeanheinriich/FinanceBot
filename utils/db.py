import sqlite3
import os
from datetime import datetime

DATABASE_NAME = os.path.join(os.path.dirname(__file__), '..', 'data', 'transactions.db')

def get_db_connection():
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'data'), exist_ok=True)
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL
    );
    ''')
    conn.commit()
    conn.close()
    print("Banco de dados inicializado ou já existente.")

def add_transaction(type: str, amount: float, category: str, description: str, date_str: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        cursor.execute('''
        INSERT INTO transactions (type, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?)
        ''', (type, amount, category, description, date_str))
        conn.commit()
        return cursor.lastrowid
    except ValueError:
        print(f"Erro: Formato de data inválido: {date_str}")
        return None
    except sqlite3.Error as e:
        print(f"Erro ao adicionar transação: {e}")
        return None
    finally:
        conn.close()

def get_transactions(start_date: str = None, end_date: str = None, category: str = None, transaction_type: str = None, limit: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT id, type, amount, category, description, date FROM transactions"
    conditions = []
    params = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if category:
        conditions.append("LOWER(category) = LOWER(?)")
        params.append(category)
    if transaction_type:
        conditions.append("type = ?")
        params.append(transaction_type)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date DESC, id DESC"
    if limit:
        query += f" LIMIT {limit}"

    try:
        cursor.execute(query, params)
        transactions = [dict(row) for row in cursor.fetchall()]
        return transactions
    except sqlite3.Error as e:
        print(f"Erro ao buscar transações: {e}")
        return []
    finally:
        conn.close()

def delete_transaction_by_id(transaction_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Erro ao excluir transação ID {transaction_id}: {e}")
        return False
    finally:
        conn.close()

def get_last_transaction_id(transaction_type: str = None, category: str = None) -> int | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT id FROM transactions"
    conditions = []
    params = []
    if transaction_type:
        conditions.append("type = ?")
        params.append(transaction_type)
    if category:
        conditions.append("LOWER(category) = LOWER(?)")
        params.append(category)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY date DESC, id DESC LIMIT 1" # Mais recente por data, depois por ID
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row['id'] if row else None
    except sqlite3.Error as e:
        print(f"Erro ao buscar último ID: {e}")
        return None
    finally:
        conn.close()

def delete_transactions_by_criteria(
    delete_all_flag: bool = False, # Renomeado para evitar conflito com keyword 'all'
    transaction_type: str = None, 
    category: str = None, 
    date_str: str = None,
    period_start_date: str = None,
    period_end_date: str = None
) -> int:
    if not any([delete_all_flag, transaction_type, category, date_str, period_start_date, period_end_date]):
        print("Nenhum critério de exclusão válido fornecido.")
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM transactions"
    conditions = []
    params = []

    if delete_all_flag:
        pass # Nenhuma condição, exclui tudo se delete_all_flag for True
    else:
        if transaction_type:
            conditions.append("type = ?")
            params.append(transaction_type)
        if category:
            conditions.append("LOWER(category) = LOWER(?)")
            params.append(category)
        if date_str:
            conditions.append("date = ?")
            params.append(date_str)
        else:
            if period_start_date:
                conditions.append("date >= ?")
                params.append(period_start_date)
            if period_end_date:
                conditions.append("date <= ?")
                params.append(period_end_date)
    
    if not delete_all_flag and not conditions:
        print("Critérios insuficientes para exclusão segura (não é delete_all e não há outros filtros).")
        return 0

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    try:
        print(f"DB: Executando exclusão: {query} com params {params}")
        cursor.execute(query, params)
        conn.commit()
        deleted_rows = cursor.rowcount
        print(f"DB: {deleted_rows} transações excluídas.")
        return deleted_rows
    except sqlite3.Error as e:
        print(f"DB: Erro ao excluir transações por critério: {e}")
        return 0
    finally:
        conn.close()

def update_transaction(
    transaction_id: int, 
    new_amount: float = None, 
    new_category: str = None, 
    new_description: str = None, 
    new_date_str: str = None,
    new_type: str = None
) -> bool:
    if not any([new_amount is not None, new_category, new_description is not None, new_date_str, new_type]):
        print("Nenhum campo fornecido para atualização.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    fields_to_update = []
    params_update = []

    if new_amount is not None:
        fields_to_update.append("amount = ?")
        params_update.append(float(new_amount))
    if new_category:
        fields_to_update.append("category = ?")
        params_update.append(new_category.lower().strip())
    if new_description is not None: # Permitir limpar a descrição
        fields_to_update.append("description = ?")
        params_update.append(new_description.strip())
    if new_date_str:
        try:
            datetime.strptime(new_date_str, '%Y-%m-%d')
            fields_to_update.append("date = ?")
            params_update.append(new_date_str)
        except ValueError:
            print(f"Formato de nova data inválido: {new_date_str}. Data não será atualizada.")
    if new_type and new_type.lower() in ["entrada", "saída"]:
        fields_to_update.append("type = ?")
        params_update.append(new_type.lower())
    
    if not fields_to_update:
        print("Nenhum campo válido para atualização.")
        conn.close()
        return False

    params_update.append(transaction_id)
    query = f"UPDATE transactions SET {', '.join(fields_to_update)} WHERE id = ?"
    
    try:
        print(f"DB: Executando atualização: {query} com params {params_update}")
        cursor.execute(query, params_update)
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"DB: Erro ao atualizar transação ID {transaction_id}: {e}")
        return False
    finally:
        conn.close()