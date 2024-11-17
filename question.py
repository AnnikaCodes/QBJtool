# This file contains a sane representation of questions — for
# stats purposes.
# TODO: bonuses
from typing import Optional
from ids import Player, Team

class Buzz:
    """A buzz."""

    position: int
    """The *word* index of the buzz within the tossup text"""

    player: Player
    team: Team
    points: int # -5, 10, 15
    """The number of points earned by the buzz"""

    def __init__(self, position: int, player: Player, team: Team, points: int) -> None:
        self.position = position
        self.player = player
        self.team = team
        self.points = points

class Tossup:
    """A tossup."""

    text: str
    """The text of the tossup"""

    answer: str
    """The answer line of the tossup"""

    correctBuzz: Optional[Buzz]
    """The buzz that correctly answered this tossup"""

    incorrectBuzz: Optional[Buzz]
    """The buzz that incorrectly answered this tossup"""

    def __init__(
        self, text: str, answer: str, correctBuzz: Optional[Buzz],
        incorrectBuzz: Optional[Buzz]
    ) -> None:
        self.text = text
        self.answer = answer
        self.correctBuzz = correctBuzz
        self.incorrectBuzz = incorrectBuzz

