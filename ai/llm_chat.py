import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Tentar importar GenerationConfig
try:
    # Tentativa 1: Direto de genai (comum em versões recentes como 0.5.0+)
    _GenerationConfig = genai.GenerationConfig
    print("INFO: Usando genai.GenerationConfig")
except AttributeError:
    # Tentativa 2: De google.generativeai.types (comum em algumas versões ou se genai global não tiver)
    try:
        from google.generativeai.types import GenerationConfig as _TypesGenerationConfig
        _GenerationConfig = _TypesGenerationConfig
        print("INFO: Usando GenerationConfig de google.generativeai.types")
    except ImportError:
        print("ERRO CRÍTICO: GenerationConfig não encontrado nem em 'genai' nem em 'google.generativeai.types'.")
        print("Verifique a instalação e a versão do SDK google-generativeai.")
        # Se não conseguir importar, não podemos continuar.
        raise ImportError("GenerationConfig não pôde ser importado. O aplicativo não pode iniciar.")


from utils.db import (
    add_transaction, get_transactions, 
    delete_transaction_by_id, get_last_transaction_id,
    delete_transactions_by_criteria, update_transaction
)
from utils.date_utils import parse_date_to_str, parse_period_to_dates
from ai.reports import generate_detailed_financial_report 
from chatbot.prompts import SYSTEM_PROMPT_FINANCEBOT

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME_CHAT = 'gemini-1.5-flash-latest' 
if API_KEY: genai.configure(api_key=API_KEY)
else: raise ValueError("GOOGLE_API_KEY não configurada.")

# --- Lógica das Funções de Backend (chamadas pelo Python após parsear JSON do LLM) ---
# (COLE AQUI TODAS AS SUAS FUNÇÕES _tool_... da versão anterior:
# _tool_add_financial_transaction, 
# _internal_query_summary, (renomeada de _tool_query_financial_transactions para clareza)
# _tool_actual_generate_report, (renomeada de _tool_generate_financial_summary_report)
# _internal_get_balance, (renomeada de _tool_get_account_balance)
# _tool_list_transactions,
# _tool_delete_financial_transactions,
# _tool_edit_financial_transaction
# )
def _tool_add_financial_transaction(transaction_type: str, amount: float, category: str, date_str: str, description: str = ""):
    parsed_date = parse_date_to_str(date_str)
    if not parsed_date: return {"status": "erro", "message_for_llm": f"Data inválida: '{date_str}'. Peça ao usuário para fornecer no formato DD/MM/AAAA ou YYYY-MM-DD."}
    transaction_type_lower = transaction_type.lower()
    if transaction_type_lower not in ["entrada", "saída"]: return {"status": "erro", "message_for_llm": f"Tipo de transação inválido: '{transaction_type}'. Use 'entrada' ou 'saída'."}
    final_category = category.lower().strip() if category and category.strip() else "diversos"
    if transaction_type_lower == "saída" and category.lower().strip() == "investimentos": final_category = "investimentos"
    elif transaction_type_lower == "entrada" and final_category == "diversos" and not (category and category.strip()):
         return {"status": "erro", "message_for_llm": "Para 'entrada', a categoria não pode ser 'diversos' por padrão. Por favor, pergunte a categoria ao usuário."}
    transaction_id = add_transaction(type=transaction_type_lower, amount=float(amount), category=final_category, description=(description.strip() if description else ""), date_str=parsed_date)
    if transaction_id: return {"status": "sucesso", "message_for_llm": "Transação registrada com sucesso.", "transaction_details": {"type": transaction_type_lower, "amount": float(amount), "category": final_category, "date": parsed_date, "description": (description.strip() if description else "")}}
    else: return {"status": "erro", "message_for_llm": "Ocorreu um erro ao tentar registrar a transação no banco de dados."}

def _internal_query_summary(period_description: str, transaction_type_filter: str = None, category_filter: str = None):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date and not end_date and period_description.lower() != "todo o período": return {"status": "erro", "message_for_llm": period_desc_for_user}
    if period_description.lower() == "todo o período": start_date, end_date = None, None
    db_type_filter = None
    if transaction_type_filter:
        if transaction_type_filter.lower() in ["entrada", "ganho"]: db_type_filter = "entrada"
        elif transaction_type_filter.lower() in ["saída", "gasto", "investimento"]: db_type_filter = "saída"
    db_category_filter = category_filter.lower().strip() if category_filter else None
    if transaction_type_filter and transaction_type_filter.lower() == "investimento":
        db_category_filter = "investimentos"; db_type_filter = "saída"
    transactions = get_transactions(start_date=start_date, end_date=end_date, category=db_category_filter, transaction_type=db_type_filter)
    if transaction_type_filter and transaction_type_filter.lower() == "gasto":
        transactions = [t for t in transactions if t['category'].lower() != 'investimentos']
    if not transactions: return {"status": "sucesso", "found_transactions": False, "message_for_llm": f"Nenhuma transação encontrada para os critérios em {period_desc_for_user}.", "period_for_llm": period_desc_for_user}
    total_amount = sum(t['amount'] for t in transactions); count = len(transactions)
    return {"status": "sucesso", "found_transactions": True, "total_amount": total_amount, "count": count, "period_details_for_user": period_desc_for_user}

def _tool_actual_generate_report(period_description: str):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date and not end_date and period_description.lower() != "todo o período": return {"status": "erro", "message_for_llm": period_desc_for_user}
    if period_description.lower() == "todo o período": start_date, end_date = None, None
    transactions = get_transactions(start_date=start_date, end_date=end_date)
    if not transactions: return {"status": "sucesso", "report_generated": False, "message_for_llm": f"Não há transações em {period_desc_for_user} para gerar um relatório.", "period_for_llm": period_desc_for_user}
    report_text = generate_detailed_financial_report(transactions, period_desc_for_user)
    return {"status": "sucesso", "report_generated": True, "report_text": report_text, "period_for_llm": period_desc_for_user}

def _internal_get_balance(period_description: str):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date and not end_date: 
        if period_description.lower() == "todo o período": start_date, end_date = None, None; period_desc_for_user = "todo o período"
        else: return {"status": "erro", "message_for_llm": period_desc_for_user}
    transactions = get_transactions(start_date=start_date, end_date=end_date)
    total_entradas = sum(t['amount'] for t in transactions if t['type'] == 'entrada')
    total_saidas = sum(t['amount'] for t in transactions if t['type'] == 'saída')
    saldo = total_entradas - total_saidas
    return {"status": "sucesso", "balance": saldo, "period_details_for_user": period_desc_for_user}

def _tool_list_transactions(period_description: str, transaction_type_filter: str = None, category_filter: str = None):
    start_date, end_date, period_desc_for_user = parse_period_to_dates(period_description)
    if not start_date and not end_date and period_description.lower() != "todo o período": return {"status": "erro", "message_for_llm": period_desc_for_user}
    if period_description.lower() == "todo o período": start_date, end_date = None, None
    db_type_filter, db_category_filter = None, category_filter.lower().strip() if category_filter else None
    if transaction_type_filter:
        tf_lower = transaction_type_filter.lower()
        if tf_lower in ["entrada", "ganho"]: db_type_filter = "entrada"
        elif tf_lower == "investimento": db_type_filter = "saída"; db_category_filter = "investimentos"
        elif tf_lower in ["saída", "gasto"]: db_type_filter = "saída"
    transactions_raw = get_transactions(start_date=start_date, end_date=end_date, category=db_category_filter, transaction_type=db_type_filter, limit=20)
    if transaction_type_filter and transaction_type_filter.lower() == "gasto":
        transactions_raw = [t for t in transactions_raw if t['category'].lower() != 'investimentos']
    if not transactions_raw: return {"status": "sucesso", "found_transactions": False, "message_for_llm": f"Nenhuma transação encontrada para {period_desc_for_user} com os filtros aplicados.", "period_for_llm": period_desc_for_user}
    listed_transactions = [{"display_index": i + 1, "transaction_id": t['id'], "summary_for_llm": f"{t['type'].capitalize()} de R${t['amount']:.2f} em '{t['category']}' no dia {t['date']}{f' - {t["description"]}' if t['description'] else ''}"} for i, t in enumerate(transactions_raw)]
    return {"status": "sucesso", "found_transactions": True, "count": len(listed_transactions), "period_for_llm": period_desc_for_user, "transactions_list_for_llm": listed_transactions}

def _tool_delete_financial_transactions(confirmation_received: bool, transaction_id_to_delete: int = None, delete_last: str = None, delete_all_in_category: str = None, delete_all_of_type: str = None, delete_by_date: str = None, delete_all_transactions: bool = False):
    if not confirmation_received: return {"status": "erro", "message_for_llm": "A exclusão foi cancelada porque a confirmação não foi dada pelo usuário."}
    num_deleted, action_description = 0, "Nenhuma ação de exclusão válida ou transação encontrada."
    if transaction_id_to_delete is not None:
        if delete_transaction_by_id(transaction_id_to_delete): num_deleted = 1; action_description = f"A transação com ID {transaction_id_to_delete} foi excluída."
        else: action_description = f"Não foi possível encontrar ou excluir a transação com ID {transaction_id_to_delete}."
    elif delete_last:
        type_f, cat_f = None, None; user_type = delete_last.lower()
        if user_type == 'gasto': type_f = 'saída' 
        elif user_type == 'entrada': type_f = 'entrada'
        elif user_type == 'investimento': type_f = 'saída'; cat_f = 'investimentos'
        elif user_type != 'qualquer': return {"status": "erro", "message_for_llm": f"Tipo '{delete_last}' inválido para 'delete_last'."}
        last_id = get_last_transaction_id(transaction_type=type_f, category=cat_f)
        if user_type == 'gasto' and last_id:
             temp_trans_list = get_transactions(limit=1) 
             if temp_trans_list and temp_trans_list[0]['id'] == last_id and temp_trans_list[0]['category'].lower() == 'investimentos':
                 action_description = f"O último registro de saída foi um investimento. Para excluir o último gasto não-investimento, por favor, liste e use o ID."; last_id = None 
        if last_id and delete_transaction_by_id(last_id): num_deleted = 1; action_description = f"A última transação ({delete_last}) foi excluída."
        elif last_id is None and "investimento" not in action_description : action_description = f"Nenhuma última transação ({delete_last}) foi encontrada para excluir."
    elif delete_all_in_category:
        cat_del = delete_all_in_category.lower()
        type_for_cat_delete = "saída" if cat_del == "investimentos" else None
        num_deleted = delete_transactions_by_criteria(category=cat_del, transaction_type=type_for_cat_delete)
        action_description = f"{num_deleted} transações da categoria '{delete_all_in_category}' foram excluídas."
    elif delete_all_of_type:
        dot_lower = delete_all_of_type.lower()
        if dot_lower in ['entrada', 'ganho']: num_deleted = delete_transactions_by_criteria(transaction_type='entrada'); action_description = f"{num_deleted} ganhos excluídos."
        elif dot_lower == 'gasto': all_s = get_transactions(transaction_type='saída'); ids_del = [t['id'] for t in all_s if t['category'].lower() != 'investimentos']; num_deleted = sum(1 for tid in ids_del if delete_transaction_by_id(tid)); action_description = f"{num_deleted} gastos (não investimentos) excluídos."
        elif dot_lower == 'investimento': num_deleted = delete_transactions_by_criteria(transaction_type='saída', category='investimentos'); action_description = f"{num_deleted} investimentos excluídos."
        elif dot_lower == 'saida_geral': num_deleted = delete_transactions_by_criteria(transaction_type='saída'); action_description = f"{num_deleted} saídas (gastos e investimentos) excluídas."
        else: return {"status": "erro", "message_for_llm": f"Tipo '{delete_all_of_type}' inválido para exclusão."}
    elif delete_by_date:
        parsed_date = parse_date_to_str(delete_by_date, False)
        if parsed_date: num_deleted = delete_transactions_by_criteria(date_str=parsed_date); action_description = f"{num_deleted} transações de {parsed_date} excluídas."
        else: action_description = f"Data '{delete_by_date}' inválida."
    elif delete_all_transactions: num_deleted = delete_transactions_by_criteria(delete_all_flag=True); action_description = f"ATENÇÃO: TODAS AS {num_deleted} TRANSAÇÕES FORAM EXCLUÍDAS."
    return {"status": "sucesso", "num_deleted": num_deleted, "message_for_llm": action_description}

def _tool_edit_financial_transaction(confirmation_received: bool, transaction_id_to_edit: int = None, edit_last: str = None, category_context_for_last: str = None, new_amount: float = None, new_category: str = None, new_date_str: str = None, new_description: str = None, new_type: str = None):
    if not confirmation_received: return {"status": "erro", "message_for_llm": "Edição cancelada. Confirmação não dada."}
    target_id = transaction_id_to_edit
    if not target_id and edit_last:
        type_f, cat_f = None, category_context_for_last.lower().strip() if category_context_for_last else None
        el_lower = edit_last.lower()
        if el_lower == 'gasto': type_f = 'saída'
        elif el_lower == 'entrada': type_f = 'entrada'
        elif el_lower == 'investimento': type_f = 'saída'; cat_f = 'investimentos'
        else: return {"status": "erro", "message_for_llm": f"Tipo '{edit_last}' inválido para 'edit_last'."}
        target_id = get_last_transaction_id(transaction_type=type_f, category=cat_f)
        if not target_id: return {"status": "erro", "message_for_llm": f"Nenhuma última transação ({edit_last}{f' de {cat_f}' if cat_f else ''}) encontrada."}
    if not target_id: return {"status": "erro", "message_for_llm": "ID da transação para editar não especificado."}
    parsed_new_date = parse_date_to_str(new_date_str, False) if new_date_str else None
    if new_date_str and not parsed_new_date: return {"status": "erro", "message_for_llm": f"Nova data '{new_date_str}' inválida."}
    success = update_transaction(transaction_id=target_id, new_amount=new_amount, new_category=new_category, new_description=new_description, new_date_str=parsed_new_date, new_type=new_type)
    if success: return {"status": "sucesso", "message_for_llm": f"Transação ID {target_id} atualizada."}
    else: return {"status": "erro", "message_for_llm": f"Falha ao atualizar transação ID {target_id}."}


class ChatManager:
    def __init__(self):
        self.model = genai.GenerativeModel(
            MODEL_NAME_CHAT,
            system_instruction=SYSTEM_PROMPT_FINANCEBOT,
            tools=None # NENHUMA FERRAMENTA EXPLÍCITA PASSADA PARA O MODELO
        )
        self.generation_config = _GenerationConfig(temperature=0.5) 
        self.chat_history = [] 

    def _add_to_history(self, role: str, text: str): # Simplificado
        self.chat_history.append({'role': role, 'parts': [{'text': text}]})

    def _handle_json_action(self, json_data: dict) -> str:
        action = json_data.get("action")
        params = json_data.get("parameters", {})
        confirmation = json_data.get("user_confirmation_received", False) 

        print(f"Python: Ação JSON: {action}, Params: {params}, Confirmado: {confirmation}")
        response_message = f"Ação '{action}' não reconhecida ou não implementada."

        if action == "add_transaction":
            result = _tool_add_financial_transaction(**params)
            response_message = result.get("message_for_llm", "Erro ao adicionar.") if result.get("status") == "erro" else f"{result.get('message_for_llm', 'Adicionado.')} ✅ Confira seu dashboard!"
        elif action == "list_transactions":
            result = _tool_list_transactions(**params)
            if result.get("status") == "sucesso" and result.get("found_transactions"):
                response_text = f"Encontrei {result['count']} transações para {result['period_for_llm']}:\n"
                for item in result['transactions_list_for_llm']: response_text += f"{item['display_index']}. {item['summary_for_llm']} (ID: {item['transaction_id']})\n"
                response_message = response_text
            else: response_message = result.get("message_for_llm", "Nenhuma transação encontrada.")
        elif action == "delete_transactions":
            if not confirmation and not params.get("transaction_id_to_delete"): # Para deleções em massa, a confirmação no JSON é vital
                response_message = "A exclusão em massa precisa de confirmação explícita. Você tem certeza?"
            else: # Para ID específico, ou se confirmation=true
                params_with_confirmation = {"confirmation_received": confirmation or bool(params.get("transaction_id_to_delete")), **params}
                result = _tool_delete_financial_transactions(**params_with_confirmation)
                response_message = result.get("message_for_llm", "Erro ao excluir.") + (" ✅ Confira seu dashboard!" if result.get("num_deleted",0) > 0 else "")
        elif action == "edit_transaction":
            if not confirmation:
                response_message = "A edição precisa de confirmação. Você tem certeza dos detalhes?"
            else:
                params_with_confirmation = {"confirmation_received": confirmation, **params}
                result = _tool_edit_financial_transaction(**params_with_confirmation)
                response_message = result.get("message_for_llm", "Erro ao editar.") + " ✅ Confira seu dashboard!"
        elif action == "generate_report":
            result = _tool_actual_generate_report(**params)
            response_message = result.get("report_text") if result.get("status") == "sucesso" and result.get("report_generated") else result.get("message_for_llm", "Erro ao gerar relatório.")
            if result.get("status") == "sucesso" and result.get("report_generated"):
                 response_message = f"Gerando relatório para {result['period_for_llm']}...\n\n{response_message}\n\n📊 Aqui está o resumo. Veja mais no dashboard!"
        
        return response_message

    def send_message(self, user_message: str) -> str:
        self._add_to_history(role='user', text=user_message)
        try:
            # Chamada ao LLM SEM o parâmetro 'tools' explícito para DB actions
            response = self.model.generate_content(
                self.chat_history,
                generation_config=self.generation_config
            )
            
            llm_response_text = ""
            if response.candidates and response.candidates[0].content.parts and hasattr(response.candidates[0].content.parts[0], 'text'):
                llm_response_text = response.candidates[0].content.parts[0].text
            else:
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                    llm_response_text = f"Minha resposta foi bloqueada. Razão: {getattr(response.prompt_feedback, 'block_reason_message', response.prompt_feedback.block_reason)}"
                else:
                    llm_response_text = "Desculpe, não consegui gerar uma resposta."

            print(f"LLM Respondeu (bruto): '{llm_response_text}'")

            try:
                json_str = llm_response_text.strip()
                if json_str.startswith("```json"): json_str = json_str[7:-3].strip()
                
                if json_str.startswith("{") and json_str.endswith("}"):
                    action_data = json.loads(json_str)
                    if "action" in action_data:
                        print(f"JSON de ação detectado: {action_data['action']}")
                        python_response = self._handle_json_action(action_data)
                        self._add_to_history(role='model', text=python_response)
                        return python_response
            except json.JSONDecodeError:
                print(f"Resposta do LLM não era JSON de ação.")
            except Exception as e_json_proc:
                print(f"Erro ao processar possível JSON: {e_json_proc}")
            
            self._add_to_history(role='model', text=llm_response_text)
            return llm_response_text

        except Exception as e:
            print(f"Erro GERAL em send_message: {e}")
            import traceback; traceback.print_exc()
            if self.chat_history and self.chat_history[-1]['role'] == 'user': self.chat_history.pop()
            return "Desculpe, um erro crítico ocorreu."