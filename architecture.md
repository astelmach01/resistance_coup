# Agent Architecture


## Overview

The GPT Player is an agent in our game that uses GPT-4o + Microsoft's Autogen to make decisions. The components are loosely based off a couple of research papers, notably [this overview](https://arxiv.org/pdf/2402.03578) as well as [BMW's Agent Framework paper](https://arxiv.org/pdf/2406.20041). [This multi-agent collaboration](https://arxiv.org/pdf/2306.03314) paper also formalizes a framework and confirms intuitions about my approach.

The high level Plan-Verify-Execute architecture overview is as follows:

1) A reasoning agent reviews the current information, reasons through a plan, and decides on an action.
2) A verifier agent checks the reasoning agent's plan and decides if any modifications are necessary.
3) An action parser agent selects the final action to be taken from a list of possible actions.

![Agent Architecture](/assets/architecture.png)

## Key Components

1. **Agents** (`agents.py`):

    All constructed agents are aware of (passed into the context window):
    - The current game state, such as players' coins and active/eliminated players.
    - The game rules
    - The round history (more details below)
    - Notes taken (more details below)
    - Possible actions, like taking income or assassinating another player.

    Agents are constructed with a round-robin groupchat, where the reasoning agent speaks first, followed by the verifier, and finally the action parser. After we extract the action from the action parser, the group chat is closed and subsequent calls start with a newly created group chat. This process occurs for every action that the player needs to make.

    Each of the agents is given a "personality" or "role", that guides their behavior, such as a "verifier". These agent also have corresponding instructions on what to do that differ from one another.

    - Reasoning/Planner Agent
        - Research has shown that giving an LLM "time to think" via explaining its thought process first has improved performance in tasks that require reasoning, compared to directly asking for an action. Thus, this agent primarily thinks through a plan, explains its reasoning, and decides on an action.

    - Verifier Agent
        - Even with a better prompting strategy, LLMs aren't always correct. This agent's job is to double-check the reasoner's logic and make sure the output is correct, based on the requested action. About 5% of the time, the verifier agent has disagreed with the reasoning agent and decided on a different action.

    - Action Parser Agent
        - Rather simple, this agent has instructions to generate a valid JSON dict to be parsed and returned to the game handler. In the very rare case that even the action parser returns invalid JSON/invalid action, we have a retry mechanism in place. If we still can't generate a valid action, we return a random action, although this has never occurred; the system is very reliable in generating valid actions.

2. **Memory**:

    Some major challenges of multi-agent systems are providing the correct context into the LLM, as well as deciding how much context to provide. Typically, model performance degrades as the context is filled. There are 2 forms of memory in the system:

    - Short-term memory:
        - Directly passed into the LLM and discarded afterwards. This includes the current game state, possible actions, and the round history. We keep the short-term memory rather short in order to guide the LLM into a clearly made decision.
        - A round history of publicly available user actions made is kept, such as "Player 1 challenged Player 2's assassination attempt." The most recent 2 rounds of play is stored as the round history, where a round is defined as a full cycle of moves from the first active player to the last active player. Intuitively, the round history does not need to keep track of every single move made from the start, as we have long-term memory to note down important events. For example, it does not matter if Player 1 exchanged 2 cards 20 turns ago, as the game state has likely changed significantly since then.

    - Long-term memory:
        - We give the player access to notes, a completely separate agent that keeps track of suspected strategies and cards of opposing players. For example, if a player assassinates another player, the notes agent would note that there is a decent probability that the player has an Assassin card. Notes can be deleted as well.

3. **Prompts** (`prompts.py`):

    Each agent is a given a role-specific prompt. These prompts were designed by Anthropic's "Generate a Prompt" feature in the dev console, turning my initial prompt into a Chain-of-Thought prompt. Specific context such as round history is then injected via jinja.

### Other Notes
- Player notes for a sample game can be inspected under the `player_notes` directory.
- The corresponding full game text can be found in `full_game_with_notes.txt`.
- Notes are only taken when a player needs to choose an action, but not when challenging, counteracting, or exchanging cards.


## New Code Added

```
game_handler.py
models/
└── players/
    └── gpt/
        ├── __init__.py
        ├── agents.py
        ├── gpt_player_utils.py
        ├── gpt_player.py
        ├── notes.py
        ├── prompts.py
        └── __init__.py
src/
└── utils/
    └── round_history.py
```

`src/handler/game_handler.py` was also slightly modified to include round history.