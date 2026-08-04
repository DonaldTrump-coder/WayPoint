
from openai import OpenAI

from agent.tools import TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = """你是 Waypoint Copilot，一个本地个人项目管理助手，管理用户的「航程」项目与「航路点」任务。

## 系统背景
用户通过看板管理任务流转（待办→进行中→已完成），通过甘特图管理时间线，
每个任务还可以关联一篇 Markdown 笔记（撰写思路、进展、总结等）。
数据全部存在本地 SQLite 数据库。

## 可用操作（通过工具）
- 项目：列出、创建（创建时自动生成默认看板列）
- 任务：创建、查询、更新（状态/优先级/进度/日期/标题）、在看板列间移动、删除、查看详情
- 子任务（checklist）：添加、列出、标记完成/取消完成、删除；子任务完成情况会自动重算父任务进度并归类状态（全完成=已完成 done / 全未完成=待办 backlog / 部分=进行中 in_progress）
- 笔记：读取、保存任务的 Markdown 笔记（支持 # 标题、- 列表、**加粗** 等语法）

## 规则
1. 用户提到「项目」时，先调用 list_projects 确认存在；创建任务前必须找到对应项目。
2. 任务状态取值：backlog(待办) / todo / in_progress(进行中) / review / done(已完成)。
3. 优先级取值：low(低) / medium(中) / high(高) / urgent(紧急)。
4. 日期格式统一用 YYYY-MM-DD。
5. 创建任务时如果用户没给日期，可先留空；用户说「下周/下周五」等相对时间时按今天推算。
6. 用户要求「写笔记/记录一下」时用 save_note；要求「看笔记/笔记里写了什么」时用 get_note。
7. 每次工具执行后，用简洁中文向用户确认结果。
8. 只操作本系统的数据，不做其他事。不确定时先查询再行动。
"""

THINKING_PROMPT = """\n\n## 思考要求
在每次调用工具之前，先用一两句话简要说明你的思路（如：先查一下有哪些项目、再决定创建哪个任务的日期），
但不要输出多余的过程描述，保持最终回复简洁。
"""


def _build_client(cfg):
    return OpenAI(
        base_url=cfg.base_url,
        api_key=cfg.api_key or "sk-local",
    )


def _agent_history(cfg, messages, thinking):
    sys_prompt = SYSTEM_PROMPT + (THINKING_PROMPT if thinking else "")
    return [{"role": "system", "content": sys_prompt}] + messages


def run_agent_loop(cfg, messages: list[dict], max_iterations: int = 6, thinking: bool = False) -> dict:
    client = _build_client(cfg)
    history = _agent_history(cfg, messages, thinking)
    tool_calls_log = []

    for _ in range(max_iterations):
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=history,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=cfg.temperature / 100,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return {"reply": msg.content or "(空回复)", "tool_calls_log": tool_calls_log}

        history.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            import json

            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = execute_tool(tc.function.name, args)
            tool_calls_log.append({"tool": tc.function.name, "args": args, "result": result})
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return {
        "reply": "工具调用次数已达上限，请重试或简化请求。",
        "tool_calls_log": tool_calls_log,
    }


def stream_agent_loop(cfg, messages: list[dict], max_iterations: int = 6, thinking: bool = False):
    import json

    client = _build_client(cfg)
    history = _agent_history(cfg, messages, thinking)
    tool_calls_log = []

    for _ in range(max_iterations):
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=history,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=cfg.temperature / 100,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            stream = client.chat.completions.create(
                model=cfg.model,
                messages=history,
                stream=True,
                temperature=cfg.temperature / 100,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield {"type": "delta", "content": delta.content}
            yield {"type": "done"}
            return

        history.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = execute_tool(tc.function.name, args)
            tool_calls_log.append({"tool": tc.function.name, "args": args, "result": result})
            yield {
                "type": "tool",
                "tool": tc.function.name,
                "result": result,
            }
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    yield {"type": "delta", "content": "（工具调用次数已达上限，请重试或简化请求）"}
    yield {"type": "done"}
