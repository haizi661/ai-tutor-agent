# Architecture Overview

## Current Flow

The current system is no longer a simple `Tutor -> Tester -> Evaluator` loop. The real entry flow is:

```text
intake_router
  -> meta_qa | smalltalk | greeting
  -> topic_confirmer
  -> assessment_generator
  -> user_profiler
  -> tutor
  -> tester
  -> evaluator
  -> pass | fail -> tutor
```

Meaning:

- `intake_router`: classifies the user's first input as study-topic, meta question, or small talk.
- `meta_qa`: answers system/product questions such as current model, what the system can do, or how configuration works.
- `smalltalk`: allows limited casual conversation, then routes back toward learning.
- `greeting`: extracts a candidate study topic.
- `topic_confirmer`: asks the user to explicitly confirm the inferred topic before assessment starts.
- `assessment_generator`: emits a full pre-assessment form.
- `user_profiler`: computes rule-based radar scores and asks the LLM only for explanatory reporting.
- `tutor/tester/evaluator`: the teaching loop.

## Layers

- `ai_tutor_agent/core/`
  - Domain-neutral contracts and shared structures.
  - `events.py`, `ports.py`, `state.py`, `text.py`
- `ai_tutor_agent/nodes/`
  - Single-purpose LangGraph nodes.
  - Includes `intake.py`, `meta.py`, `smalltalk.py`, `greeting.py`, `topic_confirm.py`, `assessment.py`, `tutor.py`, `tester.py`, `evaluator.py`
- `ai_tutor_agent/orchestration/`
  - Graph assembly and routing.
- `ai_tutor_agent/infrastructure/`
  - LLM factory, checkpoint persistence, retrieval.
- `ai_tutor_agent/application/`
  - Session-level orchestration.
- `ai_tutor_agent/interfaces/`
  - Delivery adapters: FastAPI, SSE, CLI.

## Runtime Contracts

Key contracts remain stable:

- `AgentState`: graph state carrier.
- `AgentEvent`: structured runtime event for SSE/UI.
- `EventSink`: emits events.
- `AnswerProvider`: fetches external user input.
- `KnowledgeProvider`: serves retrieval context.

Nodes must not directly use `print()` or `input()`.

## Configuration Model

The project currently separates two concerns:

1. Chat model configuration
   - `CHAT_PROFILE`
   - vendor-specific API keys
   - `MODEL_NAME`
   - `OPENAI_API_BASE` when needed
2. Retrieval / embedding configuration
   - `EMBEDDING_PROVIDER`
   - `EMBEDDING_MODEL_NAME`
   - chunk size / overlap / top-k

Supported chat profiles:

- `gemini`
- `qwen`
- `deepseek`
- `openai`
- `minimax`
- `glm`
- `custom`

## Compatibility Layer

Legacy import paths still re-export from the new layered structure. They should remain only as compatibility shims; new code should target the layered modules directly.

## Extension Guidelines

- Add new delivery modes under `interfaces/`
- Add new model or provider mappings in `interfaces/api/runtime.py` and `config.py`
- Keep retrieval changes inside `infrastructure/`
- Keep flow changes inside `nodes/` and `orchestration/`
- Update tests and docs whenever `AgentState`, event schemas, or public endpoints change
