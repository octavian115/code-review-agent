from backend.nodes.static_tools import run_static_tools_node


def test_static_tools_skip_without_repo_path():
    result = run_static_tools_node({"repo_path": None})

    assert result["tool_results"] == []
    assert result["errors"] == []
