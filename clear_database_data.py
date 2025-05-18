import sqlite3
import os
import sys

# Determinar o caminho para a pasta raiz do projeto 'finance-bot'
# Este script deve estar na pasta raiz 'finance-bot'
try:
    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT_DIR = CURRENT_SCRIPT_DIR 
    DATABASE_FILE = os.path.join(PROJECT_ROOT_DIR, 'data', 'transactions.db')
except NameError:
    # Fallback se __file__ não estiver definido (ex: alguns interpretadores interativos)
    # Assume que o script está sendo executado da pasta raiz do projeto
    PROJECT_ROOT_DIR = os.getcwd()
    DATABASE_FILE = os.path.join(PROJECT_ROOT_DIR, 'data', 'transactions.db')


def clear_all_transactions():
    """Apaga todas as linhas da tabela 'transactions'."""
    
    print(f"Tentando acessar o banco de dados em: {DATABASE_FILE}")

    if not os.path.exists(DATABASE_FILE):
        print(f"AVISO: Arquivo do banco de dados '{os.path.basename(DATABASE_FILE)}' não encontrado em '{os.path.dirname(DATABASE_FILE)}'.")
        print("Nada para limpar. O banco de dados será criado na próxima execução do aplicativo.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';")
        if cursor.fetchone() is None:
            print(f"AVISO: Tabela 'transactions' não encontrada no banco de dados.")
            print("Nada para limpar.")
            return

        cursor.execute("SELECT COUNT(*) FROM transactions")
        count_before = cursor.fetchone()[0]
        if count_before == 0:
            print("A tabela 'transactions' já está vazia. Nenhuma ação necessária.")
            return

        print(f"\nA tabela 'transactions' atualmente contém {count_before} registro(s).")
        confirm = input(f"TEM CERTEZA que deseja apagar TODOS OS {count_before} dados de transações? Esta ação é IRREVERSÍVEL. (digite 'sim' para confirmar): ")
        
        if confirm.lower() == 'sim':
            print(f"\nExcluindo {count_before} transações...")
            cursor.execute("DELETE FROM transactions")
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM transactions")
            count_after = cursor.fetchone()[0]
            
            if count_after == 0:
                print(f"Todas as {count_before} transações foram excluídas com sucesso. A tabela 'transactions' agora está vazia.")
                # Opcional: Resetar a sequência do AUTOINCREMENT
                # try:
                #     cursor.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
                #     conn.commit()
                #     print("Sequência de ID da tabela 'transactions' resetada (novos IDs começarão de 1).")
                # except sqlite3.Error as seq_e:
                #     print(f"Aviso: Não foi possível resetar a sequência de ID (pode não existir ou erro): {seq_e}")
            else:
                print(f"ERRO: A exclusão parece ter falhado. Ainda existem {count_after} registros na tabela.")
        else:
            print("\nOperação de exclusão cancelada pelo usuário.")
            
    except sqlite3.Error as e:
        print(f"Erro ao interagir com o banco de dados: {e}")
    except Exception as ex:
        print(f"Um erro inesperado ocorreu: {ex}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == '__main__':
    clear_all_transactions()
    # Pausa no Windows para que o usuário possa ver a saída antes que o terminal feche
    if os.name == 'nt':
        input("\nPressione Enter para sair...")
