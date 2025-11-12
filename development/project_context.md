# Contexto do Projeto: LexAudit (Sistema de Auditoria de Citações Jurídicas)

## 1. Visão Geral e Objetivo

Este projeto visa criar um sistema automático de auditoria, o **LexAudit**, para documentos jurídicos. O objetivo principal é **identificar, extrair e validar a correção de todas as citações jurídicas** (legislação e jurisprudência) dentro de textos como pareceres, editais e petições.

O sistema deve ler um documento bruto (DOCX/PDF), analisar cada citação e avaliá-la, sinalizando problemas e gerando uma **justificativa clara e auditável** para cada caso.

## 2. O Problema a ser Resolvido

A redação de documentos jurídicos sofre com uma incidência crescente de erros em citações. O sistema deve ser capaz de detectar e classificar quatro categorias principais de problemas:

1.  **Citações Desatualizadas:** O texto legal citado já mudou ou foi revogado, e o autor usa uma redação que não está mais em vigor.
2.  **Citações Incorretas:** A referência está errada; por exemplo, o artigo, parágrafo ou inciso apontado não corresponde ao texto apresentado.
3.  **Citações Inexistentes:** A referência é completamente fabricada (ex: um artigo de lei ou número de processo que não existe). Este é um problema típico de **alucinação de LLMs** usadas para redigir o documento.
4.  **Citações Fora de Contexto:** A norma citada é real, mas a afirmação ou inferência que o autor faz sobre ela no documento é incompatível com o texto legal.

## 3. A Metodologia: Um Pipeline de Módulos Paralelos

O sistema será construído como um pipeline automático dividido em três frentes de trabalho principais que podem ser desenvolvidas em paralelo (A, B e C).

### Parte A: Extração e Recuperação

Esta é a primeira etapa do pipeline, responsável por processar o documento bruto e encontrar as fontes.

1.  **Ingestão:** Receber o documento em formato DOCX ou PDF.
2.  **Extração (O "Linker"):** Usar uma ferramenta (inicialmente o **LexML Linker**) para detectar automaticamente as *strings* de citação no texto (ex: "Lei 9.784/1999, art. 2º, §1º").
    * **Obs:** Esta ferramenta poderá ser substituída por um sistema próprio baseado em agentes ou modelos NER mais modernos.
3.  **Resolução:** Mapear a citação textual para seu identificador canônico e oficial, a **URN:LEX**.
4.  **Recuperação (A "Busca pela Verdade"):** Usar o ecossistema **LexML** e outras fontes oficiais (STJ/STF) para recuperar a "redação verdadeira" (o texto oficial e vigente) do dispositivo legal ou da jurisprudência citada.

### Parte B: Análise Multiagente com RAG

Esta é a lógica central de validação, onde a IA compara o documento do usuário com a fonte oficial.

1.  **Entrada:** Este módulo recebe a citação extraída (da Parte A) e o texto oficial recuperado.
2.  **RAG (Retrieval-Augmented Generation):** Se o texto oficial recuperado for muito extenso (ex: uma lei inteira), um sistema RAG será usado para focar e recuperar apenas o trecho específico (o artigo ou parágrafo exato) relevante para a citação.
3.  **Debate Multiagente:** A validação será feita por **Agentes Verificadores**. Estes agentes irão "debater" (inspirado em "Multiagent Debate") o que foi afirmado no documento *versus* o que está no texto oficial.
4.  **Classificação:** Com base nessa análise, os agentes classificam a citação em categorias como: `correta`, `alterada`, `revogada` ou `ambígua`.
5.  **Justificativa Auditável:** O sistema gera uma explicação para sua classificação. Essa justificativa **deve incluir trechos do texto oficial** recuperado como evidência, garantindo a auditoria e reduzindo a alucinação do próprio sistema de verificação.

### Parte C: Avaliação e Criação de Datasets

O desenvolvimento do sistema depende de um ciclo robusto de avaliação e da criação de um *benchmark* confiável.

1.  **Coleta de Dados Reais:** Coletar documentos públicos (editais, pareceres) que contêm citações reais.
2.  **Uso de Datasets Existentes (para Extração):** Utilizar o **LeNER-br** como base para treinar ou validar a etapa de extração (NER), especialmente para a entidade "Jurisprudência".
3.  **Criação de Dataset Sintético (para Validação):**
    * **Fonte de Ouro (Golden Corpus):** Usar documentos de alta qualidade e bem revisados, como acórdãos de **Dados Abertos do STJ**, onde as citações são presumidamente corretas.
    * **Mutações (Geração de Erros):** Adicionar **erros propositais** (mutações) a esse corpus de ouro para criar exemplos sintéticos de todos os tipos de problemas: erros de citação, dispositivos revogados, redações desatualizadas, etc.
4.  **Rotulagem:** Rotular manualmente este dataset (reais + sintéticos) com as classes de validação (`correta`, `alterada`, `revogada`, etc.).
5.  **Medição:** Rodar o pipeline (Partes A+B) sobre este dataset de teste e medir o desempenho.

## 4. Métricas de Avaliação

O sucesso do projeto será medido analisando o desempenho de quatro tarefas distintas:

1.  **Captura de Citações (Recall da Extração):**
    * *Pergunta:* Quantas das citações no texto foram encontradas?
    * *Métrica:* Acurácia (ou Recall).
2.  **Conversão de Citações (Precisão da Resolução):**
    * *Pergunta:* Quantas citações capturadas foram corretamente mapeadas para a URN:LEX ou texto jurídico correto?
    * *Métrica:* Acurácia.
3.  **Classificação de Citações (Precisão da Validação):**
    * *Pergunta:* Quantas citações foram corretamente classificadas (ex: como `correta` ou `revogada`)?
    * *Métrica:* Acurácia e Matriz de Confusão.
4.  **Qualidade da Justificativa (Qualidade da Geração):**
    * *Pergunta:* A explicação gerada é clara, útil e baseada em evidências?
    * *Métrica:* Nota de 1 a 5 (dada por um agente avaliador ou por um humano).

## 5. Fundamentos Conceituais e Referências

O projeto se baseia em pesquisas recentes sobre IA, especialmente:

* **RAG e Geração com Citação:** `CitaLaw`, que aborda o alinhamento de fontes (citações) com respostas geradas por LLMs no domínio legal.
* **Extração de Entidades (NER):** Trabalhos sobre NER em documentos legais usando *prompt-based models* e *weak supervision*.
* **Raciocínio de Agentes:** Técnicas como `Chain-of-Thought` e `ReAct` (Reasoning and Acting) para permitir que os agentes pensem passo a passo.
* **Validação por Múltiplos Agentes:** A ideia de `Improving Factuality and Reasoning... through Multiagent Debate`, que será usada para os Agentes Verificadores na Parte B.