# finance-bot/ai/llm_chat.py (VERSÃO DA SUA PERGUNTA ORIGINAL PARA O CHATBOT CONVERSACIONAL)
import google.generativeai as genai
# Esta linha abaixo é a que provavelmente causará erro com SDK 0.8.5 se os tipos não estiverem lá
from google.generativeai.types import GenerationConfig, FunctionDeclaration, Tool 
import os
from dotenv import load_dotenv

from utils.db import add_transaction, get_transactions
from utils.date_utils import parse_date_to_str, parse_period_to_dates
from ai.reports import generate_detailed_financial_report 
from chatbot.prompts import SYSTEM_PROMPT_FINANCEBOT

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME_CHAT = 'gemini-1.5-flash-latest' 

if API_KEY: genai.configure(api_key=API_KEY)
else: raise ValueError("GOOGLE_API_KEY não configurada.")

# --- Definição das Ferramentas (usando FunctionDeclaration e Tool importados) ---
add_financial_transaction_tool = FunctionDeclaration( name="add_financial_transaction", description="Registra uma nova transação financeira (gasto/saída ou receita/entrada).", parameters={ "type": "object", "properties": { "transaction_type": {"type": "string", "description": "O tipo de transação, deve ser 'entrada' ou 'saída'."}, "amount": {"type": "number", "description": "O valor numérico da transação."}, "category": {"type": "string", "description": "A categoria da transação (ex: alimentação, salário, transporte, lazer)."}, "date_str": {"type": "string", "description": "A data da transação. O LLM deve converter 'hoje', 'ontem' ou datas como '15/07' para o formato YYYY-MM-DD."}, "description": {"type": "string", "description": "Uma descrição opcional para a transação."} }, "required": ["transaction_type", "amount", "category", "date_str"] } )
query_financial_transactions_tool = FunctionDeclaration( name="query_financial_transactions", description="Busca e resume transações financeiras com base em filtros.", parameters={ "type": "object", "properties": { "transaction_type_filter": {"type": "string", "description": "Filtrar por 'entrada' ou 'saída'."}, "category_filter": {"type": "string", "description": "Filtrar por uma categoria específica. Opcional."}, "period_description": {"type": "string", "description": "A descrição do período."} }, "required": ["period_description"] } )
generate_financial_summary_report_tool = FunctionDeclaration( name="generate_financial_summary_report", description="Gera um relatório financeiro resumido.", parameters={ "type": "object", "properties": { "period_description": {"type": "string", "description": "A descrição do período para o relatório."} }, "required": ["period_description"] } )
get_account_balance_tool = FunctionDeclaration( name="get_account_balance", description="Calcula e retorna o saldo financeiro.", parameters={ "type": "object", "properties": { "period_description": {"type": "string", "description": "A descrição do período para o cálculo do saldo."} }, "required": ["period_description"] } )
FINANCE_TOOLS = Tool(function_declarations=[ add_financial_transaction_tool, query_financial_transactions_tool, generate_financial_summary_report_tool, get_account_balance_tool ])

# --- Lógica das Funções de Ferramenta (como definido antes) ---
def _tool_add_financial_transaction(transaction_type: str, amount: float, category: str, date_str: str, description: str = ""):
    parsed_date = parse_date_to_str(date_str)
    if not parsed_date: return {"status": "erro", "message": f"Data inválida: '{date_str}'."}
    if transaction_type.lower() not in ["entrada", "saída"]: return {"status": "erro", "message": f"Tipo inválido: '{transaction_type}'."}
    transaction_id = add_transaction(type=transaction_type.lower(), amount=float(amount), category=category.lower().strip(), description=(description.strip() if description else ""), date_str=parsed_date)
    if transaction_id: return {"status": "sucesso", "message": "Registrado.", "transaction_details": {"id": transaction_id, "type": transaction_type.lower(), "amount": float(amount), "category": category.lower().strip(), "date": parsed_date, "description": (description.strip() if description else "")}}
    else: return {"status": "erro", "message": "Erro no DB."}

def _tool_query_financial_transactions(period_description: str, transaction_type_filter: str = None, category_filter: str = None):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date or not end_date: return {"status": "erro", "message": period_desc_for_user}
    transactions = get_transactions(start_date=start_date, end_date=end_date, category=category_filter.lower().strip() if category_filter else None, transaction_type=transaction_type_filter.lower() if transaction_type_filter else None)
    if not transactions: return {"status": "sucesso", "found_transactions": False, "message": "Nenhuma transação encontrada.", "period_details_for_user": period_desc_for_user, "category_filter_used": category_filter, "type_filter_used": transaction_type_filter}
    total_amount = sum(t['amount'] for t in transactions); count = len(transactions)
    return {"status": "sucesso", "found_transactions": True, "total_amount": total_amount, "count": count, "period_details_for_user": period_desc_for_user, "category_filter_used": category_filter, "type_filter_used": transaction_type_filter}

def _tool_generate_financial_summary_report(period_description: str):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date or not end_date: return {"status": "erro", "message": period_desc_for_user}
    transactions = get_transactions(start_date=start_date, end_date=end_date)
    if not transactions: return {"status": "sucesso", "report_generated": False, "message": "Não há transações.", "period_details_for_user": period_desc_for_user}
    report_text = generate_detailed_financial_report(transactions, period_desc_for_user)
    return {"status": "sucesso", "report_generated": True, "report_text": report_text, "period_details_for_user": period_desc_for_user}

def _tool_get_account_balance(period_description: str):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date or not end_date:
        if period_description.lower() == "todo o período" or not period_description: start_date, end_date = None, None; period_desc_for_user = "todo o período"
        else: return {"status": "erro", "message": period_desc_for_user}
    transactions = get_transactions(start_date=start_date, end_date=end_date)
    total_entradas = sum(t['amount'] for t in transactions if t['type'] == 'entrada')
    total_saidas = sum(t['amount'] for t in transactions if t['type'] == 'saída')
    saldo = total_entradas - total_saidas
    return {"status": "sucesso", "balance": saldo, "total_income": total_entradas, "total_expenses": total_saidas, "period_details_for_user": period_desc_for_user}

AVAILABLE_TOOL_FUNCTIONS = {"add_financial_transaction": _tool_add_financial_transaction, "query_financial_transactions": _tool_query_financial_transactions, "generate_financial_summary_report": _tool_generate_financial_summary_report, "get_account_balance": _tool_get_account_balance}

class ChatManager:
    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME_CHAT, system_instruction=SYSTEM_PROMPT_FINANCEBOT, tools=[FINANCE_TOOLS])
        self.generation_config = GenerationConfig(temperature=0.7)
        self.chat = self.model.start_chat(history=[]) # Esta linha usa start_chat

    def send_message(self, user_message: str) -> str:
        try:
            response = self.chat.send_message(user_message, generation_config=self.generation_config)
            # Esta parte do loop é a que precisa ser compatível com a forma como a SDK 0.8.5
            # retorna function_call e como ela espera function_response.
            # A versão original usava genai.Part para a resposta da função.
            # Se genai.Part não existir, isso falhará.
            while response.candidates[0].content.parts[0].function_call.name:
                function_call_part = response.candidates[0].content.parts[0].function_call
                tool_name = function_call_part.name
                tool_args = dict(function_call_part.args)
                print(f"LLM: {tool_name}({tool_args})")
                if tool_name in AVAILABLE_TOOL_FUNCTIONS:
                    tool_response_data = AVAILABLE_TOOL_FUNCTIONS[tool_name](**tool_args)
                    print(f"Tool: {tool_response_data}")
                    # A linha abaixo (genai.Part) é um ponto provável de falha com SDK 0.8.5 se genai.Part não existir
                    response = self.chat.send_message(
                        genai.Part(function_response={'name': tool_name, 'response': tool_response_data}),
                        generation_config=self.generation_config
                    )
                else:
                    print(f"Erro: Ferramenta desconhecida '{tool_name}'.")
                    response = self.chat.send_message(
                        genai.Part(function_response={'name': tool_name, 'response': {"status": "erro", "message": "Ferramenta não implementada."}}),
                        generation_config=self.generation_config
                    )
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            print(f"Erro em send_message: {e}")
            import traceback
            traceback.print_exc()
            return "Transação registrada"