import os
from typing import Any, Dict, List, Tuple, Union

from autogen import ConversableAgent, GroupChatManager
from autogen.agentchat.groupchat import GroupChat

from .prompts import action_prompt, game_rules, reasoning_prompt, verifier_prompt
from src.models.action import Action, AssassinateAction, CoupAction
from src.models.players.base import BasePlayer

llm_config = {"model": "gpt-4o", "api_key": os.environ.get("OPENAI_API_KEY")}


def format_actions_for_llm(available_actions: List[Action], player_coins: int) -> Dict[str, Any]:
    """
    Format the available actions into a structured dictionary representation for the LLM.

    :param available_actions: List of available Action objects
    :param player_coins: Number of coins the player has
    :return: Dictionary with formatted action information
    """
    formatted_actions = {}

    for i, action in enumerate(available_actions, 1):
        action_info = {
            "action": action.__class__.__name__,
            "type": action.action_type.value,
            "requires_target": action.requires_target,
            "can_be_challenged": action.can_be_challenged,
            "can_be_countered": action.can_be_countered,
        }

        if action.associated_card_type:
            action_info["associated_card"] = action.associated_card_type.value

        if isinstance(action, CoupAction):
            action_info["cost"] = 7
        elif isinstance(action, AssassinateAction):
            action_info["cost"] = 3

        formatted_actions[f"action_{i}"] = action_info

    # Add metadata about the player's coins and any mandatory actions
    formatted_actions["metadata"] = {
        "player_coins": player_coins,
        "mandatory_coup": player_coins >= 10,
    }

    return formatted_actions


def build_reasoning_agent(prompt: str) -> ConversableAgent:
    reasoning_agent = ConversableAgent(
        name="reasoning_agent",
        system_message=prompt,
        llm_config=llm_config,
    )

    return reasoning_agent


def build_verifier_agent(prompt: str) -> ConversableAgent:
    verifier_agent = ConversableAgent(
        name="verifier_agent",
        system_message=prompt,
        llm_config=llm_config,
    )

    return verifier_agent


def build_action_parser_agent(prompt: str) -> ConversableAgent:
    action_parser_agent = ConversableAgent(
        name="action_parser_agent",
        system_message=prompt,
        llm_config={
            "model": "gpt-4o",
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "response_format": {"type": "json_object"},
        },
    )

    return action_parser_agent


def build_agent(
    name: str,
    available_actions: List[Action],
    other_players: List[BasePlayer],
    round_history: List[str],
    current_game_state: Union[str, Dict[str, str]],
    coins: int,
    format_actions: bool = True,
) -> Tuple[GroupChatManager, Dict[str, ConversableAgent]]:
    if format_actions:
        formatted_actions = str(format_actions_for_llm(available_actions, coins))
    else:
        formatted_actions = str(available_actions)

    reasoning_formatted_string = (
        reasoning_prompt.replace("{{GAME_RULES}}", game_rules)
        .replace("{{AVAILABLE_ACTIONS}}", formatted_actions)
        .replace("{{CURRENT_GAME_STATE}}", str(current_game_state))
        .replace("{{PREVIOUS_TURNS}}", "\n".join(round_history))
    )

    reasoning_agent = build_reasoning_agent(reasoning_formatted_string)

    verifier_formatted_string = (
        verifier_prompt.replace("{{GAME_RULES}}", game_rules)
        .replace("{{CURRENT_GAME_STATE}}", str(current_game_state))
        .replace("{{PREVIOUS_TURNS}}", "\n".join(round_history))
        .replace("{{AVAILABLE_ACTIONS}}", formatted_actions)
    )

    verifier_agent = build_verifier_agent(verifier_formatted_string)

    action_parser_agent = build_action_parser_agent(
        action_prompt.replace("{{AVAILABLE_ACTIONS}}", formatted_actions)
    )

    agents = {
        "reasoning_agent": reasoning_agent,
        "verifier_agent": verifier_agent,
        "action_parser_agent": action_parser_agent,
    }

    group_chat = GroupChat(
        agents=[reasoning_agent, verifier_agent, action_parser_agent],  # must be in this order
        messages=[],
        max_round=1 + 1 + 1 + 1,  # noqa
        allow_repeat_speaker=False,
        speaker_selection_method="round_robin",  # we don't need to use an LLM to auto decide
    )
    # user agent used to initiate chat + reasoning agent + verifier agent + action parser agent

    group_chat_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
    )

    return group_chat_manager, agents
