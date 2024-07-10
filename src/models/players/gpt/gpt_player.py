import random
import time
from typing import Dict, List, Optional, Tuple, Union

from .gpt_player_utils import build_and_chat, parse_action
from src.models.action import Action, ActionType
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.models.players.gpt.notes import Notes, take_notes
from src.utils.print import print_text, print_texts


class GPTPlayer(BasePlayer):
    is_ai: bool = True
    notes: Notes = Notes()

    def choose_action(
        self,
        other_players: List[BasePlayer],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> Tuple[Action, Optional[BasePlayer]]:
        take_notes(self.notes, current_game_state, round_history, self.name)
        available_actions = self.available_actions()

        agent_message = build_and_chat(
            self.name,
            available_actions,
            other_players,
            round_history,
            current_game_state,
            self.coins,
            self.notes.format_notes(),
            f"It is my move as {self.name} and I have {self._pretty_print_cards()} in my hand",
        )

        chosen_action = parse_action(agent_message["content"])
        if not chosen_action:
            print_text(
                f"Error: Invalid action {agent_message['content']} returned. Trying again...",
                style="red",
            )
            time.sleep(5)
            return self.choose_action(other_players, round_history, current_game_state)

        try:
            action_type = ActionType[chosen_action.lower().replace("action", "")]
            target_action = next(
                action for action in available_actions if action.action_type == action_type
            )
        except (KeyError, StopIteration):
            print_text(
                f"Error: invalid action name, {chosen_action}. Available actions: {available_actions}",
                style="red",
            )
            time.sleep(5)
            return self.choose_action(other_players, round_history, current_game_state)

        target_player = None
        if target_action.requires_target:
            target_player_name = parse_action(agent_message["content"], "targeted_player")
            target_player = next(
                (player for player in other_players if player.name == target_player_name), None
            )
            if not target_player:
                print_text(
                    f"Error: Invalid target player '{target_player_name}'. Trying again...",
                    style="red",
                )
                time.sleep(5)
                return self.choose_action(other_players, round_history, current_game_state)

        return target_action, target_player

    def determine_challenge(
        self,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        agent_message = build_and_chat(
            self.name,
            "Challenge player action: True or False. \nTrue: challenge the player's action.\
            \nFalse: do not challenge the player's action.\
            The JSON dict returned should ONLY be '{action: True/False}'",
            other_players,
            round_history,
            current_game_state,
            self.coins,
            self.notes.format_notes(),
            f"It is my chance to challenge the most recent action taken by {player_being_challenged.name} as {self.name}.\
            I have {self._pretty_print_cards()} in my hand",
            format_actions=False,
        )

        challenge_action = parse_action(agent_message["content"])
        if isinstance(challenge_action, bool):
            return challenge_action
        elif isinstance(challenge_action, str):
            return challenge_action.lower() == "true"
        else:
            print_text(
                f"Error: invalid challenge action '{challenge_action}'. Trying again...",
                style="red",
            )
            time.sleep(5)
            return self.determine_challenge(
                player_being_challenged, other_players, round_history, current_game_state
            )

    def determine_counter(
        self,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: List[str],
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        agent_message = build_and_chat(
            self.name,
            "Counter player action: True or False. \nTrue: Counter the player's action.\
            \nFalse: do not counter the player's action.\
            The JSON dict returned should ONLY be '{action: True/False}'",
            other_players,
            round_history,
            current_game_state,
            self.coins,
            self.notes.format_notes(),
            f"It is my chance to counter the most recent action taken by {player_being_challenged.name} as {self.name}.\
            I have {self._pretty_print_cards()} in my hand",
            format_actions=False,
        )

        counter_action = parse_action(agent_message["content"])

        # if we were passed in a bool, return that
        if isinstance(counter_action, bool):
            return counter_action

        # or if we were passed in a string, check if it is "true" or "false"
        elif isinstance(counter_action, str):
            return counter_action.lower() == "true"
        else:
            print_text(
                f"Error: invalid counter action '{counter_action}'. Trying again...", style="red"
            )
            time.sleep(5)
            return self.determine_counter(
                player_being_challenged, other_players, round_history, current_game_state
            )

    def remove_card(
        self, round_history: List[str], current_game_state: Union[str, Dict[str, str]]
    ) -> str:
        agent_message = build_and_chat(
            self.name,
            f"Remove a card from your hand (zero indexed). Return 0 for the 1st card, 1 for the second card, etc.\
            The index returned MUST be between the range 0 and {len(self.cards) - 1}.\
            The JSON dict returned should ONLY have the key 'action' with the card number as the value'",
            [],
            round_history,
            current_game_state,
            self.coins,
            self.notes.format_notes(),
            f"I am playing as {self.name} and I have to remove a card from my hand.\
            My current deck is {self._pretty_print_cards()}",
            format_actions=False,
        )

        index = parse_action(agent_message["content"])

        # check that we were passed in a valid index and integer
        if not isinstance(index, int) or index < 0 or index >= len(self.cards):
            print_text(f"Error: Invalid index '{index}'. Trying again...", style="red")
            time.sleep(5)
            return self.remove_card(round_history, current_game_state)

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
        self.cards += exchange_cards
        random.shuffle(self.cards)

        formatted_exhange_cards = ", ".join(str(card) for card in exchange_cards)

        agent_message = build_and_chat(
            self.name,
            f"Exchange 2 cards from your hand (zero indexed) as a list.\
            For example, return [0,1] to remove the first and second card.\
            To return the 1st and 3rd cards in the deck, return [1,3].\
            The indices returned MUST be between the range 0 and {len(self.cards) - 1},\
            and the returned value MUST be a list of 2 integers only that are unique.\
            The JSON dict returned should ONLY have a key of 'action' with a value of a list of 2 valid integers",
            [],
            round_history,
            current_game_state,
            self.coins,
            self.notes.format_notes(),
            f"I am playing as {self.name} and I have to exchange 2 cards.\
            My current deck is {self._pretty_print_cards()} after adding in the exchanged cards to my deck.\
            The random cards I got from the deck were {formatted_exhange_cards}",
            format_actions=False,
        )

        indices = parse_action(agent_message["content"])

        # validate that we were passed in a list of 2 unique integers that are within the range of our cards
        if (
            not isinstance(indices, list)  # noqa: W503
            or len(indices) != 2  # noqa: W503
            or not all(  # noqa: W503
                isinstance(i, int) and 0 <= i < len(self.cards) for i in indices  # noqa: W503
            )  # noqa: W503
            or indices[0] == indices[1]  # noqa: W503
        ):
            print_text(f"Error: Invalid indices '{indices}'. Trying again...", style="red")
            time.sleep(5)
            return self.choose_exchange_cards(exchange_cards, round_history, current_game_state)

        print_text(f"{self} exchanges 2 cards")

        first_card = self.cards[indices[0]]
        second_card = self.cards[indices[1]]

        # Remove the larger index first
        self.cards.pop(max(indices))
        self.cards.pop(min(indices))

        return first_card, second_card
