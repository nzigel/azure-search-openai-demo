import openai
from approaches.approach import Approach
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from text import nonewlines

# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class RetrieveThenReadApproach(Approach):

    template = \
"You are an intelligent assistant helpings people learn more about Te Tiriti o Waitangi / The Treaty of Waitangi, New Zealand's founding document and the relationship between Māori and the British crown. " + \
"Use 'you' to refer to the individual asking the questions even if they ask with 'I'. " + \
"Answer the following question using only the data provided in the sources below. " + \
"For tabular information return it as an html table. Do not return markdown format. "  + \
"Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response. " + \
"If you cannot answer using the sources below, say you don't know. " + \
"""

###
Question: 'How has the Treaty of Waitangi been interpreted and applied in New Zealand's history, and what impact has it had on Māori rights and sovereignty?'

Sources:
info1.pdf: The Treaty of Waitangi is New Zealand's founding document. It was signed on February 6, 1840, between the British Crown and about 540 Māori rangatira (chiefs). The Treaty has been interpreted and applied in different ways there have been disagreements between Māori and the British Crown over its interpretation between the English and Māori versions of the treaty.
info2.pdf: The Treaty is an agreement in Māori and English that established a British Governor of New Zealand, recognized Māori ownership of their lands and other properties, and gave Māori the rights of British subjects.
info3.pdf: The British Crown believed that it had sovereignty over all of New Zealand, while Māori believed that they retained their sovereignty over their lands and people.
info4.pdf: The Treaty recognised Māori ownership of their lands and other property, and gave Māori the rights of British subjects.

Answer:
The Treaty of Waitangi is New Zealand's founding document. It was signed on February 6, 1840, between the British Crown and about 540 Māori rangatira (chiefs) [info1.pdf]. The Treaty is an agreement in Māori and English that established a British Governor of New Zealand, recognized Māori ownership of their lands and other properties, and gave Māori the rights of British subjects 12. [info2.pdf][info4.pdf].
The Treaty has been interpreted and applied in different ways throughout New Zealand's history. In the early years after the signing of the Treaty, there were disagreements between Māori and the British Crown over its interpretation [info1.pdf]. The British Crown believed that it had sovereignty over all of New Zealand, while Māori believed that they retained their sovereignty over their lands and people [info3.pdf].

###
Question: '{q}'?

Sources:
{retrieved}

Answer:
"""

    def __init__(self, search_client: SearchClient, openai_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.openai_deployment = openai_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field

    def run(self, q: str, overrides: dict) -> any:
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        top = overrides.get("top") or 3
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None

        if overrides.get("semantic_ranker"):
            r = self.search_client.search(q, 
                                          filter=filter,
                                          query_type=QueryType.SEMANTIC, 
                                          query_language="en-us", 
                                          query_speller="lexicon", 
                                          semantic_configuration_name="default", 
                                          top=top, 
                                          query_caption="extractive|highlight-false" if use_semantic_captions else None)
        else:
            r = self.search_client.search(q, filter=filter, top=top)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) for doc in r]
        else:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(doc[self.content_field]) for doc in r]
        content = "\n".join(results)

        prompt = (overrides.get("prompt_template") or self.template).format(q=q, retrieved=content)
        completion = openai.Completion.create(
            engine=self.openai_deployment, 
            prompt=prompt, 
            temperature=overrides.get("temperature") or 0.3, 
            max_tokens=1024, 
            n=1, 
            stop=["\n"])

        return {"data_points": results, "answer": completion.choices[0].text, "thoughts": f"Question:<br>{q}<br><br>Prompt:<br>" + prompt.replace('\n', '<br>')}
