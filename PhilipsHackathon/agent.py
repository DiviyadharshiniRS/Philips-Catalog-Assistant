
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

from tools.catalog_tools import (
    check_quote,
    check_export,
    find_expired_products
)

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"


# -----------------------------------------
# TOOL 4: SEARCH COMPANY POLICIES
# -----------------------------------------

def search_policy(query):

    filepath = Path("database/all_policies.txt")

    if not filepath.exists():
        return {"error": "Policy document not found"}

    text = filepath.read_text(encoding="utf-8")

    keywords = [
        word.lower().strip(".,?!")
        for word in query.split()
        if len(word) > 3
    ]

    lines = text.splitlines()
    matches = []

    for i, line in enumerate(lines):

        score = sum(
            1 for word in keywords
            if word in line.lower()
        )

        if score > 0:

            start = max(0, i - 1)
            end = min(len(lines), i + 3)

            section = "\n".join(lines[start:end])

            matches.append((score, section))

    matches.sort(key=lambda x: x[0], reverse=True)

    results = []

    for score, section in matches[:5]:

        if section not in results:
            results.append(section)

    return {
        "query": query,
        "policy_evidence": results
    }


# -----------------------------------------
# DEFINE AI AGENT TOOLS
# -----------------------------------------

tools = [

    {
        "type": "function",
        "function": {
            "name": "check_quote",
            "description": "Check pricing eligibility for a product option in a country.",
            "parameters": {
                "type": "object",
                "properties": {
                    "option_id": {"type": "string"},
                    "country": {"type": "string"},
                    "company": {
                        "type": "string",
                        "enum": ["CircuitNova", "Hearthwell"]
                    }
                },
                "required": ["option_id", "country"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "check_export",
            "description": "Check whether a product is export controlled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    "company": {
                        "type": "string",
                        "enum": ["CircuitNova", "Hearthwell"]
                    }
                },
                "required": ["product_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "find_expired_products",
            "description": "Find expired products that are still listed for sale.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "enum": ["CircuitNova", "Hearthwell"]
                    }
                },
                "required": ["company"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Search company policy documents for relevant rules and sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }
]


# -----------------------------------------
# TOOL EXECUTION
# -----------------------------------------

def execute_tool(name, arguments):

    if name == "check_quote":
        return check_quote(**arguments)

    elif name == "check_export":
        return check_export(**arguments)

    elif name == "find_expired_products":
        return find_expired_products(**arguments)

    elif name == "search_policy":
        return search_policy(**arguments)

    return {"error": "Unknown tool"}


# -----------------------------------------
# AGENT SYSTEM PROMPT
# -----------------------------------------


SYSTEM_PROMPT = """
You are Philips Catalog Assistant for the presales team.

You work with CircuitNova and Hearthwell.

MANDATORY TOOL-CALLING RULES:

1. If the user asks whether an option can be quoted:
   - ALWAYS call check_quote first.
   - ALWAYS call search_policy for the relevant pricing rules.
   - Never answer using assumptions.

2. If the user asks about export control:
   - ALWAYS call check_export.
   - ALWAYS call search_policy for export control rules.
   - EC-0 = Not controlled.
   - EC-1 = Controlled mass-market technology.
   - EC-2 = Controlled strong encryption.
   - EC-1 may be sold anywhere except embargoed countries.
   - EC-2 requires a licence outside the EU.
   - Never claim EC-1 requires a licence.

3. If the user asks about expired products:
   - Call find_expired_products.
   - Report the actual count and product IDs.
   - Call search_policy for lifecycle rules.

4. Never invent product information, prices or policy sections.

5. Always distinguish NOT FOUND from NOT QUOTABLE.

6. Never claim that a product is fully approved for quotation
   based only on a pricing check.

7. Use the actual tool results as your evidence.

8. If a tool returns no information, clearly say NOT FOUND.

ANSWER FORMAT:

Decision:
Reason:
Product/Option:
Evidence:
Policy Reference:
"""




# -----------------------------------------
# MAIN AGENT
# -----------------------------------------



# -----------------------------------------
# MAIN AGENT WITH EXECUTION TRACE
# -----------------------------------------

def ask_agent_with_trace(question):

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    # Store every tool execution in order
    execution_history = []

    for step in range(6):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )

        message = response.choices[0].message

        # No more tool calls: generate final answer
        if not message.tool_calls:

            if message.content:
                return {
                    "answer": message.content,
                    "execution_history": execution_history
                }

            final_response = client.chat.completions.create(
                model=MODEL,
                messages=messages + [{
                    "role": "user",
                    "content": (
                        "Provide the final answer using the tool "
                        "results above. Do not invent information."
                    )
                }],
                tool_choice="none",
                temperature=0
            )

            answer = (
                final_response.choices[0].message.content
                or "Unable to generate final answer."
            )

            return {
                "answer": answer,
                "execution_history": execution_history
            }

        # Save assistant tool-call message
        messages.append(
            message.model_dump(exclude_none=True)
        )

        # Execute requested tools
        for tool_call in message.tool_calls:

            name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            print(f"\n[Agent calling tool: {name}]")
            print("Arguments:", arguments)

            try:
                result = execute_tool(name, arguments)
                execution_status = "SUCCESS"

            except Exception as error:
                result = {"error": str(error)}
                execution_status = "ERROR"

            # Preserve execution details for Streamlit
            execution_history.append({
                "tool_name": name,
                "arguments": arguments,
                "status": execution_status,
                "result": result
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, default=str)
            })

    return {
        "answer": "Agent reached its tool-call limit. Please retry.",
        "execution_history": execution_history
    }


# Existing function preserved for terminal compatibility
def ask_agent(question):

    result = ask_agent_with_trace(question)

    return result["answer"]

# -----------------------------------------
# CHAT LOOP
# -----------------------------------------

if __name__ == "__main__":

    print("\n====================================")
    print("   PHILIPS CATALOG ASSISTANT")
    print("====================================")

    print("Type 'exit' to quit.\n")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() == "exit":
            print("Assistant: Goodbye!")
            break

        if not question:
            continue

        try:
            answer = ask_agent(question)

            print("\nAssistant:")
            print(answer)

        except Exception as error:
            print("\nAgent error:", error)
