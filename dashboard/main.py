import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
import sys
import os
import matplotlib.colors as mcolors

# Adiciona o diretório raiz do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.db import get_transactions, init_db
from ai.reports import generate_detailed_financial_report
from chatbot.handlers import handle_message, get_chat_manager

# --- Inicialização ---
init_db()
st.set_page_config(layout="wide", page_title="FinanceBot")
chat_manager = get_chat_manager()

if "messages" not in st.session_state:
    st.session_state.messages = []
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ALTERAÇÃO 1: Nova mensagem inicial do FinanceBot
    # ------------------------------------------------------------------------------
    welcome_message = (
        "Olá! 👋 Eu sou o FinanceBot, seu assistente financeiro inteligente. "
        "Estou aqui para te ajudar a registrar seus gastos, ganhos e investimentos, "
        "além de gerar relatórios e gráficos para facilitar sua organização.\n\n"
        "Para começar, me diga algo como: 'Gastei 30 reais com mercado hoje' ou "
        "'Recebi 1000 de salário'. Vamos juntos melhorar sua vida financeira!"
    )
    st.session_state.messages.append({"role": "assistant", "content": welcome_message, "type": "text"})
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# --- Função para escurecer cor (como antes) ---
def darken_color(hex_color, amount=0.1):
    try:
        rgb = mcolors.hex2color(hex_color)
        darkened_rgb = tuple(max(0, c - amount) for c in rgb)
        return mcolors.to_hex(darkened_rgb)
    except ValueError: return hex_color

# --- Paleta de Cores (como antes) ---
COLOR_BACKGROUND = "#EAF8EC"
COLOR_CARD_CHAT_CONTAINER_BG = "#F6FCF7"
COLOR_TEXT_MAIN = "#1A3C2C"
COLOR_HIGHLIGHT_GREEN = "#3CA96C"
COLOR_TEXT_SECONDARY = "#4E6E5D"
COLOR_BOT_BUBBLE_BG = "#D9F1E1"
COLOR_USER_BUBBLE_BG = COLOR_HIGHLIGHT_GREEN
COLOR_USER_BUBBLE_TEXT = "#FFFFFF"
COLOR_HIGHLIGHT_GREEN_DARK = darken_color(COLOR_HIGHLIGHT_GREEN, 0.1)
COLOR_SCROLLBAR_THUMB = "#A0DAB0" 
COLOR_SCROLLBAR_TRACK = "#E0E0E0" 
COLOR_CARD_BORDER = "#e0e0e0" 
COLOR_CARD_SHADOW = "0 2px 10px rgba(0,0,0,0.07)"
COLOR_GASTOS_RED_PIE = "#E57777" 
COLOR_INVESTIMENTOS_BLUEGREEN_PIE = "#64A3A8"
COLOR_LIGHT_GREEN_INDICATOR = "#A0DAB0"


# --- CSS Personalizado (SEU CSS ATUAL - SEM ALTERAÇÕES AQUI) ---
# MANTENHA SEU BLOCO CSS <style>...</style> EXATAMENTE COMO ESTÁ AQUI
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, .stApp {{
            height: 100%; margin: 0; padding: 0;
            background-color: {COLOR_BACKGROUND} !important;
            font-family: 'Inter', sans-serif;
            color: {COLOR_TEXT_MAIN};
        }}
        .stApp {{ overflow: hidden; }}

        .main .block-container {{
            padding: 1.5rem !important; 
            max-width: 100%;
            height: calc(100vh - 3rem); 
            display: flex; 
        }}
        
        div[data-testid="stHorizontalBlock"] {{ 
            height: 100%;
            gap: 24px; 
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid^="stVerticalBlock"] {{
            height: 100%; 
            display: flex;
            flex-direction: column;
            overflow: hidden; 
        }}

        .card-style {{
            background-color: {COLOR_CARD_CHAT_CONTAINER_BG};
            border-radius: 12px;
            padding: 20px;
            border: 1px solid {COLOR_CARD_BORDER};
            box-shadow: {COLOR_CARD_SHADOW};
        }}

        .chat-outer-container {{ /* O card branco do chat */
            display: flex;
            flex-direction: column;
            height: 100%; 
        }}

        .chatbot-header {{ display: flex; align-items: center; margin-bottom: 16px; flex-shrink: 0; }}
        .chatbot-avatar {{ font-size: 28px; margin-right: 10px; color: {COLOR_HIGHLIGHT_GREEN}; }}
        .chatbot-title {{ color: {COLOR_TEXT_MAIN}; font-size: 1.6em; font-weight: 600; margin: 0; }}

        .chat-messages-area {{
            overflow-y: auto; 
            height: calc(100% - 120px); 
            padding-right: 8px; 
            margin-bottom: 10px;
        }}
        .chat-messages-area::-webkit-scrollbar {{ width: 8px; }}
        .chat-messages-area::-webkit-scrollbar-track {{ background: {COLOR_SCROLLBAR_TRACK}; border-radius: 10px; }}
        .chat-messages-area::-webkit-scrollbar-thumb {{ background-color: {COLOR_SCROLLBAR_THUMB}; border-radius: 10px; border: 2px solid {COLOR_SCROLLBAR_TRACK}; }}
        .chat-messages-area {{ scrollbar-width: thin; scrollbar-color: {COLOR_SCROLLBAR_THUMB} {COLOR_SCROLLBAR_TRACK}; }}

        .message-wrapper {{ display: flex; margin-bottom: 12px; }}
        .message-bubble {{ padding: 10px 15px; border-radius: 18px; max-width: 85%; word-wrap: break-word; line-height: 1.45; font-size: 0.92em; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }}
        .user-message {{ justify-content: flex-end; }}
        .user-message .message-bubble {{ background-color: {COLOR_USER_BUBBLE_BG}; color: {COLOR_USER_BUBBLE_TEXT}; border-bottom-right-radius: 5px; }}
        .assistant-message {{ justify-content: flex-start; }}
        .assistant-message .message-bubble {{ background-color: {COLOR_BOT_BUBBLE_BG}; color: {COLOR_TEXT_MAIN}; border-bottom-left-radius: 5px; }}
        .quick-reply-container {{ text-align: right; margin-top: 8px; padding-right: 5%; }}
        .quick-reply-button {{ background-color: {COLOR_CARD_CHAT_CONTAINER_BG}; color: {COLOR_TEXT_MAIN}; border: 1px solid {COLOR_HIGHLIGHT_GREEN}; border-radius: 20px; padding: 6px 18px; margin-left: 8px; cursor: pointer; font-weight: 500; font-size: 0.9em; display: inline-block; }}
        .quick-reply-button:hover {{ background-color: {COLOR_HIGHLIGHT_GREEN}; color: white; }}

        .stChatInputContainer {{
             flex-shrink: 0; 
             padding-top: 10px; 
        }}
        .stChatInputContainer > div {{
            background-color: transparent !important; 
            border-radius: 12px; padding: 0px !important; border: none !important; box-shadow: none !important;
        }}
        .stChatInputContainer textarea {{
            border-radius: 12px !important; background-color: white !important; 
            border: 1px solid {COLOR_CARD_BORDER} !important; color: {COLOR_TEXT_MAIN} !important;
            min-height: 42px !important; font-size: 0.95em;
            padding-left: 15px; padding-right: 45px; 
        }}
        .stChatInputContainer div[data-baseweb="input"] {{ position: relative; }}
        .stChatInputContainer button[data-testid="stChatInputSubmitButton"] {{ 
            background-color: {COLOR_HIGHLIGHT_GREEN} !important; border-radius: 10px !important;
            width: 36px; height: 36px; padding: 6px !important;
            position: absolute; right: 6px; bottom: 3px; 
        }}
        .stChatInputContainer button[data-testid="stChatInputSubmitButton"] svg {{ fill: white !important; }}
        .stChatInputContainer button[data-testid="stChatInputSubmitButton"]:hover {{ background-color: {COLOR_HIGHLIGHT_GREEN_DARK} !important; }}

        .dashboard-column-wrapper {{ padding-left: 12px; height: 100%; overflow-y: auto; display: flex; flex-direction: column;}}
        h2 {{ color: {COLOR_TEXT_MAIN}; font-weight: 600; }}
        h3 {{ color: {COLOR_TEXT_SECONDARY}; font-size: 1.1em; font-weight: 500; margin-bottom: 10px; }}
        .dashboard-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
        .dashboard-card .card-title {{ color: {COLOR_TEXT_SECONDARY}; font-size: 1em; font-weight: 500; margin-bottom: 6px; }}
        .dashboard-card .card-value {{ color: {COLOR_TEXT_MAIN}; font-size: 2em; font-weight: 600; }}
        .graph-card .graph-title {{ color: {COLOR_TEXT_MAIN}; text-align: left; font-size: 1.2em; font-weight: 600; margin-bottom: 16px; }}
        .custom-legend {{ padding-top: 10px; }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 10px; font-size: 0.95em; }}
        .legend-color-dot {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 10px; }}
        .legend-text {{ color: {COLOR_TEXT_SECONDARY}; font-weight: 400; }}
        .legend-percentage {{ margin-left: auto; color: {COLOR_TEXT_MAIN}; font-weight: 600; }}
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares (sem mudanças) ---
def load_dashboard_data(start_date_str=None, end_date_str=None, selected_categories=None, available_categories_list=None):
    transactions = get_transactions(start_date=start_date_str, end_date=end_date_str)
    df = pd.DataFrame(transactions)
    if not df.empty:
        df['amount'] = pd.to_numeric(df['amount'])
        df['date'] = pd.to_datetime(df['date'])
        if selected_categories and available_categories_list and len(selected_categories) < len(available_categories_list):
            df = df[df['category'].isin(selected_categories)]
    else:
        df = pd.DataFrame(columns=['id', 'type', 'amount', 'category', 'description', 'date'])
    return df

def calculate_summary(df):
    if not df.empty:
        total_receitas = df[df['type'] == 'entrada']['amount'].sum()
        # Gastos são todas as saídas exceto a categoria 'investimentos' (se existir)
        total_despesas_operacionais = df[(df['type'] == 'saída') & (df['category'].str.lower() != 'investimentos')]['amount'].sum()
        total_investimentos = df[(df['type'] == 'saída') & (df['category'].str.lower() == 'investimentos')]['amount'].sum()
        # Saldo considera Ganhos - (Gastos Operacionais + Investimentos)
        saldo_geral = total_receitas - (total_despesas_operacionais + total_investimentos)
    else:
        total_receitas, total_despesas_operacionais, total_investimentos, saldo_geral = 0, 0, 0, 0
    return total_receitas, total_despesas_operacionais, total_investimentos, saldo_geral


def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Layout Principal da Aplicação ---
col_chat_wrapper, col_dashboard_wrapper = st.columns([0.35, 0.65])

# --- Coluna do Chatbot (Esquerda) ---
with col_chat_wrapper:
    st.markdown('<div class="chat-outer-container card-style">', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="chatbot-header">
            <span class="chatbot-avatar">🤖</span>
            <h2 class="chatbot-title">FinanceBot</h2>
        </div>
    """, unsafe_allow_html=True)

    # Lógica de limitação de mensagens (já estava aqui)
    MAX_MESSAGES = 7
    if len(st.session_state.messages) > MAX_MESSAGES:
        st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

    # Renderização das mensagens
    message_area_html = '<div class="chat-messages-area">' 
    for i, message in enumerate(st.session_state.messages):
        role_class = "user-message" if message["role"] == "user" else "assistant-message"
        content_html = message["content"].replace("\n", "<br>")
        message_area_html += f'<div class="message-wrapper {role_class}"><div class="message-bubble">{content_html}</div></div>'
        if message["role"] == "assistant" and "Deseja adicionar uma categoria" in message["content"]:
            message_area_html += """
                <div class="quick-reply-container">
                    <button class="quick-reply-button">Sim</button>
                    <button class="quick-reply-button">Não</button>
                </div>"""
    message_area_html += '</div>' 
    st.markdown(message_area_html, unsafe_allow_html=True)
    
    user_prompt = st.chat_input("Enviar uma mensagem...", key="chat_input_scroll_fixed_height")

    st.markdown('</div>', unsafe_allow_html=True) # Fim de chat-outer-container

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt, "type": "text"})
    with st.spinner("FinanceBot está digitando..."):
        bot_response_text = handle_message(user_prompt)
    st.session_state.messages.append({"role": "assistant", "content": bot_response_text, "type": "text"})
    st.rerun()

# --- Coluna do Dashboard (Direita) ---
with col_dashboard_wrapper:
    st.markdown('<div class="dashboard-column-wrapper">', unsafe_allow_html=True)
    df_all_data = load_dashboard_data() 
    # Use os nomes de variáveis retornados por calculate_summary consistentemente
    receitas, despesas_operacionais, investimentos_val, saldo_geral = calculate_summary(df_all_data)
    
    st.markdown(f""" <div class="dashboard-grid"> 
                        <div class="dashboard-card card-style"><p class="card-title">Saldo</p><p class="card-value">{format_currency(saldo_geral)}</p></div> 
                        <div class="dashboard-card card-style"><p class="card-title">Ganhos</p><p class="card-value">{format_currency(receitas)}</p></div> 
                        <div class="dashboard-card card-style"><p class="card-title">Gastos</p><p class="card-value">{format_currency(despesas_operacionais)}</p></div> 
                        <div class="dashboard-card card-style"><p class="card-title">Investimentos</p><p class="card-value">{format_currency(investimentos_val)}</p></div> 
                    </div> """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="graph-card card-style">', unsafe_allow_html=True)
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # ALTERAÇÃO 2: Novo título e lógica do gráfico de pizza
    # ------------------------------------------------------------------------------
    st.markdown(f'<h3 class="graph-title">Visão Geral Financeira</h3>', unsafe_allow_html=True)
    
    graph_col, legend_col = st.columns([0.6, 0.4]) # Mantém proporção ou ajusta
    with graph_col:
        # Usar os valores calculados: receitas, despesas_operacionais, investimentos_val
        graph_data_list = []
        if receitas > 0:
            graph_data_list.append({'Tipo': 'Ganhos', 'Valor': receitas})
        if despesas_operacionais > 0: # Usar despesas_operacionais aqui
            graph_data_list.append({'Tipo': 'Gastos', 'Valor': despesas_operacionais})
        if investimentos_val > 0:
            graph_data_list.append({'Tipo': 'Investimentos', 'Valor': investimentos_val})

        if graph_data_list: # Só plota se houver dados
            overview_df = pd.DataFrame(graph_data_list)
            
            fig_pie_overview = px.pie(overview_df, 
                                 values='Valor', 
                                 names='Tipo', 
                                 hole=0.7,
                                 color='Tipo', # Para aplicar cores específicas
                                 color_discrete_map={ # Mapeamento de cores para os tipos
                                     'Ganhos': COLOR_HIGHLIGHT_GREEN,
                                     'Gastos': COLOR_GASTOS_RED_PIE,
                                     'Investimentos': COLOR_INVESTIMENTOS_BLUEGREEN_PIE
                                 })
            
            saldo_no_grafico_texto = f"Saldo<br>{format_currency(saldo_geral)}"
            fig_pie_overview.update_layout(
                annotations=[dict(text=saldo_no_grafico_texto, x=0.5, y=0.5, font_size=18, 
                                  showarrow=False, font_color=COLOR_TEXT_MAIN, font_weight=600)],
                legend=dict(visible=False), # Já estava False, mantido
                margin=dict(t=10, b=10, l=10, r=10),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=250
            )
            fig_pie_overview.update_traces(textinfo='none', hoverinfo='label+percent+value', # Adicionado +value ao hover
                                      marker=dict(line=dict(color=COLOR_CARD_CHAT_CONTAINER_BG, width=4)))
            st.plotly_chart(fig_pie_overview, use_container_width=True)
        else:
            st.markdown(f"<p style='text-align:center; color:{COLOR_TEXT_SECONDARY};'>Sem dados para exibir o gráfico de visão geral.</p>", unsafe_allow_html=True)

    with legend_col:
        st.markdown(f"<div class='custom-legend'>", unsafe_allow_html=True)
        # A legenda agora reflete Ganhos, Gastos, Investimentos
        total_para_legenda = receitas + despesas_operacionais + investimentos_val
        if total_para_legenda == 0: total_para_legenda = 1

        if receitas > 0:
            st.markdown(f"""<div class="legend-item"><span class="legend-color-dot" style="background-color: {COLOR_HIGHLIGHT_GREEN};"></span><span class="legend-text">Ganhos</span><span class="legend-percentage">{(receitas / total_para_legenda) * 100:.1f}%</span></div>""", unsafe_allow_html=True)
        if despesas_operacionais > 0:
            st.markdown(f"""<div class="legend-item"><span class="legend-color-dot" style="background-color: {COLOR_GASTOS_RED_PIE};"></span><span class="legend-text">Gastos</span><span class="legend-percentage">{(despesas_operacionais / total_para_legenda) * 100:.1f}%</span></div>""", unsafe_allow_html=True)
        if investimentos_val > 0:
            st.markdown(f"""<div class="legend-item"><span class="legend-color-dot" style="background-color: {COLOR_INVESTIMENTOS_BLUEGREEN_PIE};"></span><span class="legend-text">Investimentos</span><span class="legend-percentage">{(investimentos_val / total_para_legenda) * 100:.1f}%</span></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            
    st.markdown(f'</div>', unsafe_allow_html=True) 
    st.markdown('</div>', unsafe_allow_html=True)