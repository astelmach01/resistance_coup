# gpt_player_utils.py

import json
from typing import Dict, List, Union

from autogen import ConversableAgent

from src.models.players.base import BasePlayer
from src.models.players.gpt.agents import build_agent
from src.utils.print import print_text


# build a groupchat, query it, then return the json response
# the json response will always be the last message of the action_parser_agent
def build_and_chat(
    player_name: str,
    available_actions: Union[str, List],
    other_players: List[BasePlayer],
    round_history: List[str],
    current_game_state: Union[str, Dict[str, str]],
    coins: int,
    notes: str,
    message: str,
    format_actions: bool = True,
) -> Dict:
    group_chat_manager, agents = build_agent(
        player_name,
        available_actions,
        other_players,
        round_history,
        current_game_state,
        coins,
        notes=notes,
        format_actions=format_actions,
    )

    user_agent = ConversableAgent(
        name="Player",
        llm_config=None,
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    _ = user_agent.initiate_chat(group_chat_manager, message=message)
    print()

    return group_chat_manager.last_message(agents["action_parser_agent"])


# get the action from the agent response, which should always be "content"
def parse_action(
    content: str, action_type: str = "action"
) -> Union[bool, int, List[int], str, None]:
    try:
        arguments = json.loads(content)
        return arguments[action_type]
    except (json.JSONDecodeError, KeyError):
        print_text(f"Error: invalid {action_type} in agent response", style="red")
        return None
