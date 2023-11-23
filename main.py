# Import necessary SPADE classes
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, FSMBehaviour, State
import random
import asyncio
import threading

def async_input(prompt):
    """
    A function to get user input asynchronously.
    """
    return loop.run_in_executor(None, input, prompt)

# Note: Ensure 'loop' is the asyncio event loop instance you create in your main execution.


# Define the names of the states
START_STATE = "StartState"
EXPLORE_STATE = "ExploreState"
BATTLE_STATE = "BattleState"
CAPTURE_STATE = "CaptureState"
REST_STATE = "RestState"
END_STATE = "EndState"


class Pokemon:
    def __init__(self, name, hp, attack_name, attack_damage_min, attack_damage_max):
        self.name = name
        self.hp = hp
        self.max_hp = hp  # Add this line to store the maximum HP
        self.attack_name = attack_name
        self.attack_damage_min = attack_damage_min
        self.attack_damage_max = attack_damage_max

    def attack(self):
        return random.randint(self.attack_damage_min, self.attack_damage_max)

# Example Pokémon
pikachu = Pokemon("Pikachu", 10, "Thunder Shock", 1, 3)
bulbasaur = Pokemon("Bulbasaur", 12, "Vine Whip", 2, 4)
charmander = Pokemon("Charmander", 11, "Flame Tail", 2, 3)
squirtle = Pokemon("Squirtle", 13, "Water Gun", 1, 4)
eevee = Pokemon("Eevee", 10, "Tackle", 1, 3)
jigglypuff = Pokemon("Jigglypuff", 15, "Sing", 0, 2)
psyduck = Pokemon("Psyduck", 12, "Confusion", 1, 3)
meowth = Pokemon("Meowth", 10, "Scratch", 1, 3)
growlithe = Pokemon("Growlithe", 12, "Bite", 2, 4)
pidgey = Pokemon("Pidgey", 9, "Gust", 1, 2)

EMPTY = 0
BATTLE = 1
REST = 2
CAPTURE = 3


def create_map():
    return [[random.choice([EMPTY, BATTLE, CAPTURE]) for _ in range(10)] for _ in range(10)]

game_map = create_map()
game_map = create_map()
# Each state is a behavior

class StartState(State):
    async def run(self):
        print("Welcome to PokéQuest: The Journey Begins!")
        # Assign a random Pokémon to the player
        self.agent.pokemon = random.choice([pikachu, bulbasaur, charmander, squirtle, eevee, jigglypuff, psyduck, meowth, growlithe, pidgey])

        # Increase the player's Pokémon HP by 10
        self.agent.pokemon.hp += 10
        self.agent.pokemon.max_hp += 10

        print(f"You have been assigned: {self.agent.pokemon.name} with {self.agent.pokemon.hp} HP")
        self.set_next_state(EXPLORE_STATE)


class ExploreState(State):
    async def run(self):
        print("Exploring the world...")
        action = await async_input("What would you like to do? (move/rest): ")

        # Handle "rest" action first to avoid triggering a battle
        if action == "rest":
            print("You decide to take a rest...")
            self.set_next_state(REST_STATE)
            return  # Return immediately to avoid further processing

        if action == "move":
            direction = input("Which direction would you like to travel? (up/down/left/right): ").lower()

            # Update position based on direction
            if direction == "up":
                self.agent.position[0] = max(0, self.agent.position[0] - 1)
            elif direction == "down":
                self.agent.position[0] = min(9, self.agent.position[0] + 1)
            elif direction == "left":
                self.agent.position[1] = max(0, self.agent.position[1] - 1)
            elif direction == "right":
                self.agent.position[1] = min(9, self.agent.position[1] + 1)
            else:
                print("Invalid direction. Please choose up, down, left, or right.")

            # Display current position
            print(f"Current position: Row {self.agent.position[0]}, Column {self.agent.position[1]}")

            # Check if the current tile is empty or has an event
            current_tile = game_map[self.agent.position[0]][self.agent.position[1]]
            if current_tile == EMPTY:
                print("You find nothing unusual here.")
                # Check if all tiles are empty, if so, end the game
                if all(tile == EMPTY for row in game_map for tile in row):
                    self.set_next_state(END_STATE)
                else:
                    self.set_next_state(EXPLORE_STATE)
            elif current_tile == BATTLE:
                self.set_next_state(BATTLE_STATE)
            elif current_tile == CAPTURE:
                self.set_next_state(CAPTURE_STATE)

        else:
            print("Invalid action. Please choose 'move' or 'rest'.")
            self.set_next_state(EXPLORE_STATE)  # Return to explore state for valid input


class BattleState(State):
    async def run(self):
        opponent_pokemon = random.choice([pikachu, bulbasaur, charmander, squirtle, eevee, jigglypuff, psyduck, meowth, growlithe, pidgey])
        print(f"A wild {opponent_pokemon.name} appears!")

        player_pokemon = self.agent.pokemon

        while player_pokemon.hp > 0 and opponent_pokemon.hp > 0:
            # Player's turn
            damage = player_pokemon.attack()
            opponent_pokemon.hp -= damage
            print(f"Your {player_pokemon.name} attacks {opponent_pokemon.name}, causing {damage} damage.")
            print(f"{opponent_pokemon.name}'s HP is now {max(opponent_pokemon.hp, 0)}.")

            await asyncio.sleep(2)

            if opponent_pokemon.hp <= 0:
                print(f"You defeated {opponent_pokemon.name}!")
                game_map[self.agent.position[0]][self.agent.position[1]] = EMPTY  # Set the tile to EMPTY
                self.set_next_state(EXPLORE_STATE)
                break  # Break out of the loop immediately

            # Opponent's turn
            damage = opponent_pokemon.attack()
            player_pokemon.hp -= damage
            print(f"{opponent_pokemon.name} attacks your {player_pokemon.name}, causing {damage} damage.")
            print(f"Your {player_pokemon.name}'s HP is now {max(player_pokemon.hp, 0)}.")

            await asyncio.sleep(2)

            if player_pokemon.hp <= 0:
                print(f"Your {player_pokemon.name} has been defeated!")
                self.set_next_state(END_STATE)
                break  # Break out of the loop immediately

class CaptureState(State):
    async def run(self):
        print("You got captured. Wait 10 seconds to be able to act again.")

        timeout = 10  # 10 seconds timeout
        while timeout > 0:
            await asyncio.sleep(5)  # Wait for 5 seconds
            timeout -= 5
            if timeout > 0:
                print(f"Time remaining: {timeout} seconds")
            else:
                print("Time's up!")

        # After the capture event, set the current tile to EMPTY
        game_map[self.agent.position[0]][self.agent.position[1]] = EMPTY

        # Transition back to the Explore State
        self.set_next_state(EXPLORE_STATE)


class RestState(State):
    async def run(self):
        print("Resting and healing your Pokémon...")
        self.agent.pokemon.hp = self.agent.pokemon.max_hp
        print(f"{self.agent.pokemon.name}'s health has been fully restored.")

        await asyncio.sleep(2)  # Optional: Wait for 2 seconds to simulate resting time

        self.set_next_state(EXPLORE_STATE)  # Transition back to ExploreState

class EndState(State):
    async def run(self):
        print("Your journey ends here, for now...")
        # Signal the game to stop
        self.agent.game_running = False

class PokeQuestAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.loop = asyncio.get_event_loop()  # Set the event loop here
        self.position = [5, 5]  # Starting position in the middle of the map
        self.setup_fsm()
        self.pokemon = None  # Placeholder for player's Pokémon
        self.game_running = True  # Flag to indicate if the game is running

    def setup_fsm(self):
        fsm = FSMBehaviour()

        # Add states to the FSM
        fsm.add_state(START_STATE, StartState(), initial=True)
        fsm.add_state(EXPLORE_STATE, ExploreState())
        fsm.add_state(BATTLE_STATE, BattleState())
        fsm.add_state(CAPTURE_STATE, CaptureState())
        fsm.add_state(REST_STATE, RestState())
        fsm.add_state(END_STATE, EndState())

        # Define transitions
        fsm.add_transition(START_STATE, EXPLORE_STATE)
        fsm.add_transition(EXPLORE_STATE, BATTLE_STATE)
        fsm.add_transition(EXPLORE_STATE, CAPTURE_STATE)
        fsm.add_transition(EXPLORE_STATE, REST_STATE)
        fsm.add_transition(BATTLE_STATE, EXPLORE_STATE)
        fsm.add_transition(BATTLE_STATE, END_STATE)  # Add this transition
        fsm.add_transition(CAPTURE_STATE, EXPLORE_STATE)
        fsm.add_transition(REST_STATE, EXPLORE_STATE)
        fsm.add_transition(EXPLORE_STATE, EXPLORE_STATE)
        fsm.add_transition(EXPLORE_STATE, END_STATE)
        # ... other transitions ...

        # Add FSM to the agent
        self.add_behaviour(fsm)


if __name__ == "__main__":
    try:
        pokequest_agent = PokeQuestAgent("mytestuser1234123@jabbers.one", "4R4k!wtUx87TNUs")
        loop = asyncio.get_event_loop()
        pokequest_agent.loop = loop
        loop.run_until_complete(pokequest_agent.start())
        print("Game is running. Type 'stop' to end.")
        while pokequest_agent.game_running:
            loop.run_until_complete(asyncio.sleep(1))
    except KeyboardInterrupt:
        print("Interrupted by user, stopping game...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        loop.run_until_complete(pokequest_agent.stop())
        loop.close()
