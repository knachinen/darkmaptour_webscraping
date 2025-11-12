# Standard library imports
import json
import re

# Langchain specific imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaLLM
from langchain_classic.prompts import PromptTemplate

class LLMExtractor:
    def __init__(self, model: str = 'gemma3:1b'):
        self.model = model
        self.llm = OllamaLLM(model=self.model)
        self.prompt_template = PromptTemplate(
            template="""<s>[INST] Given the context - {context} </s>[INST] [INST] Answer the following question - {question}[/INST]""",
            input_variables=["context", "question"]
        )
        self.ret_prompt = """
- 기사에서 '누가', '언제', '어디서', '무엇을' 정보를 찾을 것. 
- 기타 모든 지역 정보를 찾을 것.
- 다음과 같은 json 포맷으로 답할 것.
- {"누가": "", "언제": "", "어디서": "", "무엇을": "", "기타 지역 정보": ""}
"""

    def extract_info(self, text: str) -> dict | None:
        doc = Document(page_content=text, metadata={"source": "local"})

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=50)
        texts = text_splitter.split_documents([doc])

        # Combine the texts into a single context string
        context = "\n\n".join([t.page_content for t in texts])

        # Format the prompt with the context and question
        formatted_prompt = self.prompt_template.format(context=context, question=self.ret_prompt)

        raw_result = self.llm.invoke(formatted_prompt)
        return self._get_json(raw_result)

    def _get_json(self, json_text: str, verbose: bool = False) -> dict | None:
        """Parse JSON text into a Python dictionary.
        Strips markdown code block indicators if present, and attempts to extract
        the first valid JSON object from the string.

        Args:
            json_text (str): JSON text to parse.
            verbose (bool, optional): If True, print JSON text. Defaults to False.

        Returns:
            dict: Parsed JSON data as a dictionary, or None if parsing fails.
        """
        if verbose:
            print("Input JSON text:")
            print(json_text)

        # Strip markdown code block indicators if present
        if json_text.strip().startswith('```json') and json_text.strip().endswith('```'):
            json_text = json_text.strip()[len('```json'):-len('```')].strip()
        elif json_text.strip().startswith('```') and json_text.strip().endswith('```'):
            json_text = json_text.strip()[len('```'):-len('```')].strip()

        # Attempt to find and extract the first JSON object using a non-greedy regex
        # This handles cases where there's extra text before or after the JSON,
        # or if the LLM outputs multiple JSON-like structures.
        match = re.search(r'\{(.*?)\}', json_text, re.DOTALL)
        if not match:
            print("Error: No JSON object found in the text.")
            return None
        
        json_candidate = match.group(0)

        try:
            json_data = json.loads(json_candidate)
        except json.JSONDecodeError as e:
            print(f"Error loading JSON from candidate '{json_candidate[:100]}...': {e}")
            return None
        except Exception as e:
            print("An unknown error occurred:", e)
            return None

        return json_data
