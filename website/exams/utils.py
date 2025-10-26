import os
from functools import lru_cache
from typing import List
from pydantic import BaseModel, Field
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from pydantic import RootModel
from langchain_openai import ChatOpenAI
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


@lru_cache(maxsize=1)
def get_llm_with_bigger_brains():
    # return ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     google_api_key=os.getenv("GEMINI_API_KEY"),
    #     max_output_tokens=1000,
    # )
    return ChatOpenAI(
        model="qwen/qwen2.5-vl-72b-instruct",  # or any OpenRouter model name
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        max_output_tokens=1000,
    )

# input
class SubjectiveAnswer(BaseModel):
    qs_id: int = Field(..., description="Question ID")
    qs: str = Field(..., description="The question text")
    qs_answer: str = Field(..., description="The student's answer text")
    qs_max_marks: float = Field(..., description="Maximum marks for the question")

# output
class SubjectiveEvaluation(BaseModel):
    qs_id: int = Field(..., description="Question ID")
    marks: float = Field(..., description="Marks awarded (0 to max marks)")


# ✅ Wrap list into a root model for parsing
class SubjectiveEvaluationList(RootModel[List[SubjectiveEvaluation]]):
    pass

# for this case
subjective_eval_parser = PydanticOutputParser(pydantic_object=SubjectiveEvaluationList)

# not using this time
parser = PydanticOutputParser(pydantic_object=SubjectiveEvaluation)


# ✅ Build the full evaluation chain
@lru_cache(maxsize=1)
def get_subjective_eval_chain():
    llm = get_llm_with_bigger_brains()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
            You are an academic evaluator. Your task is to evaluate student answers.

            INSTRUCTIONS:
            - You are given multiple subjective questions with answers and max marks.
            - Evaluate each answer based on relevance, completeness, clarity, and factual correctness.
            - Output must be a JSON list of objects with `qs_id` and `marks`.
            - Marks must be within 0 and `qs_max_marks`.
            - Be fair but concise; don't explain reasoning.

            Example output:
            [
                {{"qs_id": 1, "marks": 4.5}}
            ]

            The output should be strict json.

            {format_instructions}
            """),
        ("human", "{subjective_data_json}")
    ])

    # return LLMChain(
    #     llm = llm,
    #     prompt=prompt,
    #     output_parser=subjective_eval_parser
    # )

    return prompt | llm | subjective_eval_parser
