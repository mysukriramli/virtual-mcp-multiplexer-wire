import sys
import os
import json
import re
import argparse
from typing import List, Dict, Any

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "tools_catalog.json")

def tokenize(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    return set(words)

def score_tool(query_tokens: set, tool: Dict[str, Any]) -> float:
    tool_tokens = tokenize(
        f"{tool['tool_name']} {tool['server_namespace']} {tool['category']} {tool['description']}"
    )
    if not tool_tokens:
        return 0.0
    overlap = query_tokens.intersection(tool_tokens)
    score = len(overlap) * 3.0
    for qt in query_tokens:
        if qt in tool["tool_name"].lower():
            score += 5.0
        if qt == tool["server_namespace"].lower() or qt == tool["category"].lower():
            score += 4.0
    return score

def route_tools(query: str, catalog: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    query_tokens = tokenize(query)
    scored = []
    for t in catalog:
        s = score_tool(query_tokens, t)
        scored.append((s, t))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for s, t in scored[:top_k] if s > 0.0] or [t for _, t in scored[:top_k]]

def format_openai_functions(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["tool_id"],
                "description": f"[{t['server_namespace']}] {t['description']}",
                "parameters": t["parameters"]
            }
        })
    return out

def format_anthropic_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for t in tools:
        out.append({
            "name": t["tool_id"],
            "description": f"[{t['server_namespace']}] {t['description']}",
            "input_schema": t["parameters"]
        })
    return out

def run_mcp_stdio_proxy():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Initial meta-tool schema that the agent starts with
    multiplexer_meta_tool = {
        "name": "virtual_mcp_route_tools",
        "description": "Semantic query proxy that retrieves and activates the top 3-5 relevant MCP tools for a specific sub-goal without context bloat.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subtask_intent": {
                    "type": "string",
                    "description": "Concrete sub-task or command (e.g. 'pull docker container logs' or 'commit file to github')"
                },
                "max_tools": {
                    "type": "integer",
                    "default": 3
                }
            },
            "required": ["subtask_intent"]
        }
    }

    response = {
        "jsonrpc": "2.0",
        "result": {
            "tools": [multiplexer_meta_tool]
        }
    }
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")

            if method == "tools/list":
                res = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": [multiplexer_meta_tool]}}
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})

                if name == "virtual_mcp_route_tools":
                    intent = args.get("subtask_intent", "")
                    max_tools = args.get("max_tools", 3)
                    routed = route_tools(intent, catalog, top_k=max_tools)
                    active_schemas = format_anthropic_tools(routed)

                    res = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Activated {len(routed)} scoped tools for task: '{intent}'. Context budget used: ~{len(routed)*120} tokens (vs {len(catalog)*120} tokens total)."
                                }
                            ],
                            "activated_tools": active_schemas
                        }
                    }
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
        except Exception as e:
            err = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="Virtual MCP Dynamic Tool Router CLI")
    parser.add_argument("query", nargs="?", default="", help="Natural language intent to route tools for")
    parser.add_argument("--top-k", type=int, default=3, help="Number of tool schemas to return")
    parser.add_argument("--format", choices=["openai", "anthropic", "json"], default="anthropic")
    parser.add_argument("--serve-mcp", action="store_true", help="Launch interactive MCP stdio proxy")

    args = parser.parse_args()

    if args.serve_mcp:
        run_mcp_stdio_proxy()
        return

    if not args.query:
        print("Error: query parameter required unless running with --serve-mcp", file=sys.stderr)
        sys.exit(1)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    routed = route_tools(args.query, catalog, top_k=args.top_k)

    if args.format == "openai":
        output = format_openai_functions(routed)
    elif args.format == "anthropic":
        output = format_anthropic_tools(routed)
    else:
        output = routed

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
