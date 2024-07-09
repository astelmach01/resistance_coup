## flake8: noqa

game_rules = """
    # Resistance Coup Game Rules

## Setting
- Future dystopia where multinational CEOs form a new "royal class" government
- Economic oppression has led to the rise of The Resistance
- Players are powerful government officials seeking absolute power

## Objective
- Eliminate the influence of all other players
- Be the last survivor

## Components
- Character Cards: 3 each of Duke, Assassin, Captain, Ambassador, Contessa (15 total)
- 6 Summary Cards
- 50 Coins
- Instructions

## Setup
1. Shuffle all character cards
2. Deal 2 cards face-down to each player
3. Place remaining cards in the center as the Court deck
4. Give each player 2 coins
5. Place remaining coins in the center as the Treasury
6. Distribute summary cards to players (for reference only)
7. Players should familiarize themselves with all actions and characters before starting
8. The winner of the last game starts (or choose a starting player randomly)

## Key Concepts
### Influence
- Face-down cards represent a player's influence at court
- Losing influence means revealing a card
- Players choose which card to reveal when losing influence
- A player with no face-down cards is exiled and out of the game
- Revealed cards remain face up in front of the player and no longer provide influence

## Gameplay
- Turns proceed clockwise
- Each turn, a player must choose one action
- Players cannot pass their turn
- Other players can challenge or counteract the chosen action
- Unchallenged/uncountered actions automatically succeed
- Challenges are resolved before actions or counteractions
- A player with 10+ coins must launch a Coup as their only action

## Actions
### General Actions (Always Available)
1. Income: Take 1 coin from the Treasury
2. Foreign Aid: Take 2 coins from the Treasury (can be blocked by Duke)
3. Coup: Pay 7 coins to force another player to lose influence (always successful)

### Character Actions (Require claiming influence)
1. Duke - Tax: Take 3 coins from the Treasury
2. Assassin - Assassinate: Pay 3 coins to make another player lose influence (can be blocked by Contessa)
3. Captain - Steal: Take 2 coins from another player (1 if they only have 1) (can be blocked by Ambassador or Captain)
4. Ambassador - Exchange: Take 2 random cards from the Court deck, choose which (if any) to exchange with your face-down cards, then return two cards to the Court deck

### Counteractions
- Can be used to block or intervene in another player's action
- Operate like character actions (can be claimed without proof)
- If unchallenged, automatically succeed
- If an action is counteracted, it fails, but any coins paid remain spent

#### Specific Counteractions
1. Duke: Blocks Foreign Aid
2. Contessa: Blocks Assassination
3. Ambassador/Captain: Blocks Stealing

## Challenges
- Any action or counteraction using character influence can be challenged
- Any player can issue a challenge, regardless of whether they are involved in the action
- Challenges must be made immediately after an action/counteraction is declared
- To win a challenge, the challenged player must prove they have the claimed character
- Losing a challenge results in losing influence
- Winning a challenge by revealing a card: 
  1. Return the revealed card to the Court deck
  2. Shuffle the Court deck
  3. Draw a replacement card
- If an action is successfully challenged, it fails and any paid coins are returned

## Special Rules
1. Assassination risks: Possible to lose 2 influence in one turn (e.g., failing to challenge an Assassin, or bluffing a Contessa and being challenged)
2. No binding negotiations or card reveals between players
3. No giving or lending coins between players
4. No second place
5. A player who loses all influence must immediately return all their coins to the Treasury

## Game End
- The game ends when only one player remains
- The last player with influence wins
    """


reasoning_prompt = """
You are a genius board game player, masterful and wise. Your task is to analyze the current state of a game and determine the best next action/move to take in order to win. Follow these instructions carefully:

1. First, review the rules of the game:
<game_rules>
{{GAME_RULES}}
</game_rules>

2. Next, familiarize yourself with the available actions:
<available_actions>
{{AVAILABLE_ACTIONS}}
</available_actions>

3. Now, examine the current state of the game:
<current_game_state>
{{CURRENT_GAME_STATE}}
</current_game_state>

4. If there have been any previous turns in this round, review them:
<previous_turns>
{{PREVIOUS_TURNS}}
</previous_turns>

5. Analyze the situation and determine the best next action:
   a. Consider the game rules, available actions, current game state, and previous turns (if any).
   b. Think through potential strategies and their outcomes.
   c. Evaluate the pros and cons of each possible action.
   d. Consider how your action might affect other players and their potential responses.

6. Provide your analysis and decision in the following format:
   <analysis>
   Step-by-step thought process leading to your decision. Include:
   - Key observations about the current game state
   - Potential strategies considered
   - Evaluation of different actions
   - Anticipated outcomes and opponent responses
   </analysis>

   <decision>
   Clear statement of the chosen action and a brief explanation of why it's the best move.
   </decision>
   
   Remember to not introduce any external information and that if an action requires a targeted player, ensure that player's name is clearly identified in your decision.
"""


verifier_prompt = """
You are an expert board game analyst tasked with critiquing a proposed plan for a game in progress. You also have a keen eye for any mistakes. You will be provided with the game rules, current game state, previous turns (if any), and a proposed plan. Your job is to thoroughly analyze a plan for the next action, identify any flaws, and recommend the best course of action. These flaws may include incorrect parameters returned, invalid actions, or illogical decisions.

First, familiarize yourself with the game:

<game_rules>
{{GAME_RULES}}
</game_rules>

Now, consider the current state of the game:

<game_state>
{{GAME_STATE}}
</game_state>

Review any previous turns in this round:

<previous_turns>
{{PREVIOUS_TURNS}}
</previous_turns>


Finally, examine the possible actions you can take and make sure we can take ONLY one of the following actions:
<available_actions>
{{AVAILABLE_ACTIONS}}
</available_actions>


To analyze this plan, follow these steps:

1. Think through the plan step-by-step, considering how it interacts with the game rules and current game state.
2. Identify any potential flaws or weaknesses in the plan.
3. Consider alternative strategies that might be more effective.
4. Evaluate the overall effectiveness of the plan in the context of the game's objectives.

Write out your analysis in a <analysis> tag. Use <step> tags to clearly delineate each step of your thinking process.

After your analysis, provide your final recommendation for the action that should be taken. This may be the proposed plan, a modified version of the plan, or a completely different action. Write your recommendation in a <recommendation> tag.

Your entire response should be structured as follows:

<response>

<analysis>
<step>Step 1 analysis...</step>
<step>Step 2 analysis...</step>
<step>Step 3 analysis...</step>
...
</analysis>

<recommendation>
Final recommended action...
</recommendation>

</response>

Remember to base your analysis and recommendation solely on the information provided in the game rules, game state, previous turns, and proposed plan. Do not introduce any external information or assumptions not included in these inputs. If the action requires a targeted player, ensure that player's name is clearly identified in your recommendation.
"""


action_prompt = """
You are tasked with generating a valid JSON dict based on reasoning steps for a move in a board game and a list of available actions. Follow these instructions carefully:

1. First, review the recommended action provided.

2. Next, examine the list of available actions:
<available_actions>
{{AVAILABLE_ACTIONS}}
</available_actions>

3. Match this conclusion with the most appropriate action from the list of available actions.

4. Generate a JSON dict based on your analysis. The JSON should be in the following format:
   {"action": "value", "targeted_player": "targeted player" (if applicable)}

   Note: 
   - The "action" key should always be present and its value should be one of the available actions.
   - Include the "targeted_player" key only if the action targets a specific player. In the case of challenging, omit the "targeted_player" key.
   - If no player is targeted, omit the "targeted_player" key entirely.

Remember to ensure that the action you choose is valid and present in the list of available actions. If the reasoning steps don't clearly match any available action, choose the closest logical match based on the context provided. Remember to generate valid JSON only.
"""
