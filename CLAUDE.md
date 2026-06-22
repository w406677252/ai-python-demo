# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install / sync dependencies
uv sync

# Run the agent (three equivalent entry points)
uv run python main.py
uv run python -m idefense_ai
uv run idefense-ai

# Add a dependency
uv add <package>

# Run a specific Python expression in the venv
uv run python -c "..."

# Check syntax without running
uv run python -c "import ast; ast.parse(open('src/idefense_ai/graph.py').read())"
```

## Project Structure

```
src/idefense_ai/           # Package root (src layout)
├── entry.py               # L1 Entry layer — CLI entry point (main())
├── graph.py               # L2 Orchestration layer — nodes, routing, compile
├── llm.py                 # L3 Model layer — LLM init, env vars, tool binding
├── state.py               # L3 Data layer — MessagesState TypedDict
├── tools.py               # L3 Capability layer — @tool functions + registry
├── __init__.py            # Empty package marker
└── __main__.py            # python -m support
main.py                    # Thin 3-line shim
pyproject.toml             # Package config, deps, [project.scripts] entry
```

## Architecture

### 5-layer dependency rule
Layers can only depend on layers below them. No reverse dependencies.

| Layer | Module | Depends on |
|-------|--------|------------|
| Entry | `entry.py` | graph |
| Config | `llm.py` | tools |
| Orchestration | `graph.py` | config + state + tools |
| Model | `state.py` | (none) |
| Capability | `tools.py` | (none) |

### Core pattern: LangGraph agent loop
The agent is a `StateGraph` with a 2-node loop:

```
START → llm_call → (tool_node ←→ llm_call)* → END
```

- **`llm_call()`**: Invokes the model with SystemMessage + conversation history. Returns updated messages + increment `llm_calls` counter.
- **`tool_node()`**: Iterates over `tool_calls` in the last message, dispatches to `tools_by_name`, returns `ToolMessage` results.
- **`should_continue()`**: Conditional edge — routes to `"tool_node"` if `tool_calls` exist, otherwise `END`.

### Graph state
```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]  # reducer appends
    llm_calls: int                                       # manual increment
```

### Model configuration
```python
model = init_chat_model(
    "deepseek-chat",
    model_provider="openai",
    temperature=0,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
)
```
DeepSeek is accessed via OpenAI-compatible API. Set `OPENAI_API_KEY` env var.

### Code conventions
- All imports at top of file: stdlib → third-party → internal (`from .module import ...`)
- Google-style docstrings with `Args:` / `Returns:` sections
- Double quotes for strings; `"""` for docstrings
- 100-char line limit
- Use `typing_extensions.TypedDict` + `Annotated` for graph state
- Functions have full type annotations (params + return)
- No wildcard imports; no bare `except:`
