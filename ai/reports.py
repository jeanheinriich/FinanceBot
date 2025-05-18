# finance-bot/ai/reports.py
import google.generativeai as genai
import os
import pandas as pd
from dotenv import load_dotenv
from chatbot.prompts import REPORT_PROMPT_TEMPLATE_FOR_GENERATION_TOOL # Importa o template correto

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME_REPORTS = 'gemini-1.5-flash-latest' 

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("AVISO: GOOGLE_API_KEY não configurada para ai.reports. A geração de relatórios por IA não funcionará.")

def _format_transactions_for_report_ia(transactions_list: list) -> str: # Renomeado no seu exemplo
    """Formata a lista de transações para ser enviada à IA para geração de relatório."""
    if not transactions_list:
        return "Nenhuma transação encontrada para este período."

    df = pd.DataFrame(transactions_list)
    df['amount'] = pd.to_numeric(df['amount'])

    summary_lines = []
    for _, row in df.iterrows():
        description_part = f" - {row['description']}" if row['description'] else ""
        summary_lines.append(
            f"- {row['date']}: {row['type']} de R${row['amount']:.2f} ({row['category']}){description_part}"
        )
    return "\n".join(summary_lines)

def generate_detailed_financial_report(transactions_list: list, period_description: str) -> str: # Nome da função no seu exemplo
    """
    Gera um relatório financeiro detalhado usando IA do Google com base nas transações fornecidas.
    Esta função é chamada pela ferramenta do LLM, não diretamente pelo handler.
    """
    if not API_KEY:
        return "Erro: API Key do Google não configurada. Não é possível gerar o relatório detalhado."
    if not transactions_list:
        return f"Não há transações para o período de {period_description} para gerar um relatório detalhado."

    transactions_summary = _format_transactions_for_report_ia(transactions_list) # Usa a função renomeada

    prompt = REPORT_PROMPT_TEMPLATE_FOR_GENERATION_TOOL.format(
        period_description=period_description,
        transactions_summary=transactions_summary
    )

    try:
        model = genai.GenerativeModel(MODEL_NAME_REPORTS)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Erro ao gerar relatório detalhado com IA: {e}")
        return f"Desculpe, ocorreu um erro ao tentar gerar o relatório detalhado: {e}"

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.db import get_transactions, init_db, add_transaction
    
    init_db()
    
    if not get_transactions(start_date="2024-07-01", end_date="2024-07-31"):
        print("Adicionando transações de exemplo para teste de relatório...")
        add_transaction("saída", 50.0, "alimentação", "Supermercado X", "2024-07-20")
        add_transaction("entrada", 1500.0, "salário", "Pagamento mensal", "2024-07-05")
        add_transaction("saída", 100.0, "contas", "Energia", "2024-07-10")

    sample_transactions = get_transactions(start_date="2024-07-01", end_date="2024-07-31")
    if sample_transactions:
        report = generate_detailed_financial_report(sample_transactions, "Julho de 2024")
        print("\n--- Relatório Financeiro Detalhado (Julho 2024) ---")
        print(report)
    else:
        print("Nenhuma transação de exemplo encontrada para gerar relatório detalhado.")