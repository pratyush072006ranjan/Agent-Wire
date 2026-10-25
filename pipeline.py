import re
from langchain_core.messages import ToolMessage
from agents import build_reader_agent,build_search_agent,critic_chain,writer_chain
from tools import scrape_url as scrape_url_tool

def get_message_text(message):
    content = message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    return str(content)


def get_tool_output_text(messages):
    """
    Pull the raw output of every tool call made during an agent run
    (e.g. the Title/URL/Snippet blocks from web_search, or the scraped
    page text from scrape_url). This is the ground truth for things like
    URLs — the agent's own final summary message is an LLM paraphrase and
    can drop or mangle links even when the tool itself returned them fine.
    Returns "" if the agent never actually called a tool.
    """
    parts = []
    for m in messages:
        if isinstance(m, ToolMessage):
            parts.append(get_message_text(m))
    return "\n----\n".join(p for p in parts if p and p.strip())


def looks_like_scrape_failure(text: str) -> bool:
    if not text or not text.strip():
        return True
    return "could not scrape url" in text.lower()


def extract_urls(text: str):
    """Pull URLs out of the raw web_search tool output (lines like 'URL:https://...')."""
    return re.findall(r"URL:\s*(\S+)", text)

def run_research_pipeline(topic:str, on_step=None)->dict:
    """
    on_step: optional callback(step_name:str, payload:dict) fired after each
    stage completes, so a UI can render progress live. Fully optional —
    calling this exactly as before still works unchanged.
    """

    def _notify(step_name, **payload):
        if on_step:
            on_step(step_name, payload)

    state={}

    #  Step 1: Search Agent working
    print("\n"+"="*50)
    print("Step 1 - search agent is working...")
    print("="*50)

    search_agent=build_search_agent()
    search_result=search_agent.invoke({
        "messages":[("user",f"Find recent, reliable and detailed information about: {topic}")]
    })

    raw_search_output = get_tool_output_text(search_result["messages"])
    state["search_results"] = raw_search_output if raw_search_output.strip() else get_message_text(
        search_result["messages"][-1]
    )

    print("\n search result",state['search_results'])
    _notify("search", text=state["search_results"])


    #  Step 2: Reader Chain

    print("\n"+"="*50)
    print("Step 2 - Reader Agent is scraping top resources...")
    print("="*50)

    reader_agent= build_reader_agent()
    reader_result=reader_agent.invoke({
        "messages":[("user",
        f"Based on the following search results about '{topic}', "
        f"Pick the most relevant URL and scrape it for deeper content.\n\n"
        f"Search Results:\n{state['search_results'][:800]}"
        )]
    })

    raw_scrape_output = get_tool_output_text(reader_result["messages"])
    state["scraped_content"] = raw_scrape_output if raw_scrape_output.strip() else get_message_text(
        reader_result["messages"][-1]
    )

    # If the agent's chosen URL failed (e.g. 404), don't give up — try the other URLs the search step actually found, scraping them directly.
    if looks_like_scrape_failure(state["scraped_content"]):
        print("\nFirst scrape attempt failed, trying other search result URLs...")
        for candidate_url in extract_urls(state["search_results"]):
            try:
                attempt = scrape_url_tool.invoke({"url": candidate_url})
            except Exception as e:
                attempt = f"could not scrape URL:{e}"
            if not looks_like_scrape_failure(attempt):
                state["scraped_content"] = f"Scraped from: {candidate_url}\n\n{attempt}"
                break

    print("\nScraped Content:\n",state['scraped_content'])
    _notify("read", text=state["scraped_content"])


    #  Step 3: Writer Chain


    print("\n"+"="*50)
    print("Step 3 - Writer is drafting the report...")
    print("="*50)

    research_combined=(
        f"SEARCH RESULTS:\n {state['search_results']} \n \n"
        f"DETAILED SCRAPED CONTENT:\n {state['scraped_content']}"
    )

    state["report"]=writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print(" \n Final Report \n",state['report'])
    _notify("write", text=state["report"])


    # Critic Report

    
    print("\n"+"="*50)
    print("Step 4 - Critic is reviewing the report...")
    print("="*50)

    state["feedback"]=critic_chain.invoke({
        "report":state['report']
    })

    print("\n Critic Report \n",state['feedback'])
    _notify("critique", text=state["feedback"])

    return state



if __name__=="__main__":
    topic = input("\nEnter a research topic: ")
    run_research_pipeline(topic)