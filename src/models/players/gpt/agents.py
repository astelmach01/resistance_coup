import os
from typing import Any, Dict, List, Tuple, Union

from autogen import ConversableAgent, GroupChatManager
from autogen.agentchat.groupchat import GroupChat
from jinja2 import Template

from .prompts import action_prompt, game_rules, reasoning_prompt, verifier_prompt
from src.models.action import Action, AssassinateAction, CoupAction
from src.models.players.base import BasePlayer
from src.utils.round_history import RoundHistory

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o")

llm_config = {"model": LLM_MODEL, "api_key": OPENAI_API_KEY}


def format_actions_for_llm(available_actions: List[Action], player_coins: int) -> str:
    formatted_actions = {}
    for i, action in enumerate(available_actions, 1):
        formatted_actions[f"action_{i}"] = {
            "action": action.__class__.__name__,
            "type": action.action_type.value,
            "requires_target": action.requires_target,
            "can_be_challenged": action.can_be_challenged,
            "can_be_countered": action.can_be_countered,
            "associated_card": (
                action.associated_card_type.value if action.associated_card_type else None
            ),
            "cost": (
                7
                if isinstance(action, CoupAction)
                else 3
                if isinstance(action, AssassinateAction)
                else None
            ),
        }

    formatted_actions["metadata"] = {
        "player_coins": player_coins,
        "mandatory_coup": player_coins >= 10,
    }

    return str(formatted_actions)


def render_template(template_string: str, **kwargs) -> str:
    template = Template(template_string)
    result = template.render(**kwargs)
    return result


def build_agent_base(
    name: str, prompt: str, response_format: Dict[str, Any] = None
) -> ConversableAgent:

    agent_config = llm_config.copy()
    if response_format:
        agent_config["response_format"] = response_format

    return ConversableAgent(
        name=name,
        system_message=prompt,
        llm_config=agent_config,
    )


def build_agent(
    name: str,
    available_actions: List[Action],
    other_players: List[BasePlayer],
    round_history: RoundHistory,
    current_game_state: Union[str, Dict[str, str]],
    coins: int,
    notes: str,
    format_actions: bool = True,
) -> Tuple[GroupChatManager, Dict[str, ConversableAgent]]:
    formatted_actions = (
        format_actions_for_llm(available_actions, coins)
        if format_actions
        else str(available_actions)
    )

    common_kwargs = {
        "GAME_RULES": game_rules,
        "AVAILABLE_ACTIONS": formatted_actions,
        "CURRENT_GAME_STATE": str(current_game_state),
        "PREVIOUS_TURNS": str(round_history),
        "PLAYER_NOTES": notes,
    }

    reasoning_agent = build_agent_base(
        name="reasoning_agent", prompt=render_template(reasoning_prompt, **common_kwargs)
    )

    verifier_agent = build_agent_base(
        name="verifier_agent", prompt=render_template(verifier_prompt, **common_kwargs)
    )

    action_parser_agent = build_agent_base(
        name="action_parser_agent",
        prompt=render_template(action_prompt, **common_kwargs),
        response_format={"type": "json_object"},
    )

    agents = {
        "reasoning_agent": reasoning_agent,
        "verifier_agent": verifier_agent,
        "action_parser_agent": action_parser_agent,
    }

    group_chat = GroupChat(
        agents=list(agents.values()),
        messages=[],
        max_round=4,  # initial user query + reasoning agent + verifier agent + action parser agent
        allow_repeat_speaker=False,
        speaker_selection_method="round_robin",
    )

    group_chat_manager = GroupChatManager(groupchat=group_chat, llm_config=llm_config)

    return group_chat_manager, agents
