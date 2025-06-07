from mcp import ClientSession
from mcp.client.sse import sse_client
import json
from typing import Optional
from enum import Enum


class McpSseClient:
    class Provider(str, Enum):
        OLLAMA = "ollama"
        # TODO: Add other providers like OpenAI, etc.

    class Model(str, Enum):
        LLAMA3_2 = "llama3.2"
        # TODO: Add other models like GPT-4, etc.

    def __init__(
        self,
        provider: Provider = Provider.OLLAMA,
        model: Model = Model.LLAMA3_2,
        server_url: str = "http://localhost:8080/sse",
    ):
        """Initialize the MCP client

        Args:
            provider: LLM provider (default: Provider.OLLAMA)
            model: Model name to use (default: Model.LLAMA3_2)
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.provider = provider
        self.model = model
        self.server_url = server_url

    async def connect_to_sse_server(self) -> None:
        """Connect to an MCP server

        Args:
            server_url: URL of the SSE MCP server to connect to
        """

        # Manually create the client session to avoid closing the connection when exiting the context
        self._streams_context = sse_client(url=self.server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        await self.session.initialize()

    async def close_session(self) -> None:
        """Close the MCP session"""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    def __exit__(self) -> None:
        """Exit the client and clean up resources"""
        import asyncio

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.close_session())

    async def register_tools(self) -> tuple[str, list[dict]]:
        """Register tools from the MCP server"""

        response = await self.session.list_tools()
        _, _, tools = response
        _, tools_list = tools

        from src.ollama_agent.tools_registry import OllamaToolsRegistry

        tools_registry = OllamaToolsRegistry().parse_from_mcp_function_tool(tools_list)
        self.tools = [tool.to_dict() for tool in tools_registry]

        return f"Registered {len(self.tools)} tools from MCP server.", self.tools

    async def process_query(self, query: str):
        """Process a query using the selected LLM provider and tools and returns the prompt response"""

        if self.provider == McpSseClient.Provider.OLLAMA.value:
            from src.ollama_agent.agent import OllamaAgent

            self.agent = OllamaAgent(
                model=self.model,
                tools=[] if not hasattr(self, "tools") else self.tools,
            )
        else:
            # TODO: Add support for other providers like OpenAI, etc.
            raise ValueError(f"Unsupported provider: {self.provider}")

        return await self.agent.chat(query)

    async def execute_tool_calls(self, tool_calls: list):
        try:
            for tool_call in tool_calls:
                function_to_call = next(
                    (
                        tool
                        for tool in self.agent.tools
                        if tool.get("function", {}).get("name")
                        == tool_call.function.name
                    ),
                    None,
                )
                if not function_to_call:
                    return f"Function {tool_call.function.name} is not available."

                output = await self.session.call_tool(
                    tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )

                return output
        except Exception as e:
            return f"Error executing tool calls: {str(e)}"

    async def start_console_chat_loop(self):
        """Run an interactive chat loop in the console"""

        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)

                print(
                    json.dumps(
                        {
                            "query": query,
                            "message_content": response.message.content,
                        },
                        indent=2,
                    )
                )
                print("\nTool Calls:")
                print(response.message.tool_calls)

                execute_tool_calls = (
                    input("\nDo you want to execute the tool calls? (yes/no): ")
                    .strip()
                    .lower()
                )
                if execute_tool_calls == "yes":
                    print("\nExecuting tool calls...")
                    if response.message.tool_calls:
                        output = await self.execute_tool_calls(
                            response.message.tool_calls
                        )

                        print("\nTool Call Raw Output:")
                        print(output)

                        print("\nTool Call Output (formatted):")
                        try:
                            print(json.dumps(output, indent=2))
                        except Exception:
                            print(output.content[0].text)

            except Exception as e:
                print(f"\nError: {str(e)}")
