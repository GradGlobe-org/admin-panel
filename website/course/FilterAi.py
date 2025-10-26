# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import Optional, Annotated
from enum import Enum
from pydantic import Field
from functools import lru_cache
import os
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class ProgramLevel(str, Enum):
    bachelors = "bachelors"
    masters = "masters"


class Country(str, Enum):
    Australia = "Australia"
    Canada = "Canada"
    France = "France"
    Germany = "Germany"
    Ireland = "Ireland"
    Italy = "Italy"
    Netherlands = "Netherlands"
    Poland = "Poland"
    Russia = "Russia"
    Spain = "Spain"
    Sweden = "Sweden"
    Switzerland = "Switzerland"
    Ukraine = "Ukraine"
    UAE = "United Arab Emirates"
    UK = "United Kingdom"
    USA = "United States"


class SearchParams(BaseModel):
    university_name: Optional[str] = Field(None, description="Name of the university")
    program_name: Optional[str] = Field(None, description="Name of the program/course")

    # Make program_level mandatory, allow only ProgramLevel Enum
    program_level: Annotated[
        Optional[ProgramLevel],
        Field(description="Program level, e.g., bachelors, masters"),
    ] = None

    # Country restricted to Country Enum
    country_name: Annotated[
        Optional[Country], Field(description="Country name from allowed list")
    ] = None

    duration_min: Annotated[
        Optional[int], Field(ge=0, description="Minimum duration in years")
    ] = None
    duration_max: Annotated[
        Optional[int], Field(ge=0, description="Maximum duration in years")
    ] = None

    tuition_fees_min: Annotated[
        Optional[int], Field(ge=0, description="Minimum tuition fees in USD")
    ] = None
    tuition_fees_max: Annotated[
        Optional[int], Field(ge=0, description="Maximum tuition fees")
    ] = None

    gpa_min: Annotated[
        Optional[float], Field(ge=0.0, le=4.0, description="Minimum GPA")
    ] = None
    gpa_max: Annotated[
        Optional[float], Field(ge=0.0, le=4.0, description="Maximum GPA")
    ] = None

    sat_min: Annotated[
        Optional[float], Field(ge=400, le=1600, description="Minimum SAT score")
    ] = None
    sat_max: Annotated[
        Optional[float], Field(ge=400, le=1600, description="Maximum SAT score")
    ] = None

    act_min: Annotated[
        Optional[float], Field(ge=1, le=36, description="Minimum ACT score")
    ] = None
    act_max: Annotated[
        Optional[float], Field(ge=1, le=36, description="Maximum ACT score")
    ] = None

    ielts_min: Annotated[
        Optional[float], Field(ge=0.0, le=9.0, description="Minimum IELTS score")
    ] = None
    ielts_max: Annotated[
        Optional[float], Field(ge=0.0, le=9.0, description="Maximum IELTS score")
    ] = None

    limit_val: Annotated[
        int, Field(gt=0, le=200, description="Pagination limit, max 200")
    ] = 100
    offset_val: Annotated[int, Field(ge=0, description="Pagination offset")] = 0

    class Config:
        use_enum_values = True


parser = PydanticOutputParser(pydantic_object=SearchParams)


@lru_cache(maxsize=1)
def get_llm():
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash-lite",
    #     google_api_key=os.getenv("GEMINI_API_KEY"),
    #     max_output_tokens=500,
    # )
    llm = ChatOpenAI(
        model="qwen/qwen2.5-vl-72b-instruct",  # or any OpenRouter model name
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        max_output_tokens=500,
    )
    return llm


@lru_cache(maxsize=1)
def get_llm_with_bigger_brains():
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     google_api_key=os.getenv("GEMINI_API_KEY"),
    #     max_output_tokens=500,
    # )
    llm = ChatOpenAI(
        model="qwen/qwen2.5-vl-72b-instruct",  # or any OpenRouter model name
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        max_output_tokens=500,
    )
    return llm


@lru_cache(maxsize=1)
def get_chain():
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a precise query parser for university search. Your ONLY task is to extract EXACTLY what the user explicitly mentions.

            CRITICAL RULES:
            1. ONLY fill fields that are EXPLICITLY mentioned in the user query
            2. NEVER assume or infer any information not directly stated
            3. If a field is not mentioned, leave it as null/None
            4. For program_level and country_name, ONLY use the exact values from the allowed enums
            5. If the user mentions general terms like "bachelors" or "masters", map to ProgramLevel enum
            6. If the user mentions country names, map to exact Country enum values
            7. DO NOT invent university names, program names, scores, or any other details
            8. If the query is too vague, only fill what's explicitly stated

            EXAMPLES:
            - "I want to study bachelors in USA" → program_level: "bachelors", country_name: "United States"
            - "Looking for computer science masters" → program_name: "computer science", program_level: "masters"
            - "Universities with low tuition" → tuition_fees_max: (some reasonable low value, but ONLY if "low" is explicitly mentioned)
            - "Study abroad" → ALL fields None except maybe program_level if implied

            Your output MUST be strictly limited to the JSON format with NO additional text.
            {format_instructions}
            """,
            ),
            (
                "human",
                "{query}",
            ),
        ]
    )

    return prompt | llm | parser


class ChatResponseToUser(BaseModel):
    response_text: Annotated[
        str,
        Field(description="Descriptive response to the user"),
    ]
    should_suggest: Annotated[
        bool,
        Field(
            description="Whether to search universities/courses, crucial for system to query and get data"
        ),
    ] = True
    university_name: Optional[str] = Field(None, description="Name of the university")
    program_name: Optional[str] = Field(None, description="Name of the program/course")

    program_level: Annotated[
        Optional[ProgramLevel],
        Field(description="Program level, e.g., bachelors, masters"),
    ] = None

    country_name: Annotated[
        Optional[Country], Field(description="Country name from allowed list")
    ] = None

    duration_min: Annotated[
        Optional[int], Field(ge=0, description="Minimum duration in years")
    ] = None
    duration_max: Annotated[
        Optional[int], Field(ge=0, description="Maximum duration in years")
    ] = None

    tuition_fees_min: Annotated[
        Optional[int], Field(ge=0, description="Minimum tuition fees in USD")
    ] = None
    tuition_fees_max: Annotated[
        Optional[int], Field(ge=0, description="Maximum tuition fees")
    ] = None

    class Config:
        use_enum_values = True


chat_parser = PydanticOutputParser(pydantic_object=ChatResponseToUser)


@lru_cache(maxsize=1)
def chat_chain():
    llm = get_llm_with_bigger_brains()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a chatbot for GRADGLOBE.org.
                Your ONLY job is to output structured JSON that matches the schema exactly.

                Make sure:
                - "response_text" is short and sweet (≤ 50 words).
                - "should_suggest" is to define wether to suggest any university or course to the user, True == yes, False == no
                - Leave other fields null unless explicitly provided by the user.
                - Output strictly valid JSON, with no extra commentary, no markdown, no text before or after.
                
                {format_instructions}
                """,
            ),
            ("human", "{query}"),
        ]
    )
    return prompt | llm | chat_parser
