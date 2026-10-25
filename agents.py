import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)

from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import scrape_url,web_search


llm=ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview",temperature=0)

SEARCH_SYSTEM_PROMPT = (
    "You are a research search agent. Use the web_search tool to gather sources. "
    "In your final answer, list every source you used with its exact URL copied "
    "verbatim from the tool output (never shorten, paraphrase, or omit a URL), "
    "along with a short summary of what each source says. Do not invent URLs "
    "that did not come from a tool result."
)

READER_SYSTEM_PROMPT = (
    "You are a research reading agent. Use the scrape_url tool to fetch the full "
    "content of the single most relevant URL you were given. In your final answer, "
    "state the exact URL you scraped (verbatim), then report the scraped content "
    "in detail. If scrape_url reports a failure (e.g. a 404 or connection error), "
    "say plainly that the scrape failed and name the URL and the error — do not "
    "fabricate content and do not claim success."
)

# 1st Agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=SEARCH_SYSTEM_PROMPT,
    )

# 2nd Agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=READER_SYSTEM_PROMPT,
    )


# writer chain
writer_prompt=ChatPromptTemplate.from_messages([
    ("system","You are an expert research writer. Write clear, structured and insightful reports."),
    ("human","""Write a detailed research report on the topic below.

    Topic:{topic}
    
    Research Gathered:{research}

    Structure the report as :
    - Introduction
    - Key Findings (minimum 3 well-explained points)
    - Conclusion
    - Sources (list every URL that literally appears in the Research Gathered
      text above, exactly as written. Do not paraphrase, shorten, or invent
      URLs. If the Research Gathered text truly contains no URLs, write
      "No source URLs were returned by the search step." and nothing else
      in that section.)

    Be detailed, factual and professional
    """),
])

writer_chain=writer_prompt | llm | StrOutputParser()


# critic_chain
critic_prompt=ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain=critic_prompt | llm | StrOutputParser()