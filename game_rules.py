"""Pure game-rule helpers shared by the GUI and network state."""

from game_config import CREWMATE_TASK_GOAL


def count_alive(game):
    from roles import Crewmate, Impostor

    alive_crewmates = sum(
        1 for player in game.players
        if player.is_alive and isinstance(player.role, Crewmate)
    )
    alive_impostors = sum(
        1 for player in game.players
        if player.is_alive and isinstance(player.role, Impostor)
    )
    return alive_crewmates, alive_impostors


def crewmates_completed_tasks(game):
    from roles import Crewmate

    living_crewmates = [
        player for player in game.players
        if player.is_alive and isinstance(player.role, Crewmate)
    ]
    if not living_crewmates:
        return True

    return all(
        getattr(player, "completed_tasks", 0) >= CREWMATE_TASK_GOAL
        for player in living_crewmates
    )


def evaluate_game_outcome(game):
    """Return ('crewmate'|'impostor'|None, reason)."""
    alive_crewmates, alive_impostors = count_alive(game)
    if alive_crewmates == 0:
        return "impostor", "no_crewmates"
    if alive_impostors == 0:
        return "crewmate", "no_impostors"

    any_player_out = any(not player.is_alive for player in game.players)
    if alive_impostors >= alive_crewmates and any_player_out:
        return "impostor", "equal_population"
    if crewmates_completed_tasks(game):
        return "crewmate", "all_tasks_completed"
    return None, None
