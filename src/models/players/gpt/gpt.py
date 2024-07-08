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

        _ = user_agent.initiate_chat(group_chat_manager, message=f"It is my move as {self.name}")
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
            print(f"Error: Invalid action name '{chosen_action_type}'")
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

    def determine_challenge(self, player: BasePlayer) -> bool:
        """Choose whether to challenge the current player"""

        # 20% chance of challenging
        return random.randint(0, 4) == 0

    def determine_counter(self, player: BasePlayer) -> bool:
        """Choose whether to counter the current player's action"""

        # 10% chance of countering
        return random.randint(0, 9) == 0

    def remove_card(self) -> str:
        """Choose a card and remove it from your hand"""

        # Remove a random card
        discarded_card = self.cards.pop(random.randrange(len(self.cards)))
        print_texts(
            f"{self} discards their ",
            (f"{discarded_card}", discarded_card.style),
            " card",
        )
        return f"{self} discards their {discarded_card} card"

    def choose_exchange_cards(self, exchange_cards: list[Card]) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""

        self.cards += exchange_cards
        random.shuffle(self.cards)
        print_text(f"{self} exchanges 2 cards")

        return self.cards.pop(), self.cards.pop()
