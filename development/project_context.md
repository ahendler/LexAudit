# Contexto do Projeto: LexAudit (Sistema de Auditoria de Citações Jurídicas)

## 1. Visão Geral e Objetivo

[cite_start]Este projeto visa criar um sistema automático de auditoria, o **LexAudit**[cite: 1], para documentos jurídicos. [cite_start]O objetivo principal é **identificar, extrair e validar a correção de todas as citações jurídicas** (legislação e jurisprudência) dentro de textos como pareceres, editais e petições[cite: 6].

[cite_start]O sistema deve ler um documento bruto (DOCX/PDF) [cite: 21][cite_start], analisar cada citação e avaliá-la, sinalizando problemas e gerando uma **justificativa clara e auditável** para cada caso[cite: 8].

## 2. O Problema a ser Resolvido

[cite_start]A redação de documentos jurídicos sofre com uma incidência crescente de erros em citações[cite: 7]. O sistema deve ser capaz de detectar e classificar quatro categorias principais de problemas:

1.  [cite_start]**Citações Desatualizadas:** O texto legal citado já mudou ou foi revogado, e o autor usa uma redação que não está mais em vigor[cite: 7, 16].
2.  [cite_start]**Citações Incorretas:** A referência está errada; por exemplo, o artigo, parágrafo ou inciso apontado não corresponde ao texto apresentado[cite: 7].
3.  **Citações Inexistentes:** A referência é completamente fabricada (ex: um artigo de lei ou número de processo que não existe). [cite_start]Este é um problema típico de **alucinação de LLMs** usadas para redigir o documento[cite: 7].
4.  [cite_start]**Citações Fora de Contexto:** A norma citada é real, mas a afirmação ou inferência que o autor faz sobre ela no documento é incompatível com o texto legal[cite: 7].

## 3. A Metodologia: Um Pipeline de Módulos Paralelos

[cite_start]O sistema será construído como um pipeline automático [cite: 11] [cite_start]dividido em três frentes de trabalho principais que podem ser desenvolvidas em paralelo (A, B e C)[cite: 19].

### Parte A: Extração e Recuperação

Esta é a primeira etapa do pipeline, responsável por processar o documento bruto e encontrar as fontes.

1.  [cite_start]**Ingestão:** Receber o documento em formato DOCX ou PDF[cite: 21].
2.  [cite_start]**Extração (O "Linker"):** Usar uma ferramenta (inicialmente o **LexML Linker** [cite: 12][cite_start]) para detectar automaticamente as *strings* de citação no texto (ex: "Lei 9.784/1999, art. 2º, §1º")[cite: 22].
    * [cite_start]**Obs:** Esta ferramenta poderá ser substituída por um sistema próprio baseado em agentes ou modelos NER mais modernos[cite: 13].
3.  [cite_start]**Resolução:** Mapear a citação textual para seu identificador canônico e oficial, a **URN:LEX**[cite: 12, 23].
4.  [cite_start]**Recuperação (A "Busca pela Verdade"):** Usar o ecossistema **LexML** [cite: 14] [cite_start]e outras fontes oficiais (STJ/STF) [cite: 46] [cite_start]para recuperar a "redação verdadeira" (o texto oficial e vigente) do dispositivo legal ou da jurisprudência citada[cite: 14, 24].

### Parte B: Análise Multiagente com RAG

Esta é a lógica central de validação, onde a IA compara o documento do usuário com a fonte oficial.

1.  [cite_start]**Entrada:** Este módulo recebe a citação extraída (da Parte A) e o texto oficial recuperado[cite: 26].
2.  [cite_start]**RAG (Retrieval-Augmented Generation):** Se o texto oficial recuperado for muito extenso (ex: uma lei inteira), um sistema RAG será usado para focar e recuperar apenas o trecho específico (o artigo ou parágrafo exato) relevante para a citação[cite: 27].
3.  **Debate Multiagente:** A validação será feita por **Agentes Verificadores**. [cite_start]Estes agentes irão "debater" (inspirado em "Multiagent Debate" [cite: 65][cite_start]) o que foi afirmado no documento *versus* o que está no texto oficial[cite: 28].
4.  [cite_start]**Classificação:** Com base nessa análise, os agentes classificam a citação em categorias como: `correta`, `alterada`, `revogada` ou `ambígua`[cite: 29].
5.  **Justificativa Auditável:** O sistema gera uma explicação para sua classificação. [cite_start]Essa justificativa **deve incluir trechos do texto oficial** recuperado como evidência, garantindo a auditoria e reduzindo a alucinação do próprio sistema de verificação[cite: 15, 30].

### Parte C: Avaliação e Criação de Datasets

O desenvolvimento do sistema depende de um ciclo robusto de avaliação e da criação de um *benchmark* confiável.

1.  [cite_start]**Coleta de Dados Reais:** Coletar documentos públicos (editais, pareceres) que contêm citações reais[cite: 32, 41].
2.  [cite_start]**Uso de Datasets Existentes (para Extração):** Utilizar o **LeNER-br** como base para treinar ou validar a etapa de extração (NER), especialmente para a entidade "Jurisprudência"[cite: 43].
3.  **Criação de Dataset Sintético (para Validação):**
    * [cite_start]**Fonte de Ouro (Golden Corpus):** Usar documentos de alta qualidade e bem revisados, como acórdãos de **Dados Abertos do STJ**, onde as citações são presumidamente corretas[cite: 46].
    * [cite_start]**Mutações (Geração de Erros):** Adicionar **erros propositais** (mutações) a esse corpus de ouro para criar exemplos sintéticos de todos os tipos de problemas: erros de citação, dispositivos revogados, redações desatualizadas, etc.[cite: 32, 46].
4.  [cite_start]**Rotulagem:** Rotular manualmente este dataset (reais + sintéticos) com as classes de validação (`correta`, `alterada`, `revogada`, etc.)[cite: 33, 44].
5.  [cite_start]**Medição:** Rodar o pipeline (Partes A+B) sobre este dataset de teste e medir o desempenho[cite: 34].

## 4. Métricas de Avaliação

[cite_start]O sucesso do projeto será medido analisando o desempenho de quatro tarefas distintas[cite: 49]:

1.  **Captura de Citações (Recall da Extração):**
    * *Pergunta:* Quantas das citações no texto foram encontradas?
    * [cite_start]*Métrica:* Acurácia (ou Recall) [cite: 50-51].
2.  **Conversão de Citações (Precisão da Resolução):**
    * *Pergunta:* Quantas citações capturadas foram corretamente mapeadas para a URN:LEX ou texto jurídico correto?
    * [cite_start]*Métrica:* Acurácia[cite: 52].
3.  **Classificação de Citações (Precisão da Validação):**
    * *Pergunta:* Quantas citações foram corretamente classificadas (ex: como `correta` ou `revogada`)?
    * [cite_start]*Métrica:* Acurácia e Matriz de Confusão [cite: 53-54].
4.  **Qualidade da Justificativa (Qualidade da Geração):**
    * *Pergunta:* A explicação gerada é clara, útil e baseada em evidências?
    * [cite_start]*Métrica:* Nota de 1 a 5 (dada por um agente avaliador ou por um humano) [cite: 55-56].

## 5. Fundamentos Conceituais e Referências

O projeto se baseia em pesquisas recentes sobre IA, especialmente:

* [cite_start]**RAG e Geração com Citação:** `CitaLaw` [cite: 62][cite_start], que aborda o alinhamento de fontes (citações) com respostas geradas por LLMs no domínio legal[cite: 63].
* [cite_start]**Extração de Entidades (NER):** Trabalhos sobre NER em documentos legais usando *prompt-based models* e *weak supervision*[cite: 64].
* [cite_start]**Raciocínio de Agentes:** Técnicas como `Chain-of-Thought` [cite: 64] [cite_start]e `ReAct` (Reasoning and Acting) [cite: 64] para permitir que os agentes pensem passo a passo.
* [cite_start]**Validação por Múltiplos Agentes:** A ideia de `Improving Factuality and Reasoning... through Multiagent Debate` [cite: 65][cite_start], que será usada para os Agentes Verificadores na Parte B[cite: 28].