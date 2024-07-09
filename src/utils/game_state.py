from typing import Dict, List, Optional, Union

from rich.panel import Panel
from rich.table import Column, Table
from rich.text import Text

from src.models.card import Card
from src.models.players.human import BasePlayer


def generate_state_panel(
    deck: List[Card], treasury_coins: int, current_player: BasePlayer, rich: bool = True
) -> Union[Panel, Dict[str, Union[int, str]]]:
    """Generate a panel or dictionary showing game information"""
    if rich:
        return Panel(
            f"""
:game_die: Deck: {len(deck)} cards
:moneybag: Treasury: {treasury_coins} coins
:person_tipping_hand: Current Player: [bold magenta]{current_player}
""",
            width=50,
        )
    else:
        return {
            "deck_size": len(deck),
            "treasury_coins": treasury_coins,
            "current_player": str(current_player),
        }


def generate_players_table(
    players: List[BasePlayer],
    current_player_index: int,
    rich: bool = True,
    challenged_player: Optional[BasePlayer] = None,
) -> Union[Table, List[Dict[str, Union[str, int, bool, List[str]]]]]:
    """Generate a table or list of dictionaries of the players"""
    if rich:
        table = Table("Players", "Coins", Column(header="Cards", justify="center", min_width=40))
        for ind, player in enumerate(players):
            if player.is_ai:
                player_text = Text.from_markup(f":robot: {str(player)}")
            else:
                player_text = Text.from_markup(f":grimacing: {str(player)}")
            if ind == current_player_index:
                player_text.stylize("bold magenta")
            coin_text = Text(str(player.coins), style="gray")
            card_text = Text()
            if player.is_active:
                for card in player.cards:
                    if player.is_ai and ind != current_player_index:
                        card_text.append("<Secret...> ")
                    else:
                        card_text.append(
                            str(card),
                            style=f"{card.foreground_color} on {card.background_color}",
                        )
                        card_text.append(" ")
            else:
                card_text = Text.from_markup(":skull:")
            table.add_row(player_text, coin_text, card_text)
        return table
    else:
        players_info = []
        for ind, player in enumerate(players):
            # if there's a challenged player, don't leak information incorrectly
            # we pass in the challenged player in order to pass in the
            # correct information to the LLM for constructing the prompt
            if challenged_player:
                is_currently_going = player == challenged_player
            else:
                is_currently_going = ind == current_player_index
            player_info = {
                "name": str(player),
                "is_currently_going": is_currently_going,
                "coins": player.coins,
                "eliminated": not player.is_active,
            }

            if player.is_active:
                # remove the ind != current_player_index check if back to using humans
                if player.is_ai and ind != current_player_index:
                    player_info["cards"] = ["<Secret...>"] * len(player.cards)
                else:
                    player_info["cards"] = [str(card) for card in player.cards]
            else:
                player_info["cards"] = ["<Eliminated>"]

            players_info.append(player_info)

        return players_info
