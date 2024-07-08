import os
from typing import Dict, List, Union

from autogen import ConversableAgent, GroupChatManager
from autogen.agentchat.groupchat import GroupChat

from .prompts import action_prompt, game_rules, reasoning_prompt, verifier_prompt
from src.models.action import Action, AssassinateAction, CoupAction
from src.models.players.base import BasePlayer

llm_config = {"model": "gpt-4o", "api_key": os.environ.get("OPENAI_API_KEY")}


def format_actions_for_llm(available_actions: List[Action], player_coins: int) -> str:
    """Format the available actions into a string representation for the LLM."""
    action_descriptions = []
    for i, action in enumerate(available_actions, 1):
        description = f"{i}. {action.__class__.__name__}:\n"
        description += f"   - Type: {action.action_type.value}\n"
        if action.associated_card_type:
            description += f"   - Associated Card: {action.associated_card_type.value}\n"
        description += f"   - Requires Target: {'Yes' if action.requires_target else 'No'}\n"
        description += f"   - Can be Challenged: {'Yes' if action.can_be_challenged else 'No'}\n"
        description += f"   - Can be Countered: {'Yes' if action.can_be_countered else 'No'}\n"

        # Add cost information for relevant actions
        if isinstance(action, CoupAction):
            description += "   - Cost: 7 coins\n"
        elif isinstance(action, AssassinateAction):
            description += "   - Cost: 3 coins\n"

        action_descriptions.append(description)

    # Add a note about mandatory coup if player has 10 or more coins
    if player_coins >= 10:
        action_descriptions.append(
            "Note: You must perform a Coup action as you have 10 or more coins."
        )

    return "\n".join(action_descriptions)


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
        system_message=verifier_prompt,
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
) -> GroupChatManager:
    formatted_actions = format_actions_for_llm(available_actions, coins)

    formatted_string = (
        reasoning_prompt.replace("{{GAME_RULES}}", game_rules)
        .replace("{{AVAILABLE_ACTIONS}}", formatted_actions)
        .replace("{{CURRENT_GAME_STATE}}", str(current_game_state))
        .replace("{{PREVIOUS_TURNS}}", "\n".join(round_history))
    )
    reasoning_agent = build_reasoning_agent(formatted_string)

    verifier_agent = build_verifier_agent(formatted_string)

    action_parser_agent = build_action_parser_agent(
        action_prompt.replace("{{AVAILABLE_ACTIONS}}", formatted_actions)
    )

    group_chat = GroupChat(
        agents=[reasoning_agent, verifier_agent, action_parser_agent],
        messages=[],
        max_round=1,
        speaker_selection_method="round_robin",
    )

    group_chat_manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config,
    )

    return group_chat_manager
