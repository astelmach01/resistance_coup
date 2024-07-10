import os
from collections import defaultdict
from typing import Annotated, Dict, List, Union

from autogen import ConversableAgent, register_function
from pydantic import BaseModel

from src import PLAYER_NOTES_DIR
from src.models.players.gpt.prompts import note_prompt


class Notes(BaseModel):
    notes: Dict[str, List[str]] = {}

    def __init__(self, **data):
        super().__init__(**data)
        self.notes = defaultdict(list)

    def add_note(self, character: str, note: str) -> str:
        self.notes[character].append(note)
        return "Successfully added note."

    def delete_note(self, character: str, note: str) -> str:
        if character not in self.notes:
            return f"Character {character} not found. The available characters are: {', '.join(self.notes.keys())}"

        if note in self.notes[character]:
            self.notes[character].remove(note)
            return "Successfully deleted note."

        else:
            return f"Note {note} not found for character {character}.\
        The available notes are: {', '.join(self.notes[character])}"

    def format_notes(self) -> str:
        return "\n".join(
            f"{character}:\n" + "\n".join(f"\t{i+1}. {note}" for i, note in enumerate(notes))
            for character, notes in self.notes.items()
        )

    def __str__(self):
        return self.format_notes()

    class Config:
        arbitrary_types_allowed = True


def take_notes(
    player_notes: Notes,
    current_game_state: Union[str, Dict[str, str]],
    round_history: List[str],
    current_player_name: str,
) -> None:
    def add_note(
        character: Annotated[str, "The character to add a note for"],
        notes: Annotated[
            List[str], "The note(s) to add. Entries can be just a string, without numbers"
        ],
    ) -> str:
        response = ""
        for i, note in enumerate(notes):
            # format this so we know which note was added
            response += f"{i+1}. {player_notes.add_note(character, note)}\n"

        return response

    def delete_note(
        character: Annotated[str, "The character to delete a note for"],
        notes: Annotated[
            List[str],
            "The note(s) to delete. Entries should be just a string, without numbers.\
            The string should match exactly with the note to delete",
        ],
    ) -> str:
        response = ""
        for i, note in enumerate(notes):
            # format this so we know which note was deleted
            response += f"{i+1}. {player_notes.delete_note(character, note)}\n"

        return response

    note_take_prompt = note_prompt.replace("{{GAME_STATE}}", str(current_game_state)).replace(
        "{{ROUND_HISTORY}}", str(round_history).replace("{{PLAYER_NOTES}}", str(player_notes))
    )

    llm_config = {"model": "gpt-4o", "api_key": os.environ.get("OPENAI_API_KEY")}
    note_taker = ConversableAgent(
        name="Note Taker",
        system_message=note_take_prompt,
        llm_config=llm_config,
    )

    user_proxy = ConversableAgent(
        name="User",
        llm_config=False,
        human_input_mode="NEVER",
        is_termination_msg=lambda msg: msg.get("content") is not None
        and "terminate" in msg["content"].lower(),  # noqa
    )

    register_function(
        add_note,
        caller=note_taker,
        executor=user_proxy,
        name="add_note",
        description="Add a note or multiple notes about an opposing character in the game.\
        Returns a message indicating the success or failure of the addition(s) for the corresponding notes passed in.",
    )

    register_function(
        delete_note,
        caller=note_taker,
        executor=user_proxy,
        name="delete_note",
        description="Delete a note or multiple notes about an opposing character in the game.\
        Returns a message indicating the success or failure of the deletion(s) for the corresponding notes passed in.",
    )

    _ = user_proxy.initiate_chat(
        note_taker, message=f"I am currently playing as {current_player_name}.", max_turns=3
    )

    with open(PLAYER_NOTES_DIR / f"{current_player_name}_notes.txt", "w") as f:
        f.write(str(player_notes))
