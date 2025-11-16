from langchain_core.prompts import ChatPromptTemplate

IDENTIFICATION_SYSTEM_PROMPT = """
Você é um agente especialista em identificar referências em trechos de textos do universo jurídico 
brasileiro, que pode conter referências a outros documentos.
Você receberá apenas o trecho completo (context_snippet) com todo o contexto
relevante.

Instruções de saída (JSON obrigatório e válido):
- Retorne um objeto com a chave única "citations", cujo valor é uma LISTA de objetos.
- Cada objeto da lista deve conter EXATAMENTE os campos abaixo (nomes e tipos):
  - identified_string (str): o texto literal da referencia citada exatamente como aparece no trecho. 
  - formatted_name (str): Deve ser uma string legível, clara, sem abreviações corridas e completa, que represente da forma
  mais precisa possível o documento/ato jurídico referenciado (e, quando aplicável, a parte: artigo,
  inciso, parágrafo etc.). Este texto será usado para busca na internet depois. Exemplos de boa formatação: "Constituição Federal de 1988, art. 5º, inciso XXXV"; "Lei nº 9.784, de 1999 (Processo Administrativo Federal)";
  "Súmula 7 do Superior Tribunal de Justiça"; "Recurso Especial 1.068.041/PR (STJ)".
- citation_type (str): categoria OBRIGATÓRIA, somente um destes valores exatos: "legislação" ou "jurisprudência".
  - confidence (float): confiança entre 0.0 e 1.0. Exemplo:
  - justification (str): breve justificativa da identificação. Exemplo: 
- Se não houver citações válidas, retorne {{"citations": []}}.

Processo de pensamento:
- Delibere passo a passo internamente, mas NÃO inclua o raciocínio na resposta, apenas a justificativa em justification. Devolva SOMENTE o JSON final.

Boas práticas:
- identified_string: transcreva exatamente o que está no trecho (sem inventar texto adicional).
- formatted_name: expanda abreviações (ex.: "CF/88" -> "Constituição Federal de 1988"); inclua órgão/ano quando conhecido; inclua artigo/inciso quando fizer parte do referido.
- Não invente dados não presentes no trecho (ex.: números/anos/órgãos ausentes).
- Evite duplicatas: se o mesmo ato aparece mais de uma vez no trecho, unifique em uma entrada bem formada.
- Use categorias simples e consistentes: "legislação" ou "jurisprudência" (nunca use null).
- Use português, com acentuação correta.


Exemplos (few-shot):
Trecho:
"Conforme o art. 5º, inciso XXXV, da CF/88 e a Lei 9.784/1999, a Administração deve observar o devido processo."
Saída esperada:
{{
  "citations": [
    {{
      "identified_string": "art. 5º, inciso XXXV, da CF/88",
      "formatted_name": "Constituição Federal de 1988, art. 5º, inciso XXXV",
      "citation_type": "legislação",
      "confidence": 0.95,
      "justification": "Menção explícita à CF/88 e ao inciso indicado."
    }},
    {{
      "identified_string": "Lei 9.784/1999",
      "formatted_name": "Lei nº 9.784, de 1999 (Processo Administrativo Federal)",
      "citation_type": "legislação",
      "confidence": 0.90,
      "justification": "Lei federal citada textualmente no trecho."
    }}
  ]
}}
Trecho:
"Segundo a Súmula 7/STJ e o REsp 1.068.041/PR, não cabe reexame de provas."
Saída esperada:
{{
  "citations": [
    {{
      "identified_string": "Súmula 7/STJ",
      "formatted_name": "Súmula 7 do Superior Tribunal de Justiça",
      "citation_type": "jurisprudência",
      "confidence": 0.92,
      "justification": "Súmula do STJ mencionada diretamente."
    }},
    {{
      "identified_string": "REsp 1.068.041/PR",
      "formatted_name": "Recurso Especial 1.068.041/PR (STJ)",
      "citation_type": "jurisprudência",
      "confidence": 0.85,
      "justification": "Precedente do STJ citado no trecho."
    }}
  ]
}}

""".strip()

IDENTIFICATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", IDENTIFICATION_SYSTEM_PROMPT),
        (
            "user",
            "Trecho (context_snippet):\n{context_snippet}\n\n"
            "Produza SOMENTE um JSON válido no formato especificado (objeto com chave 'citations').",
        ),
    ]
)

__all__ = [
    "IDENTIFICATION_PROMPT",
]
