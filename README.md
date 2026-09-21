Assignment: Rebuild the RAG Assistant as a LangGraph Agent
Objective
A command-line assistant that answers policy questions from a document set, where the control flow is a LangGraph graph rather than a straight line, and the document index is built in memory at startup rather than hosted as a managed service. It cites where its answers came from, it gets a second attempt when its first search comes back weak, and it refuses to answer when the documents do not cover the question.

Starting point
You have two options. Both are fine, and neither is worth more credit.

Reuse the policy assistant you built in class. It is in the class Github. Copy it into a new repository of your own and rebuild from there — you already have a working Bedrock client, a system prompt, and a set of source documents to model yours on.
Start fresh. If you would rather write it from scratch, do. There is not much scaffolding here, and you may learn more by building each piece.
Either way you are judged on the requirements below, not on how much you kept.

Requirements
The knowledge base
The index must be built in memory when the program starts, from files in your repository, and disappear when it stops.
No managed vector store, no hosted Knowledge Base, no external database. Nothing this assignment creates should appear on a bill or need tearing down. Cost is the reason: a hosted vector store charges a minimum capacity floor around the clock whether you query it or not, which is a poor trade for a handful of documents.
Documents must be files in the repository, not string literals inside a .py file. Loading them is something you should be able to test.
At least one question a user might reasonably ask must be deliberately not covered by your documents. You will need it for requirement 12, and you should note it in your README so it can be checked.
The graph
Control flow must be a compiled LangGraph StateGraph.
The state must be a typed schema, and anything that accumulates across nodes must actually accumulate rather than being overwritten.
Routing must be conditional — driven by what is in the state, not a fixed sequence. A graph whose nodes always run in the same order is a chain with extra steps.
The graph must contain at least one cycle: when the first search comes back weak, the assistant gets another attempt at finding something better within the same user question. How you decide "weak" and what you change on the retry is your call — a reworded query, a broader one, a different phrasing of the user's question. Say what you chose in your README.
That cycle must be bounded. It must be impossible for one user question to retry forever, no matter what comes back. Decide the limit, and decide what the assistant says when it runs out.
Answering
Answers must be built from retrieved text, and the retrieved text must actually reach the model. Retrieval that runs but does not influence the answer does not count.
The assistant must refuse when the documents do not support an answer. Ask it the question from requirement 5 and it should say it does not know, rather than producing something plausible. This is the hardest requirement here and the most important — budget time for it.
Answers must cite their sources — name the document each supporting passage came from, so a user can go read it.
The assistant must handle a multi-turn conversation. A follow-up that only makes sense in context ("is that the same for members?") should work.
The repository
Source code separate from tests. How you split the source into modules is your call, and part of what is being assessed.
A dependency file — pyproject.toml.
A .gitignore that excludes your virtual environment.
A README with setup and run instructions, your answers to requirements 5 and 9, and a diagram of your graph showing every node and edge. Draw it in ASCII by hand, or have LangGraph generate it — a compiled graph can emit Mermaid, and GitHub renders Mermaid inside a fenced ```mermaid block.
pytest must pass on a fresh clone, run from the repository root.
Your tests must pass without AWS credentials and without network access. That rules out testing the model's answers, which is the point — test what is deterministic. At minimum, cover these four:
your documents load and split as expected,
your graph has the nodes and edges you think it has,
your routing decision, given a state you construct by hand,
your retry bound, given a state that has already used its attempts.
Credentials
No AWS keys in the repository. Region, model ids and credentials come from the environment. Your README should say which variables are needed; a committed .env.example with empty values is a good pattern.
Deliverable
A link to a public GitHub repository, submitted on Canvas as a URL — nothing else.

Time expectation
~2 hours.