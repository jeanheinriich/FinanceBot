# FinanceBot: Seu Assistente Financeiro Inteligente com IA

Bem-vindo ao FinanceBot! Este projeto é um assistente financeiro pessoal que combina um chatbot conversacional para registro e consulta de transações, um banco de dados SQLite para armazenamento persistente, um dashboard Streamlit para visualização interativa de dados e a IA Generativa do Google (Gemini) para fornecer insights e relatórios financeiros.

O chatbot permite que você gerencie suas finanças usando linguagem natural para registrar ganhos, gastos e investimentos, além de listar, editar ou excluir transações. O dashboard oferece uma visão gráfica e resumida da sua situação financeira.

## Funcionalidades Principais

*   **Chatbot Conversacional com IA:**
    *   Registre despesas, receitas e investimentos usando linguagem natural (ex: "Gastei 50 reais com mercado hoje", "Recebi 1000 de salário", "Investi 200 em Tesouro Direto").
    *   Consulte gastos e receitas por categoria e período.
    *   Liste transações com filtros.
    *   **Exclua transações:** última, por data, por categoria, todas de um tipo, ou todas as transações (com confirmação).
    *   **Edite transações existentes:** altere valor, categoria, data ou descrição (com confirmação).
    *   Solicite relatórios financeiros gerados por IA para um período específico.
*   **Dashboard Visual Interativo:**
    *   Exibe cartões com totais de Saldo, Ganhos, Gastos e Investimentos.
    *   Apresenta um gráfico de pizza com a visão geral financeira (distribuição entre Ganhos, Gastos e Investimentos).
    *   Atualiza em tempo real com base nas interações do chatbot.
*   **Banco de Dados Local:**
    *   Utiliza SQLite para armazenar todas as suas transações de forma segura e local.
*   **Inteligência Artificial (Google Gemini):**
    *   Interpreta comandos em linguagem natural.
    *   Gera relatórios financeiros detalhados com análises e dicas (quando solicitado).


## Configuração e Instalação

Siga os passos abaixo para configurar e rodar o FinanceBot no seu ambiente local:

1.  **Clone o Repositório (se você estiver baixando de outro lugar):**
    ```bash
    git clone https://github.com/SEU_NOME_DE_USUARIO/finance-bot.git
    cd finance-bot
    ```
    (Substitua `SEU_NOME_DE_USUARIO` e `finance-bot` pelo nome correto do seu repositório).

2.  **Crie e Ative um Ambiente Virtual Python (Recomendado):**
    Isso isola as dependências do projeto.
    ```bash
    # Navegue para a pasta raiz do projeto 'finance-bot' se ainda não estiver lá
    python -m venv venv 
    ```
    Para ativar (Windows - PowerShell ou CMD):
    ```bash
    .\venv\Scripts\activate 
    ```
    (No Git Bash ou Linux/macOS: `source venv/bin/activate`)
    Seu prompt do terminal deve agora mostrar `(venv)` no início.

3.  **Instale as Dependências:**
    Com o ambiente virtual ativado, instale todas as bibliotecas necessárias:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure sua Chave de API do Google Generative AI:**
    *   Obtenha uma API Key no [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Na pasta raiz do projeto (`finance-bot/`), crie um arquivo chamado `.env` (exatamente assim, com um ponto no início).
    *   Adicione sua API Key a este arquivo da seguinte forma:
        ```
        GOOGLE_API_KEY=SUA_CHAVE_DE_API_AQUI
        ```
        Substitua `SUA_CHAVE_DE_API_AQUI` pela sua chave real.
    *   **Importante:** O arquivo `.env` já está listado no `.gitignore`, então sua chave de API não será enviada para o GitHub se você fizer novos commits.

5.  **Inicialize o Banco de Dados (Opcional - será criado automaticamente):**
    O banco de dados (`data/transactions.db`) e a tabela `transactions` serão criados automaticamente na primeira vez que você rodar a aplicação. Se desejar inicializá-lo manualmente por algum motivo:
    ```bash
    # Com o ambiente (venv) ativado
    python utils/db.py 
    ```
    (Isso executará o bloco `if __name__ == '__main__':` em `db.py`, que chama `init_db()`).

## Como Executar a Aplicação

Após completar a configuração e instalação:

1.  **Certifique-se de que seu ambiente virtual `(venv)` está ativado.**
2.  **No terminal, dentro da pasta raiz `finance-bot`, execute o Streamlit:**
    ```bash
    streamlit run dashboard/main.py
    ```
3.  O Streamlit iniciará um servidor local e, geralmente, abrirá a aplicação automaticamente no seu navegador padrão. Se não abrir, copie a URL "Local URL" (algo como `http://localhost:8501`) do terminal e cole no seu navegador.

4.  **Interaja com o FinanceBot!**
    *   Use a interface de chat na coluna da esquerda para registrar transações, fazer perguntas, solicitar edições, exclusões ou relatórios.
    *   Observe o dashboard na coluna da direita atualizar com seus dados financeiros.

## Exemplo de Comandos para o Chatbot

*   **Registrar:**
    *   "Gastei 50 reais com almoço hoje"
    *   "Recebi 1500 de salário no dia 05/07/2024"
    *   "Investi 300 em CDB ontem" (será registrado como saída, categoria 'investimentos')
*   **Consultar:**
    *   "Quanto gastei com alimentação este mês?"
    *   "Qual meu saldo total?"
*   **Listar:**
    *   "Liste meus gastos de ontem"
    *   "Me mostre todas as minhas entradas de janeiro"
*   **Editar (o bot pedirá confirmação):**
    *   (Após listar) "Edite o item 2 para 75 reais"
    *   "Altere o valor do meu último gasto para 90"
    *   "Mude a categoria da minha despesa de mercado de hoje para 'compras diversas'"
*   **Excluir (o bot pedirá confirmação):**
    *   "Apague meu último investimento"
    *   (Após listar) "Excluir o primeiro item da lista"
    *   "Delete todas as transações de transporte do mês passado"
    *   "Quero limpar todos os meus gastos"
*   **Relatório:**
    *   "Me dá um relatório financeiro de abril"

## Limpar o Banco de Dados (Se Necessário)

Se você quiser limpar todas as transações e começar do zero (mantendo a estrutura da tabela):

1.  Certifique-se de que seu ambiente virtual `(venv)` está ativado.
2.  No terminal, na pasta `finance-bot`, execute o script de limpeza:
    ```bash
    python clear_database_data.py 
    ```
    (Use o nome do script que você criou para limpar o banco, como `clear_my_data.py` ou `clear_database_data.py`).
    O script pedirá confirmação antes de apagar os dados.

## Próximos Passos e Melhorias (Sugestões)

*   Melhorar ainda mais o parsing de linguagem natural e a robustez do LLM.
*   Adicionar mais tipos de gráficos e visualizações ao dashboard.
*   Implementar funcionalidade de orçamento e metas.
*   Permitir exportação de dados.
*   Considerar autenticação de usuário se for para uso compartilhado.

Divirta-se gerenciando suas finanças com o FinanceBot!
