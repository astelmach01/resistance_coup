import random
import time
from typing import Dict, List, Optional, Tuple, Union

from .gpt_player_utils import build_and_chat, parse_action
from src.models.action import Action, ActionType
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.models.players.gpt.notes import Notes, take_notes
from src.models.players.gpt.prompts import exchange_cards_prompt, remove_card_prompt
from src.utils.print import print_text, print_texts
from src.utils.round_history import RoundHistory


class GPTPlayer(BasePlayer):
    is_ai: bool = True
    notes: Notes = Notes()

    def choose_action(
        self,
        other_players: List[BasePlayer],
        round_history: RoundHistory,
        current_game_state: Union[str, Dict[str, str]],
    ) -> Tuple[Action, Optional[BasePlayer]]:
        take_notes(self.notes, current_game_state, round_history, self.name)
        available_actions = self.available_actions()

        max_attempts = 5

        for _ in range(max_attempts):
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
                continue

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
                continue

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
                    continue

            return target_action, target_player

        print_text(
            f"Error: Failed to choose a valid action after {max_attempts} attempts. Choosing randomly.",
            style="red",
        )
        return random.choice(available_actions), (
            random.choice(other_players) if available_actions[0].requires_target else None
        )

    def _determine_action(
        self,
        action_type: str,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: RoundHistory,
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        while True:
            agent_message = build_and_chat(
                self.name,
                f"{action_type.capitalize()} player action: True or False. \nTrue: {action_type} the player's action.\
                \nFalse: do not {action_type} the player's action.\
                The JSON dict returned should ONLY be '{{action: True/False}}'",
                other_players,
                round_history,
                current_game_state,
                self.coins,
                self.notes.format_notes(),
                f"It is my chance to {action_type} the most recent action taken by {player_being_challenged.name} as {self.name}.\
                    I have {self._pretty_print_cards()} in my hand",
                format_actions=False,
            )

            action_decision = parse_action(agent_message["content"])
            if isinstance(action_decision, bool):
                return action_decision
            elif isinstance(action_decision, str):
                return action_decision.lower() == "true"
            else:
                print_text(
                    f"Error: invalid {action_type} action '{action_decision}'. Trying again...",
                    style="red",
                )
                time.sleep(5)

    def determine_challenge(
        self,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: RoundHistory,
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        return self._determine_action(
            "challenge", player_being_challenged, other_players, round_history, current_game_state
        )

    def determine_counter(
        self,
        player_being_challenged: BasePlayer,
        other_players: List[BasePlayer],
        round_history: RoundHistory,
        current_game_state: Union[str, Dict[str, str]],
    ) -> bool:
        return self._determine_action(
            "counter", player_being_challenged, other_players, round_history, current_game_state
        )

    def remove_card(
        self, round_history: RoundHistory, current_game_state: Union[str, Dict[str, str]]
    ) -> str:
        if not self.cards:
            raise ValueError("Cannot remove card from an empty hand")

        max_attempts = 5

        for _ in range(max_attempts):
            agent_message = build_and_chat(
                self.name,
                remove_card_prompt.replace("{{NUM_CARDS}}", str(len(self.cards))),
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

            if isinstance(index, int) and 0 <= index < len(self.cards):
                discarded_card = self.cards.pop(index)
                print_texts(
                    f"{self} discards their ",
                    (f"{discarded_card}", discarded_card.style),
                    " card",
                )
                return f"{self} discards their {discarded_card} card"
            else:
                print_text(f"Error: Invalid index '{index}'. Trying again...", style="red")
                time.sleep(5)

        return f"{self} discards their {self.cards.pop()} card"

    def choose_exchange_cards(
        self,
        exchange_cards: List[Card],
        round_history: RoundHistory,
        current_game_state: Union[str, Dict[str, str]],
    ) -> Tuple[Card, Card]:
        if not exchange_cards:
            raise ValueError("No cards provided for exchange")

        self.cards += exchange_cards
        random.shuffle(self.cards)

        formatted_exchange_cards = ", ".join(str(card) for card in exchange_cards)

        max_attempts = 5

        for _ in range(max_attempts):
            agent_message = build_and_chat(
                self.name,
                exchange_cards_prompt.replace("{{NUM_CARDS}}", str(len(self.cards))),
                [],
                round_history,
                current_game_state,
                self.coins,
                self.notes.format_notes(),
                f"I am playing as {self.name} and I have to exchange 2 cards.\
                My current deck is {self._pretty_print_cards()} after adding in the exchanged cards to my deck.\
                The random cards I got from the deck were {formatted_exchange_cards}",
                format_actions=False,
            )

            indices = parse_action(agent_message["content"])

            if (
                isinstance(indices, list)  # noqa: W503
                and len(indices) == 2  # noqa: W503
                and all(  # noqa: W503
                    isinstance(i, int) and 0 <= i < len(self.cards) for i in indices  # noqa: W503
                )  # noqa: W503
                and indices[0] != indices[1]  # noqa: W503
            ):
                print_text(f"{self} exchanges 2 cards")

                first_card = self.cards[indices[0]]
                second_card = self.cards[indices[1]]

                # Remove the larger index first
                self.cards.pop(max(indices))
                self.cards.pop(min(indices))

                return first_card, second_card
            else:
                print_text(f"Error: Invalid indices '{indices}'. Trying again...", style="red")
                time.sleep(5)

        return self.cards.pop(), self.cards.pop()
