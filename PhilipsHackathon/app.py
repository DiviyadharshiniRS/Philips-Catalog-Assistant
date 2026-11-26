
import streamlit as st
import pandas as pd

from agent import ask_agent_with_trace

st.set_page_config(
    page_title="Philips Catalog Assistant",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Philips Catalog Assistant")
st.caption(
    "Agentic RAG | Product Catalog | "
    "SQL Transparency | Policy-Based Decision Support"
)

st.divider()


# -----------------------------------------
# DISPLAY TOOL EXECUTION DETAILS
# -----------------------------------------

def display_execution_history(history):

    st.subheader("Investigation Details")

    if not history:
        st.info("No tools were executed for this question.")
        return

    for index, execution in enumerate(history, start=1):

        tool_name = execution.get("tool_name", "Unknown tool")
        arguments = execution.get("arguments", {})
        status = execution.get("status", "UNKNOWN")
        result = execution.get("result", {})

        with st.expander(
            f"Step {index}: {tool_name} — {status}",
            expanded=(index == 1)
        ):

            st.markdown("**Tool:**")
            st.code(tool_name)

            st.markdown("**Tool arguments:**")
            st.json(arguments)

            query_details = result.get("query_details")

            if query_details:

                st.markdown("### SQL Query")

                st.code(
                    query_details.get("sql_query", ""),
                    language="sql"
                )

                st.markdown("**Query parameters:**")
                st.json(query_details.get("parameters", []))

                st.markdown("**Database tables accessed:**")
                st.write(
                    query_details.get("database_tables", [])
                )

                st.metric(
                    "Rows returned",
                    query_details.get("rows_returned", 0)
                )

            else:
                st.caption(
                    "This tool did not execute a database SQL query."
                )

            st.markdown("### Retrieved Evidence")

            evidence = result.get("evidence")

            if evidence:
                if isinstance(evidence, list):
                    st.dataframe(
                        pd.DataFrame(evidence),
                        use_container_width=True
                    )
                elif isinstance(evidence, dict):
                    st.json(evidence)

            products = result.get("products")

            if products is not None:
                st.metric("Products found", result.get("count", len(products)))

                if products:
                    st.dataframe(
                        pd.DataFrame(products),
                        use_container_width=True
                    )

            policy_evidence = result.get("policy_evidence")

            if policy_evidence:
                st.markdown("### Policy Evidence")

                for section in policy_evidence:
                    st.markdown(section)

            if result.get("error"):
                st.error(result["error"])

            # Show remaining tool result fields
            st.markdown("### Complete Tool Result")
            st.json(result)


# -----------------------------------------
# CHAT HISTORY
# -----------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------------------
# SIDEBAR
# -----------------------------------------

with st.sidebar:

    st.header("About")

    st.write(
        "Ask questions about product quotation, "
        "export controls, product lifecycle, "
        "pricing and company policies."
    )

    st.divider()

    st.subheader("Example Questions")

    st.markdown("""
    - Can I quote EO-10001 in Denmark?
    - Is EP-1023 export-controlled?
    - Which expired CircuitNova products are still on sale?
    """)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# -----------------------------------------
# DISPLAY PREVIOUS CONVERSATION
# -----------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":
            display_execution_history(
                message.get("execution_history", [])
            )


# -----------------------------------------
# CHAT INPUT
# -----------------------------------------

question = st.chat_input(
    "Ask your catalog question..."
)


# -----------------------------------------
# PROCESS USER QUESTION
# -----------------------------------------

if question:

    # Display and store user question
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # Run agent and capture execution history
    with st.chat_message("assistant"):

        with st.spinner(
            "Analyzing catalog data and company policies..."
        ):

            try:

                result = ask_agent_with_trace(question)

                answer = result["answer"]

                execution_history = result["execution_history"]

                st.markdown(answer)

                display_execution_history(execution_history)

                # Store answer and execution details
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "execution_history": execution_history
                })

            except Exception as error:

                error_message = f"Error: {str(error)}"

                st.error(error_message)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "execution_history": []
                })
