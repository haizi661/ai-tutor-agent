# Architecture Overview

## Layered Structure

The project now follows a layered package layout to make collaboration and extension safer:

- `ai_tutor_agent/core/`: domain-neutral contracts and shared structures.
  - `events.py`: runtime event model.
  - `ports.py`: I/O contracts (`EventSink`, `AnswerProvider`) and runtime context.
  - `state.py`: graph state schema.
  - `text.py`: model output normalization helpers.
- `ai_tutor_agent/nodes/`: LangGraph node builders (`tutor`, `tester`, `evaluator`).
- `ai_tutor_agent/orchestration/`: graph assembly and routing logic.
- `ai_tutor_agent/infrastructure/`: external dependency integrations (LLM, checkpointer).
- `ai_tutor_agent/application/`: use-case orchestration (`run_learning_session`).
- `ai_tutor_agent/interfaces/`: delivery channels (CLI, SSE now; FastAPI/WebSocket next).

## Backward Compatibility

Legacy import paths are still available and re-export from the new locations:

- `ai_tutor_agent.cli`
- `ai_tutor_agent.events`
- `ai_tutor_agent.ports`
- `ai_tutor_agent.state`
- `ai_tutor_agent.text`
- `ai_tutor_agent.routing`
- `ai_tutor_agent.workflow`
- `ai_tutor_agent.sse`
- `ai_tutor_agent.agents.*`
- `ai_tutor_agent.adapters.cli`

This allows incremental migration across collaborators and branches.

## Extension Guidelines

- Add a new delivery mode (HTTP, WebSocket, UI bridge):
  - implement adapter(s) in `interfaces/<mode>/`.
  - keep nodes untouched; only inject `RuntimeContext`.
- Add a new model/provider:
  - extend `infrastructure/llm.py` with provider factories.
  - keep prompt/node logic unchanged when possible.
- Add RAG:
  - implement retrieval in `infrastructure/` and inject a retrieval service into relevant node builders.
- Keep business flow changes in:
  - `application/` for use-case behavior,
  - `orchestration/` for graph topology/routing.
