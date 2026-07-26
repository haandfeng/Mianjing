
https://deepwiki.com/sanbuphy/claude-code-source-code/10-context-management-and-compaction



The system uses three primary mechanisms to reduce context:

1. **Micro-compaction (Token Trimming):** Aggressive removal of non-essential metadata, ANSI codes, and redundant tool outputs.
	 - **`microCompact()`**: Strips ANSI escape sequences from tool outputs and truncates extremely long, repetitive stdout/stderr blocks [src/services/compact/microCompact.ts1-15](https://github.com/sanbuphy/claude-code-source-code/blob/19b097b6/src/services/compact/microCompact.ts#L1-L15)
	- **`apiMicrocompact()`**: Specifically formats messages for the Anthropic API, ensuring that tool results are optimized for token consumption before being sent over the wire [src/services/compact/apiMicrocompact.ts5-25](https://github.com/sanbuphy/claude-code-source-code/blob/19b097b6/src/services/compact/apiMicrocompact.ts#L5-L25)
2. **Auto-compaction (Summarization):** Using a "summarizer" model to condense older parts of the conversation into a concise narrative.
3. **Context Sniping (Boundary Mechanics):** Truncating the message history at specific "compact boundaries" to strictly limit the active window.