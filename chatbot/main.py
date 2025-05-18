# finance-bot/chatbot/main.py
from chatbot.handlers import handle_message, get_chat_manager # Adicionar get_chat_manager
from utils.db import init_db
import os # Para verificar se é a primeira execução

# Arquivo para marcar a primeira execução
FIRST_RUN_FLAG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', '.first_run_completed')

def print_initial_greeting():
    """Imprime a saudação inicial completa."""
    greeting = """
Olá! 👋
Sou o FinanceBot, seu assistente financeiro pessoal. 
Posso registrar seus gastos e receitas, mostrar saldos, gerar relatórios e te ajudar a manter as finanças organizadas!

Você pode experimentar me dizer algo como:
  ➡️ 'gastei 50 reais com alimentação hoje'
  ➡️ 'recebi meu salário ontem de R$2000'
  ➡️ 'quanto gastei com lazer este mês?'
  ➡️ 'me dá um relatório do mês passado'

💡 E o melhor: todos os seus dados ficam disponíveis em um painel visual interativo.
Você pode acessar seu dashboard financeiro aqui: http://localhost:8501 
(Lembre-se de rodar 'streamlit run finance-bot/dashboard/main.py' em outro terminal se ainda não o fez!)

Como posso te ajudar a começar?
"""
    print(f"FinanceBot: {greeting}")

def run_chatbot_cli():
    """Inicia o chatbot no modo de linha de comando."""
    init_db() # Garante que o banco de dados e a tabela existam
    
    # Garante que o diretório data exista para o arquivo de flag
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'data'), exist_ok=True)

    if not os.path.exists(FIRST_RUN_FLAG_FILE):
        print_initial_greeting()
        # Marca que a primeira saudação foi exibida
        with open(FIRST_RUN_FLAG_FILE, 'w') as f:
            f.write('completed')
    else:
        # Saudação mais curta para execuções subsequentes, ou deixar o LLM responder a um "Olá"
        # Para manter a consistência da "personalidade", vamos deixar o LLM se apresentar
        # se o usuário iniciar com uma saudação.
        print("FinanceBot: Olá! Sou o FinanceBot. Como posso te ajudar hoje?")


    # Certifique-se de que o ChatManager é inicializado para carregar o system prompt
    get_chat_manager() 

    while True:
        user_input = input("Você: ")
        if user_input.lower() == 'sair':
            # Usar o LLM para a despedida, se desejado, ou uma mensagem fixa.
            # Para consistência com o system prompt:
            print(f"FinanceBot: {handle_message('tchau, obrigado')}") 
            # Ou a mensagem fixa:
            # print("FinanceBot: Tudo certo por aqui! Qualquer coisa, é só me chamar de novo. Te desejo ótimas finanças! 💸📊")
            break
        
        response = handle_message(user_input)
        print(f"FinanceBot: {response}")

if __name__ == '__main__':
    # Adicionar o diretório raiz ao sys.path se estiver executando este arquivo diretamente:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # Sobe um nível para finance-bot
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    run_chatbot_cli()