from typing import List


class OllamaTool:
    """Represents a tool for interacting with the Ollama model."""

    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_dict(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class OllamaToolsRegistry:
    """Registry for managing Ollama tools."""

    def __init__(self):
        self.tools: List[OllamaTool] = []

    def parse_from_mcp_function_tool(self, tools: List[dict]) -> List[OllamaTool]:
        """Parse the tool from MCP Tool Object."""

        try:
            for tool in tools:
                self.tools.append(
                    OllamaTool(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.inputSchema,
                    )
                )
        except Exception as e:
            print(f"Error parsing tools: {e}")
            print(f"Raw tools data: {tools}")

        return self.tools
