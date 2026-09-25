"""Independent stdio MCP client for SpendGuard calculation tools."""

from pathlib import Path
from typing import Any, get_args

from fastmcp import Client

from spendguard.models import CalculationToolName


SERVER_PATH = Path(__file__).with_name("mcp_server.py")


async def list_calculation_tools() -> list[str]:
    """Registered calculation-tool names."""

    async with Client(SERVER_PATH) as client:
        tools = await client.list_tools()
    calculation_names = set(get_args(CalculationToolName))
    return [tool.name for tool in tools if tool.name in calculation_names]


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
