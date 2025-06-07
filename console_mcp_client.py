from src.mcp_sse_client.client import McpSseClient

if __name__ == "__main__":
    client = McpSseClient(
        provider=McpSseClient.Provider.OLLAMA,
        model=McpSseClient.Model.LLAMA3_2,
        server_url="http://localhost:8080/sse",
    )

    async def main():
        await client.connect_to_sse_server()
        await client.register_tools()
        await client.start_console_chat_loop()

    import asyncio

    asyncio.run(main())
