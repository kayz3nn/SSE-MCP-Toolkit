from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
import uvicorn
import requests


mcp = FastMCP("SSE MCP Server")


# Example filesystem tool
@mcp.tool()
async def list_files(directory: str) -> str:
    """List files in a directory.

    Args:
        directory: Path to the directory to list files from.
    """
    import os

    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


# Example API call tool
@mcp.tool()
async def fetch_data(url: str) -> str:
    """Fetch data from a given URL.

    Args:
        url: The URL to fetch data from.
    """

    try:
        # Fetch the data from the URL here
        return "Data fetched from URL: " + url
    except requests.RequestException as e:
        return f"Error fetching data: {str(e)}"


# Above are dummy tools. Add more tools as needed following the same pattern (function + mcp tool decorator).


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the MCP server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    port = 8080
    uvicorn.run(
        create_starlette_app(mcp._mcp_server, debug=True), host="0.0.0.0", port=port
    )

    print(f"SSE MCP Server is running on http://localhost:{port}/sse")
    print("You can connect to this server using an SSE client.")
