# This file contains the overall state tracker for a whole tournament.

from typing import List, Tuple, Dict, TypedDict
from ids import Player, Team, Category
from question import Tossup, Buzz
from parsing import QBJ, PacketJSON

# TODO: also track PPG per category (& overall)

class PlayerCatStat:
    """A player's statistics in a category."""
    points: int
    """The number of points the player has earned in this category."""
    powers: int
    """The number of +15 pts the player has earned in this category."""
    gets: int
    """The number of tossups the player has correctly answered in this category."""
    negs: int
    """The number of tossups the player has incorrectly answered in this category."""
    buzzPositions: List[int]

    def __init__(self) -> None:
        """Default initialization w/ no questions"""
        self.points = 0
        self.powers = 0
        self.gets = 0
        self.negs = 0
        self.buzzPositions = []

    def __str__(self) -> str:
        # TODO: average buzz position
        #averageBuzzPosition = sum(self.buzzPositions) / len(self.buzzPositions)
        return f"Points: {self.points} ({self.powers}/{self.gets}/{self.negs})" #, average buzz position: {averageBuzzPosition}"
    def __repr__(self) -> str:
        return f"'{str(self)}'"

class Tournament:
    """A tournament."""

    #teams: List[Tuple[Team, List[Player]]]
    # TODO: teams
    """Every team in the tournament, paired with its players."""

    players: List[Player] # memory usage is irrelevant; let's just store the players
    """Every player in the tournament."""

    tossups: List[Tossup]

    playerStatsByCategory: Dict[Player, Dict[Category, PlayerCatStat]]

    def __init__(self) -> None:
        """Default initialization."""
        self.players = []
        self.tossups = []
        self.playerStatsByCategory = {}

    def addQBJAndPacket(self, qbj: QBJ, packet: PacketJSON) -> None:
        """Imports a QBJ parsed json object with associated parsed packet.

        Args:
            qbj (QBJ): parsed QBJ file
            packet (PacketJSON): packet that is the one used for the QBJ
        """
        # iterate over tossups and update state for them
        for rawTossup in qbj["match_questions"]:
            # get the question text from the packet
            qnIdx = rawTossup["question_number"] - 1 # 1-indexed
            if qnIdx >= len(packet["tossups"]):
                print(f"Warning: tossup number {qnIdx} not found in packet")
                continue

            text = packet["tossups"][qnIdx]["question"]
            answer = packet["tossups"][qnIdx]["answer"]
            category = packet["tossups"][qnIdx]["metadata"]

            correctBuzz = None
            incorrectBuzz = None
            # iterate over buzzes and look for gets/powers/negs
            for rawBuzz in rawTossup["buzzes"]:
                player = rawBuzz["player"]["name"]
                if player not in self.players:
                    self.players.append(player)

                points = rawBuzz["result"]["value"]
                position = rawBuzz["buzz_position"]["word_index"]
                buzz = Buzz(position, player, "teams aren't real yet", points)

                if points > 0:
                    if correctBuzz is not None:
                        print(f"Warning: multiple correct buzzes on tossup with answerline '{answer}'")
                    correctBuzz = buzz
                else:
                    # TODO rework incorrect buzz tracking — OK to have >1 0s but not >1 -5s
                    # if incorrectBuzz is not None:
                    #     print(f"Warning: multiple negs on tossup with answerline '{answer}' (this neg: {player})")
                    incorrectBuzz = buzz

                # update player stats
                if player not in self.playerStatsByCategory:
                    self.playerStatsByCategory[player] = {}
                if category not in self.playerStatsByCategory[player]:
                    self.playerStatsByCategory[player][category] = PlayerCatStat()

                self.playerStatsByCategory[player][category].points += points
                self.playerStatsByCategory[player][category].buzzPositions.append(position)
                if points == 15:
                    self.playerStatsByCategory[player][category].powers += 1
                if points > 0:
                    self.playerStatsByCategory[player][category].gets += 1
                else:
                    self.playerStatsByCategory[player][category].negs += 1
            self.tossups.append(Tossup(text, answer, correctBuzz, incorrectBuzz))

