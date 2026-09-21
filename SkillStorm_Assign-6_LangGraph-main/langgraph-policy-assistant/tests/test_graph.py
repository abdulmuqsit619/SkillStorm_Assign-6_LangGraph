from policy_assistant.graph.graph import build_graph


def test_graph_has_expected_nodes():
    app = build_graph()

    graph = app.get_graph()

    node_names = set(
        graph.nodes.keys()
    )

    assert "contextualize" in node_names
    assert "retrieve" in node_names
    assert "reframe" in node_names
    assert "answer" in node_names
    assert "refuse" in node_names


def test_graph_has_retry_cycle():
    app = build_graph()

    graph = app.get_graph()

    edges = {
        (edge.source, edge.target)
        for edge in graph.edges
    }

    assert (
        "contextualize",
        "retrieve",
    ) in edges

    assert (
        "reframe",
        "retrieve",
    ) in edges

    assert (
        "answer",
        "__end__",
    ) in edges

    assert (
        "refuse",
        "__end__",
    ) in edges