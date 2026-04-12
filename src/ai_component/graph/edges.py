from src.utils import utils
from src.ai_component.graph.state import GraphState

def route_after_query(state: GraphState) -> str:
    messages = state.get('messages', [])
    if not messages:
        return 'judge_node'
        
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return 'tools'

    # Skip judge when no document is uploaded — nothing to validate against
    session_id = state.get('session_id', '')
    if not session_id:
        message_count = len(messages)
        if message_count > utils.MAX_CONVERSATION:
            return 'summarizer_node'
        return '__end__'

    return 'judge_node'

def route_after_judge(state: GraphState) -> str:
    verdict = state.get('Judge_response', 'No')
    loops = state.get('max_loop', 0)

    if verdict == 'No' and loops < utils.max_tries:
        return 'query_node'

    message_count = len(state.get('messages', []))
    if message_count > utils.MAX_CONVERSATION:
        return 'summarizer_node'

    return '__end__'