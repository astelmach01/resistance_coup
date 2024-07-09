import json
import random
import time
from typing import Dict, List, Optional, Tuple, Union

from autogen import ConversableAgent

from src.models.action import Action, ActionType
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.models.players.gpt.agents import build_agent
from src.utils.print import print_text, print_texts


class GPTPlayer(BasePlayer):
    is_ai: bool = True

    def choose_action(
        self,
        other_players: List[BasePlayer],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> Tuple[Action, Optional[BasePlayer]]:
        available_actions = self.available_actions()

        group_chat_manager, agents = build_agent(
            self.name,
            available_actions,
            other_players,
            round_history,
            current_game_state,
            self.coins,
        )

        print_text(f"[bold magenta]{self}[/] is thinking...", with_markup=True)
        # Coup is only option
        if len(available_actions) == 1:
            player = random.choice(other_players)
            return available_actions[0], player

        user_agent = ConversableAgent(
            name="Initiator",
            llm_config=None,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        _ = user_agent.initiate_chat(
            group_chat_manager,
            message=f"It is my move as {self.name} and I have {self._pretty_print_cards()} in my hand",
        )  # noqa
        print()

        agent_last_message = group_chat_manager.last_message(agents["action_parser_agent"])
        print(f"Agent Last Message: {agent_last_message}")

        arguments = json.loads(agent_last_message["content"])

        print(f"Parsed Arguments: {arguments}")
        target_action = arguments["action"]

        try:
            chosen_action_type = target_action.lower().replace("action", "")
            chosen_action_type = ActionType[chosen_action_type]
        except KeyError:
            print_text(
                f"Error: invalid action name, {chosen_action_type}. Available actions: {available_actions}",
                style="red",
            )
            return None, None

        # Match the chosen action type to an available action
        for action in available_actions:
            if action.action_type == chosen_action_type:
                target_action = action
                break

        target_player = None

        if target_action.requires_target:
            target_player = arguments.get("targeted_player", "")

            if not target_player:
                print_text(
                    f"We didn't get a target player from the agent-generated message: {arguments}",
                    style="red",
                )
                time.sleep(1)
                target_player = random.choice(other_players)

            for player in other_players:
                if player.name == target_player:
                    target_player = player
                    break

        # Make sure we have a valid action/player combination
        while not self._validate_action(target_action, target_player):
            print_text(
                f"{self} chose an invalid action: {target_action} on {target_player}", style="red"
            )
            time.sleep(1)
            target_action = random.choice(available_actions)
            if target_action.requires_target:
                target_player = random.choice(other_players)

        return target_action, target_player

    def determine_challenge(
        self,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        """Choose whether to challenge the current player making the move"""

        available_actions = "Challenge player action: True or False. \nTrue: challenge the player's action. \nFalse: do not challenge the player's action. The JSON dict returned should ONLY be '{action: True/False}'"  # noqa

        group_chat_manager, agents = build_agent(
            self.name,
            available_actions,
            other_players,
            round_history,
            current_game_state,
            self.coins,
            format_actions=False,
        )

        user_agent = ConversableAgent(
            name="Initiator",
            llm_config=None,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        _ = user_agent.initiate_chat(
            group_chat_manager,
            message=f"It is my chance to challenge the most recent action taken by {player_being_challenged.name} as {self.name}. I have {self._pretty_print_cards()} in my hand",  # noqa
        )
        print()

        agent_last_message = group_chat_manager.last_message(agents["action_parser_agent"])
        print(f"Agent Last Message: {agent_last_message}")

        arguments = json.loads(agent_last_message["content"])

        print(f"Parsed Arguments: {arguments}")
        target_action = arguments["action"]

        # can be True, False, or a string "True" or "False", so parse both types
        if isinstance(target_action, bool):
            return target_action
        elif isinstance(target_action, str):
            lowered = target_action.lower()
            if lowered == "true":
                return True
            elif lowered == "false":
                return False

        else:
            print_text(f"Error: invalid  challenge action '{target_action}'", style="red")
            time.sleep(1)
            return False

    def determine_counter(
        self,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        """Choose whether to counter the current player making the move"""

        available_actions = "Counter player action: True or False. \nTrue: Counter the player's action. \nFalse: do not counter the player's action. The JSON dict returned should ONLY be '{action: True/False}'"  # noqa

        group_chat_manager, agents = build_agent(
            self.name,
            available_actions,
            other_players,
            round_history,
            current_game_state,
            self.coins,
            format_actions=False,
        )

        user_agent = ConversableAgent(
            name="Initiator",
            llm_config=None,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        _ = user_agent.initiate_chat(
            group_chat_manager,
            message=f"It is my chance to counter the most recent action taken by {player_being_challenged.name} as {self.name}. I have {self._pretty_print_cards()} in my hand",  # noqa
        )
        print()

        agent_last_message = group_chat_manager.last_message(agents["action_parser_agent"])
        print(f"Agent Last Message: {agent_last_message}")

        arguments = json.loads(agent_last_message["content"])

        print(f"Parsed Arguments: {arguments}")
        target_action = arguments["action"]

        # can be True, False, or a string "True" or "False", so parse both types
        if isinstance(target_action, bool):
            return target_action
        elif isinstance(target_action, str):
            lowered = target_action.lower()
            if lowered == "true":
                return True
            elif lowered == "false":
                return False

        else:
            print_text(f"Error: invalid counter action '{target_action}'", style="red")
            time.sleep(1)
            return False

    def remove_card(
        self, round_history: List[str], current_game_state: Union[str, Dict[str, str]]
    ) -> str:
        """Choose a card and remove it from your hand"""

        available_actions = f"Remove a card from your hand (zero indexed). Return 0 for the 1st card, 1 for the second card, etc. The index returned MUST be between the range 0 and {len(self.cards)}. The JSON dict returned should ONLY have the key 'action' with the card number as the value'"  # noqa

        other_players = []

        group_chat_manager, agents = build_agent(
            self.name,
            available_actions,
            other_players,
            round_history,
            current_game_state,
            self.coins,
            format_actions=False,
        )

        user_agent = ConversableAgent(
            name="Initiator",
            llm_config=None,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        _ = user_agent.initiate_chat(
            group_chat_manager,
            message=f"I am playing as {self.name} and I have to remove a card from my hand. My current deck is {self._pretty_print_cards()}",  # noqa
        )
        print()

        agent_last_message = group_chat_manager.last_message(agents["action_parser_agent"])
        print(f"Agent Last Message: {agent_last_message}")

        arguments = json.loads(agent_last_message["content"])

        print(f"Parsed Arguments: {arguments}")
        target_action = arguments["action"]

        index = None

        try:
            index = int(target_action)
        except ValueError:
            print(f"Error: Invalid action '{target_action}'")
            time.sleep(1)
            return ""

        if index < 0 or index >= len(self.cards):
            print(f"Error: Invalid index '{index}'")
            time.sleep(1)
            index = random.choice(range(len(self.cards)))

        # Remove a random card
        discarded_card = self.cards.pop(index)
        print_texts(
            f"{self} discards their ",
            (f"{discarded_card}", discarded_card.style),
            " card",
        )
        return f"{self} discards their {discarded_card} card"

    def choose_exchange_cards(
        self,
        exchange_cards: List[Card],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""

        self.cards += exchange_cards
        random.shuffle(self.cards)

        available_actions = f"Exchange 2 cards from your hand (zero indexed) as a list. For example, return [0,1] to remove the first and second card. To return the 1st and 3rd cards in the deck, return [1,3]. The indices returned MUST be between the range 0 and {len(self.cards) - 1}, and the returned value MUST be a list of 2 integers only that are unique. The JSON dict returned should ONLY have a key of 'action' with a value of a list of 2 valid integers"  # noqa

        other_players = []

        group_chat_manager, agents = build_agent(
            self.name,
            available_actions,
            other_players,
            round_history,
            current_game_state,
            self.coins,
            format_actions=False,
        )

        user_agent = ConversableAgent(
            name="Initiator",
            llm_config=None,
            human_input_mode="NEVER",
            code_execution_config=False,
        )

        _ = user_agent.initiate_chat(
            group_chat_manager,
            message=f"I am playing as {self.name} and I have to exchange 2 cards. My current deck is {self._pretty_print_cards()} after adding in the exchanged cards to my deck. The random cards I got from the deck were {exchange_cards}",  # noqa
        )
        print()

        agent_last_message = group_chat_manager.last_message(agents["action_parser_agent"])
        print(f"Agent Last Message: {agent_last_message}")

        arguments = json.loads(agent_last_message["content"])

        print(f"Parsed Arguments: {arguments}")
        target_action = arguments["action"]

        if not isinstance(target_action, list) or len(target_action) != 2:
            print(f"Error: Invalid action '{target_action}'")
            time.sleep(1)
            exit()

        try:
            index1, index2 = int(target_action[0]), int(target_action[1])
        except ValueError:
            print(f"Error: Invalid action '{target_action}'")
            time.sleep(1)
            return ""

        if index1 < 0 or index1 >= len(self.cards) or index2 < 0 or index2 >= len(self.cards):
            print(f"Error: Invalid index '{index1}' or '{index2}'")
            time.sleep(1)
            exit()

        if index1 == index2:
            print(f"Error: Cannot exchange the same card '{index1}' and '{index2}'")
            time.sleep(1)
            exit()

        print_text(f"{self} exchanges 2 cards")

        first_card = self.cards[index1]
        second_card = self.cards[index2]

        # Remove the larger index first
        if index1 > index2:
            self.cards.pop(index1)
            self.cards.pop(index2)
        else:
            self.cards.pop(index2)
            self.cards.pop(index1)

        return first_card, second_card
