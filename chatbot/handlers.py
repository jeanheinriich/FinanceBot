# finance-bot/chatbot/handlers.py
from ai.llm_chat import ChatManager 

_chat_manager_instance = None

def get_chat_manager():
    global _chat_manager_instance
    if _chat_manager_instance is None:
        _chat_manager_instance = ChatManager()
    return _chat_manager_instance

def handle_message(user_input: str) -> str:
    manager = get_chat_manager()
    if not user_input.strip():
        return "Por favor, diga algo."
    bot_response = manager.send_message(user_input)
    return bot_response

if __name__ == '__main__':
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from utils.db import init_db
    init_db()
    print("Iniciando FinanceBot com IA Conversacional (Ctrl+C para sair)...")
    # Para modo interativo no __main__
    while True:
        try:
            user_msg = input("Você: ")
            if user_msg.lower() == 'sair':
                print("FinanceBot: Até logo!")
                break
            response = handle_message(user_msg)
            print(f"FinanceBot: {response}")
        except KeyboardInterrupt:
            print("\nFinanceBot: Encerrando...")
            break
        except Exception as e_main:
            print(f"Erro inesperado no loop principal: {e_main}")
            break