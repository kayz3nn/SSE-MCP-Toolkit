from src.mcp_sse_client.client import McpSseClient


async def main():
    import streamlit as st

    client = McpSseClient(
        provider="ollama", model="llama3.2", server_url="http://localhost:8080/sse"
    )
    await client.connect_to_sse_server()
    await client.register_tools()

    st.title("MCP SSE Client")
    st.write("This is a Streamlit app for the MCP SSE Client.")

    query = st.text_input("Enter your query:")
    if st.button("Submit"):
        if query:
            response = await client.process_query(query)
            st.json(
                {
                    "query": query,
                    "message_content": response.message.content,
                    "tool_calls": response.message.tool_calls,
                }
            )
            response_tool_calls = await client.execute_tool_calls(
                response.message.tool_calls
            )
            st.write("Tool Call Raw Output:")
            st.json(response_tool_calls)
            st.write("Tool Call Output:")
            try:
                st.json(response_tool_calls)
            except Exception:
                st.write(response_tool_calls.content[0].text)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
