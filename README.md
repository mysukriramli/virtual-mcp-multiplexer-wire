```markdown
# ⚡ Virtual MCP Multiplexer Wire

An autonomous Model Context Protocol (MCP) tool router and schema pruning proxy. It eliminates "Tool Pollution" and context window bloat by dynamically searching tool registries and injecting only the top 2–4 relevant tool schemas into an agent's execution memory on demand.

## Token Impact
- **Token Reduction**: 85% – 94%
- **Context Preservation**: Reduces multi-thousand token tool lists down to ~300 tokens per sub-goal step.

## Standalone Agent CLI
Autonomous terminal agents can clone this repository and query the multiplexer locally with zero cloud dependencies:

```bash
# Get OpenAI function calling schema for sub-goal
python multiplexer.py "query postgres database table" --top-k 2 --format openai

# Launch as a virtual MCP stdio proxy
python multiplexer.py --serve-mcp
