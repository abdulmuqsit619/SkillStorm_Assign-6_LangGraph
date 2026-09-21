import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from policy_assistant.graph.graph import build_graph_with_memory
from policy_assistant.graph.state import AssistantState


def main() -> None:
    app = build_graph_with_memory()

    # One thread ID represents one conversation.
    thread_id = str(uuid.uuid4())

    graph_config: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    print("=" * 50)
    print("LangGraph Policy Assistant")
    print("=" * 50)
    print("Ask a question about the policy documents.")
    print("Type 'quit' or 'exit' to stop.")
    print()

    while True:
        question = input("You > ").strip()

        if not question:
            continue

        if question.lower() in {
            "quit",
            "exit",
        }:
            print("Goodbye!")
            break

        state: AssistantState = {
            "question": question,
            "messages": [
                HumanMessage(content=question)
            ],
            "documents": [],
            "retrieval_attempts": 0,
            "sources": [],
        }

        result = app.invoke(
            state,
            config=graph_config,
        )

        answer = result.get(
            "answer",
            "No answer was generated.",
        )

        print()
        print(f"Assistant > {answer}")

        sources = result.get(
            "sources",
            [],
        )

        if sources:
            print()
            print("Sources:")

            for source in sorted(set(sources)):
                print(f"- {source}")

        print()


if __name__ == "__main__":
    main()