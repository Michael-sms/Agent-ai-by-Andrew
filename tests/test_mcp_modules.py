from agent_mcp.server import calculator, health_check, list_tools, web_search


def test_mcp_health_check_ok():
    result = health_check()
    assert result["status"] == "ok"


def test_mcp_list_tools_contains_core_tools():
    result = list_tools()
    tools = result["tools"]
    assert "calculator" in tools
    assert "file_read" in tools
    assert "file_write" in tools
    assert "data_analysis" in tools
    assert "web_search" in tools


def test_mcp_calculator_runs():
    result = calculator("sqrt(256)")
    assert result["tool_name"] == "calculator"
    assert result["success"] is True
    assert "16" in result["output"]


def test_mcp_web_search_callable():
    result = web_search("python", max_results=1)
    assert result["tool_name"] == "web_search"
    assert isinstance(result["success"], bool)
