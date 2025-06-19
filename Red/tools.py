# %%
import warnings
from Red.defender_llm import run_command
from Red.model import MitreMethodUsed
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json

def handle_tool_call(response, ssh):
    tool_name = response.function
    args = response.arguments or {}
    tool_response = None
    mitre_method = None

    if tool_name == "run_command":
        tool_response, mitre_method = terminal_tool(args, ssh)
    elif tool_name == "terminate":
        tool_response = terminate_tool(args)
    elif tool_name == "web_search_tool":
        tool_response = handle_web_search_tool(args)
    else:
        raise ValueError(f"Unknown tool call: {tool_name}")
    
    return tool_response, mitre_method

def search_and_scrape(query: str, num_results=4, max_chars=2500):
    # DuckDuckGo search

    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"q": query}

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
    except Exception as e:
        return {"role": "function", "name": "web_search_tool", "content": f"Search failed: {str(e)}"}

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for result in soup.select(".result__title", limit=num_results):
        link = result.find("a", href=True)
        if not link:
            continue

        href = link["href"]
        title = link.get_text(strip=True)

        try:
            page = requests.get(href, headers=headers, timeout=5)
            page.raise_for_status()
            page_soup = BeautifulSoup(page.text, "html.parser")

            # Grab main text content, with fallback
            text = page_soup.get_text(separator="\n", strip=True)
            content = text[:max_chars] + "..." if len(text) > max_chars else text

        except Exception as e:
            content = f"Failed to fetch content: {str(e)}"

        results.append({
            "title": title,
            "link": href,
            "content": content
        })

    return {
        "role": "function",
        "name": "web_search_tool",
        "content": json.dumps(results, indent=2)
    }


# Needs SSH development

def handle_web_search_tool(arguments):
    return search_and_scrape(**arguments)

def terminal_tool(args, ssh):
    command_key = "command"
    tactic_key = "tactic_used"
    technique_key = "technique_used"

    if not args:
        raise ValueError("Tool call 'run_command' requires at least one argument but none were provided.")

    if command_key not in args:
        # find any other user-supplied key excluding tactic and technique
        other_keys = [k for k in args.keys() if k not in (tactic_key, technique_key)]
        if other_keys:
            command_key = other_keys[0]
            warnings.warn(
                "Tool call 'run_command' missing 'command'; using '{command_key}' as the command key instead."
            )
        else:
            raise ValueError(
                "Tool call 'run_command' requires a 'command' argument but only optional keys were provided."
            )

    command = args[command_key]
    command_response = run_command(command, ssh)
    tool_response = {
        "role": "function",
        "name": "run_command",
        "content": command_response
    }

    mitre_method = MitreMethodUsed()


    if tactic_key in args:
        mitre_method.tactic_used = args[tactic_key]
    if technique_key in args:
        mitre_method.technique_used = args[technique_key]

    return tool_response, mitre_method

def terminate_tool(args):
    if args:
        warnings.warn("Tool call 'terminate' does not require any arguments. Ignoring provided arguments.")
    terminate_response = "Sangris feels like it has completed its task and is now terminating the session."
    print(terminate_response)
    tool_response = {
        "role": "function",
        "name": "terminate",
        "content": terminate_response
    }
    return tool_response


# %%
