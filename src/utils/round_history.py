class RoundHistory:
    def __init__(self):
        self.current_round = ["Start"]
        self.previous_round = []

    def append(self, entry: str) -> None:
        """Append a new entry to the current round history."""
        self.current_round.append(entry)

    def conclude_round(self) -> str:
        """Mark the current round as concluded and prepare for the next round."""
        if len(self.current_round) > 1:  # More than just "Start"
            self.previous_round = self.current_round
            self.current_round = ["Start"]
            return "Round concluded. Starting new round."
        return "Round concluded with no additional entries."

    def __str__(self) -> str:
        """Return a string representation of the round history."""
        previous = (
            "Previous Round:\n" + "\n".join(self.previous_round)
            if self.previous_round
            else "No previous round"
        )
        current = "Current Round:\n" + "\n".join(self.current_round)
        return f"{previous}\n\n{current}"

    def get_full_history(self):
        """Return the full history including both previous and current rounds."""
        return self.previous_round + self.current_round

    def reset(self):
        """Reset the round history."""
        self.__init__()
