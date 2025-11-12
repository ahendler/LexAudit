# LexAudit ⚖️
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-blue)](https://github.com/seu-usuario/lexaudit)
[![Python Version](https://img.shields.io/badge/Python%3A%203.13-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

O **LexAudit** é um sistema de auditoria e validação de citações jurídicas em documentos. Ele verifica se as leis, artigos,  parágrafos e ~~jurisprudências~~ citados estão corretos, atualizados e contextualmente válidos, combatendo referências desatualizadas ou alucinações geradas por LLMs.

--- 

## O Problema

Documentos jurídicos (petições, pareceres, editais) dependem da precisão de suas citações (leis e jurisprudência). No entanto, é cada vez mais comum encontrar problemas graves:

* **Leis Revogadas/Desatualizadas:** O texto citado não corresponde mais à redação atual da lei.
* **Referências Incorretas:** O artigo, parágrafo ou inciso apontado está errado ("ponteiro quebrado").
* **Citações Inexistentes:** A referência simplesmente não existe, muitas vezes resultado de alucinação de LLMs usadas na redação.
* **Uso Fora de Contexto:** A lei existe, mas a afirmação feita pelo autor no documento não é suportada (ou é contradita) pelo texto legal.

Esses erros comprometem a segurança jurídica, a validade de argumentos e a qualidade de decisões.

## Pipeline LexAudit

O LexAudit processa um documento bruto através de um pipeline automático de validação em 4 etapas, gerando um relatório de auditoria claro e auditável para cada citação encontrada.

1.  **[ETAPA 1] Extração:** O sistema lê o documento e identifica todas as menções a normas (ex: "Art. 5º da CF") e jurisprudência (ex: "REsp nº 1.234.567").
2.  **[ETAPA 2] Resolução:** Cada menção textual é convertida em um identificador canônico (URN:LEX) usando um LLM.
3.  **[ETAPA 3] Recuperação:** O sistema busca no Google (via SerpAPI) por fontes oficiais e baixa o texto completo de sites governamentais (planalto.gov.br, normas.leg.br, etc.).
4.  **[ETAPA 4] Validação (Agente RAG):** Um Agente de IA (usando RAG) compara o texto do documento com o texto oficial recuperado, classificando a citação e gerando justificativa.

## Estrutura do Repositório (Sugestão)

```
lexaudit/
│
├── config/         # Configurações e chaves de API
│   └── .env.example
│
├── data/           # Datasets de validação (ex: LeNER-Br, corpus de mutações)
│
├── notebooks/      # Jupyter Notebooks para exploração, prototipagem e P&D
│   ├── 01_explore_data.ipynb
│   ├── 02_dev_linker.ipynb
│   └── 03_dev_rag_agent.ipynb
│
├── src/            # Código-fonte principal da aplicação
│   └── lexaudit/   # O pacote Python instalável
│       │
│       ├── extraction/   # [ETAPA 1] Módulos de extração de citações
│       ├── retrieval/    # [ETAPA 2 & 3] Resolução (LLM) + Recuperação (SerpAPI)
│       ├── validation/   # [ETAPA 4] Lógica do Agente RAG de validação
│       │
│       ├── prompts/      # Templates de prompts usados pelos Agentes RAG
│       │   ├── __init__.py
│       │   ├── validation.py
│       │   └── templates.py
│       │
│       ├── core/         # Orquestração do pipeline e modelos de dados (Pydantic)
│       │   ├── pipeline.py
│       │   ├── models.py
│       │   └── settings.py
│       │
│       └── main.py       # Ponto de entrada (API FastAPI ou CLI)
│
├── tests/          # Testes unitários e de integração (Pytest)
│
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Como Usar

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/lexaudit.git](https://github.com/seu-usuario/lexaudit.git)
    cd lexaudit
    ```

2.  **Crie um ambiente virtual e instale as dependências:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure suas chaves de API:**
    * Copie o arquivo de exemplo de ambiente:
        ```bash
        cp config/.env.example config/.env
        ```
    * Edite o arquivo `config/.env` e adicione suas chaves:
        ```bash
        LLM_PROVIDER=gemini
        LLM_MODEL=gemini-2.5-flash
        GOOGLE_API_KEY=sua-chave-gemini-aqui
        SERPAPI_API_KEY=sua-chave-serpapi-aqui  # Chave grátis em serpapi.com
        ```

## Como Usar (Exemplo)

O pipeline pode ser invocado programaticamente. (Este é um exemplo conceitual de como o pacote `src/lexaudit` será usado):

```python
from lexaudit.core.pipeline import LexAuditPipeline

# Carrega o pipeline (ele vai instanciar o Linker, o Resolver, etc.)
auditor = LexAuditPipeline()

document_text = """
Segundo o Art. 5º, inciso XI, da Constituição Federal, "a casa é asilo 
inviolável do indivíduo".

Conforme a Lei nº 8.112 de 1990, em seu Art. 999, o servidor será 
aposentado compulsoriamente.
"""

# Executa a auditoria completa
report = auditor.run(document_text)

# Imprime o relatório de validação
for validation in report.validations:
    print(f"Citação: {validation.citation.original_text}")
    print(f"Status: {validation.status}")  # Ex: CORRETA, INEXISTENTE
    print(f"Justificativa: {validation.justification}\n")

```

### Saída Esperada:

```
Citação: Art. 5º, inciso XI, da Constituição Federal
Status: CORRETA
Justificativa: A citação textual "a casa é asilo inviolável do indivíduo" corresponde exatamente ao texto oficial do Art. 5º, XI, da CF/88.

Citação: Art. 999, da Lei nº 8.112 de 1990
Status: INEXISTENTE
Justificativa: A referência "Art. 999" não foi encontrada na Lei nº 8.112/1990. O último artigo desta lei é o Art. 253.
```

## 📜 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.