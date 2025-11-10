# Project Context: LexAudit (Legal Citation Audit System)

## 1. Overview and Objective

This project aims to create an automatic audit system, **LexAudit**, for legal documents. The main objective is to **identify, extract, and validate the correctness of all legal citations** (legislation and case law) within texts such as legal opinions, notices, and petitions.

The system must read a raw document (DOCX/PDF), analyze each citation and evaluate it, flagging problems and generating a **clear and auditable justification** for each case.

## 2. The Problem to be Solved

The drafting of legal documents suffers from a growing incidence of citation errors. The system must be able to detect and classify four main categories of problems:

1.  **Outdated Citations:** The cited legal text has already changed or been revoked, and the author uses wording that is no longer in effect.
2.  **Incorrect Citations:** The reference is wrong; for example, the article, paragraph, or section pointed to does not correspond to the text presented.
3.  **Non-existent Citations:** The reference is completely fabricated (e.g., a law article or case number that does not exist). This is a typical problem of **LLM hallucination** used to draft the document.
4.  **Out-of-Context Citations:** The cited norm is real, but the statement or inference that the author makes about it in the document is incompatible with the legal text.

## 3. The Methodology: A Pipeline of Parallel Modules

The system will be built as an automatic pipeline divided into three main work fronts that can be developed in parallel (A, B, and C).

### Part A: Extraction and Retrieval

This is the first stage of the pipeline, responsible for processing the raw document and finding the sources.

1.  **Ingestion:** Receive the document in DOCX or PDF format.
2.  **Extraction (The "Linker"):** Use a tool (initially the **LexML Linker**) to automatically detect citation *strings* in the text (e.g., "Law 9.784/1999, art. 2, §1").
    * **Note:** This tool may be replaced by a proprietary system based on agents or more modern NER models.
3.  **Resolution:** Map the textual citation to its canonical and official identifier, the **URN:LEX**.
4.  **Retrieval (The "Search for Truth"):** Use the **LexML** ecosystem and other official sources (STJ/STF) to retrieve the "true wording" (the official and current text) of the legal provision or cited case law.

### Part B: Multi-Agent Analysis with RAG

This is the core validation logic, where AI compares the user's document with the official source.

1.  **Input:** This module receives the extracted citation (from Part A) and the retrieved official text.
2.  **RAG (Retrieval-Augmented Generation):** If the retrieved official text is too extensive (e.g., an entire law), a RAG system will be used to focus and retrieve only the specific excerpt (the exact article or paragraph) relevant to the citation.
3.  **Multi-Agent Debate:** Validation will be performed by **Verifier Agents**. These agents will "debate" (inspired by "Multiagent Debate") what was stated in the document *versus* what is in the official text.
4.  **Classification:** Based on this analysis, the agents classify the citation into categories such as: `correct`, `altered`, `revoked`, or `ambiguous`.
5.  **Auditable Justification:** The system generates an explanation for its classification. This justification **must include excerpts from the official text** retrieved as evidence, ensuring auditability and reducing hallucination from the verification system itself.

### Part C: Evaluation and Dataset Creation

The development of the system depends on a robust evaluation cycle and the creation of a reliable *benchmark*.

1.  **Real Data Collection:** Collect public documents (notices, legal opinions) that contain real citations.
2.  **Use of Existing Datasets (for Extraction):** Use **LeNER-br** as a basis for training or validating the extraction stage (NER), especially for the "Case Law" entity.
3.  **Creation of Synthetic Dataset (for Validation):**
    * **Golden Corpus:** Use high-quality and well-reviewed documents, such as rulings from **STJ Open Data**, where citations are presumably correct.
    * **Mutations (Error Generation):** Add **intentional errors** (mutations) to this golden corpus to create synthetic examples of all types of problems: citation errors, revoked provisions, outdated wording, etc.
4.  **Labeling:** Manually label this dataset (real + synthetic) with validation classes (`correct`, `altered`, `revoked`, etc.).
5.  **Measurement:** Run the pipeline (Parts A+B) on this test dataset and measure performance.

## 4. Evaluation Metrics

The success of the project will be measured by analyzing the performance of four distinct tasks:

1.  **Citation Capture (Extraction Recall):**
    * *Question:* How many of the citations in the text were found?
    * *Metric:* Accuracy (or Recall).
2.  **Citation Conversion (Resolution Precision):**
    * *Question:* How many captured citations were correctly mapped to the URN:LEX or correct legal text?
    * *Metric:* Accuracy.
3.  **Citation Classification (Validation Precision):**
    * *Question:* How many citations were correctly classified (e.g., as `correct` or `revoked`)?
    * *Metric:* Accuracy and Confusion Matrix.
4.  **Justification Quality (Generation Quality):**
    * *Question:* Is the generated explanation clear, useful, and evidence-based?
    * *Metric:* Score from 1 to 5 (given by an evaluator agent or by a human).

## 5. Conceptual Foundations and References

The project is based on recent research on AI, especially:

* **RAG and Generation with Citation:** `CitaLaw`, which addresses the alignment of sources (citations) with responses generated by LLMs in the legal domain.
* **Named Entity Recognition (NER):** Works on NER in legal documents using *prompt-based models* and *weak supervision*.
* **Agent Reasoning:** Techniques such as `Chain-of-Thought` and `ReAct` (Reasoning and Acting) to allow agents to think step by step.
* **Multi-Agent Validation:** The idea of `Improving Factuality and Reasoning... through Multiagent Debate`, which will be used for the Verifier Agents in Part B.
