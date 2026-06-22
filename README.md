<<<<<<< HEAD
# ai-python-demo
=======
# idefense-ai-python

LangGraph agent for arithmetic operations using DeepSeek.

## 目录

- [项目分层](#1-项目分层)
- [代码风格](#2-代码风格)
- [分层规范细则](#3-分层规范细则)
- [环境与依赖](#4-环境与依赖)
- [API Key 管理](#5-api-key-管理)
- [Git 规范](#6-git-规范)
- [测试规范](#7-测试规范)

---

## 1. 项目分层

```
src/idefense_ai/
├── __init__.py          # 包标记，可导出公共 API
├── __main__.py          # python -m 入口
├── entry.py             # L1 入口层：CLI 交互、参数解析 (原 cli.py)
├── graph.py             # L2 编排层：图构建、节点路由、生命周期
├── llm.py               # L3 模型层：LLM 初始化、环境变量 (原 config.py)
├── state.py             # L3 数据层：状态类型定义（TypedDict / Pydantic）
└── tools.py             # L3 能力层：工具函数定义（@tool）
```

### 层间依赖关系

| 层级 | 模块 | 职责 | 可依赖（项目内） |
|------|------|------|------------------|
| **L1 入口层** | `entry.py` | CLI 交互、参数解析、用户输入输出 | 编排层 |
| **L2 编排层** | `graph.py` | 图构建、节点函数、路由逻辑 | 模型层 + 数据层 + 能力层 |
| **L3 模型层** | `llm.py` | 模型初始化、环境变量读取、tool binding | 能力层 |
| **L3 数据层** | `state.py` | 状态类型、数据模型定义 | 无 |
| **L3 能力层** | `tools.py` | 工具函数、工具注册表 | 无 |

```
entry.py ──→ graph.py ──→ llm.py ──→ tools.py
              │                │
              │                └── state.py
              │
              └── tools.py
```

> **禁止逆向依赖**：能力层不能引用编排层，模型层不能引用配置层。

---

## 2. 代码风格

### 2.1 导入规范

- 所有 `import` **必须集中在文件顶部**，按以下顺序分组，组间空一行：

```python
# 1. Python 标准库
import os
import operator
from typing import Literal

# 2. 第三方库
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from typing_extensions import Annotated, TypedDict

# 3. 项目内部模块
from .tools import tools
```

- 优先使用 `from X import Y` 而非裸 `import X`。
- 同一模块的多个导入合并为同一个 `from` 语句。
- 禁止使用通配符导入 (`from X import *`)。

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包 / 模块 | `snake_case` | `idefense_ai`, `graph.py` |
| 类 / TypedDict | `PascalCase` | `MessagesState` |
| 函数 / 方法 | `snake_case` | `llm_call()`, `should_continue()` |
| 变量 | `snake_case` | `tools_by_name`, `agent_builder` |
| 常量 | `UPPER_CASE` | `START`, `END` |
| 私有成员 | 前导下划线 `_` | `_format_prompt()` |

### 2.3 类型注解

- **所有函数必须包含完整的参数和返回值类型注解**。
- 优先使用标准库 `typing`，不足时使用 `typing_extensions`。
- TypedDict 用于状态定义，Pydantic 用于复杂数据校验。

```python
def llm_call(state: MessagesState) -> dict:
    """..."""
```

### 2.4 Docstring

- 使用 **Google 风格** docstring。
- 每个模块、类、函数均需写 docstring。

```python
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First integer.
        b: Second integer.
    """
    return a * b
```

### 2.5 其他格式约定

- 字符串统一使用 **双引号** `"`（docstring 使用 `"""`）。
- 行宽不超过 **100 字符**。
- 函数间空 1 行，逻辑段间空 2 行。
- 禁止 `try/except` 裸捕获，必须指定异常类型。
- 文件末尾保留一个空行。

---

## 3. 分层规范细则

### 3.1 入口层 — `cli.py`

- **只做**：参数解析、用户交互、调用编排层。
- **不做**：业务逻辑、模型初始化、工具定义。
- 提供 `main()` 函数作为统一入口点，通过 `pyproject.toml` 的 `[project.scripts]` 注册。

```python
def main() -> None:
    """Run the arithmetic agent."""
    messages = [HumanMessage(content="Add 3 and 4.")]
    result = agent.invoke({"messages": messages})
    for m in result["messages"]:
        m.pretty_print()
```

### 3.2 配置层 — `config.py`

- **只做**：模型实例化、环境变量读取、全局配置对象构建。
- 模块级直接初始化（单例模式），不做惰性加载。

```python
model = init_chat_model(
    "deepseek-chat",
    model_provider="openai",
    temperature=0,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
)
```

### 3.3 编排层 — `graph.py`

- **只做**：定义图节点、路由逻辑、组合图结构。
- 节点函数应当是纯函数式风格，接收 `State`、返回 `dict`。
- 编译后的 `agent` 对象作为模块级变量导出。

```python
def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:
    """Route to the tool node when the LLM made tool calls, otherwise end."""
    last_message = state["messages"][-1]
    return "tool_node" if last_message.tool_calls else END
```

### 3.4 能力层 — `tools.py`

- **只做**：定义 `@tool` 函数，维护工具注册表。
- 每个工具应当是独立的、无副作用的纯函数。
- `tools` 和 `tools_by_name` 作为模块级变量导出。

### 3.5 模型层 — `state.py`

- **只做**：定义状态类型和数据结构。
- 使用 `TypedDict` + `Annotated` 处理 LangGraph 的 reducer 逻辑。
- 保持轻量，不引入业务逻辑。

---

## 4. 环境与依赖

| 项目 | 配置 |
|------|------|
| **Python 版本** | `>=3.14`（见 `.python-version`） |
| **包管理器** | `uv` |
| **添加依赖** | `uv add <package>`（自动更新 `pyproject.toml` 和 `uv.lock`） |
| **安装项目** | `uv sync`（自动以 editable 模式安装当前包） |
| **运行** | `uv run python main.py` / `uv run idefense-ai` / `uv run python -m idefense_ai` |

当前依赖：

- `langchain>=1.3.9` — LangChain 框架
- `langchain-anthropic>=1.4.6` — Anthropic 模型支持（备用）
- `langchain-openai>=0.3.0` — OpenAI 兼容接口（用于 DeepSeek）
- `langgraph>=1.2.4` — LangGraph 图编排
- `ipython>=9.14.1` — 交互式支持

---

## 5. API Key 管理

### 方式一：.env 文件（推荐）

复制 `.env.example` 为 `.env`，填入你的 Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```
OPENAI_API_KEY="sk-your-deepseek-key"
# DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"  # 可选
```

> `.env` 已加入 `.gitignore`，不会提交到版本控制。

### 方式二：环境变量

```bash
# Linux / macOS
export OPENAI_API_KEY="sk-your-deepseek-key"

# Windows (cmd)
set OPENAI_API_KEY="sk-your-deepseek-key"

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-deepseek-key"
```

自定义 API 地址（可选）：

```bash
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
```

> **禁止**将 API Key 硬编码在代码中。始终通过 `.env` 或环境变量注入。

---

## 6. Git 规范

- **分支命名**：`feature/<short-description>` / `fix/<short-description>`
- **提交信息**：简洁英文，首字母大写，不加句号

```
Add multiply tool support
Fix tool_node routing when no tool calls
Refactor package structure under src/
```

- **主分支**：`main`（保护分支，禁止直接推送）

---

## 7. 测试规范

- **目录**：`tests/`（项目根目录）
- **文件命名**：`test_<module>.py`（如 `test_tools.py`）
- **框架**：`pytest`（推荐，TODO：添加到依赖）
- **覆盖要求**：
  - 工具函数必须有单元测试
  - 图节点需 mock LLM 调用进行测试
  - 路由逻辑需覆盖所有分支

---

## 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 DeepSeek API Key

# 3. 运行
uv run python main.py
```
>>>>>>> 0352cbe (Initial commit: LangGraph arithmetic agent with DeepSeek)
