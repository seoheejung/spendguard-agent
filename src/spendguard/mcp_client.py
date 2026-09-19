"""Independent stdio MCP client for SpendGuard calculation tools."""

from pathlib import Path
from typing import Any

from fastmcp import Client


SERVER_PATH = Path(__file__).with_name("mcp_server.py")


async def list_calculation_tools() -> list[str]:
    """Registered calculation-tool names."""

    async with Client(SERVER_PATH) as client:
        tools = await client.list_tools()
    return [tool.name for tool in tools]


async def call_calculation_tool(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Calculation result through an independent stdio client."""

    async with Client(SERVER_PATH) as client:
        result = await client.call_tool(name, {"data": data})
    if not isinstance(result.data, dict):
        fields = ("inputs", "formula", "intermediate", "result")
        if all(hasattr(result.data, field) for field in fields):
            return {field: getattr(result.data, field) for field in fields}
        raise TypeError("MCP calculation tool returned an invalid result shape")
    return result.data
