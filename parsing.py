# This file contains things for turning .qbj and .json files into Python objects
# in a very naive way. What it spits out won't be too useful as-is, but it can be
# made better...(!)

from typing import TypedDict, List
import json

# These types are for what you get from raw JSOn, slightly annoying for actual use
"""Player representation in the QBJ JSOn"""
class QBJPlayer(TypedDict):
    """The player's name."""
    name: str


"""buzzpt representation in the QBJ JSOn"""
class QBJBuzzPosition(TypedDict):
    word_index: int


"""controlled_points representation in the QBJ JSOn"""
class QBJControlledPoints(TypedDict):
    controlled_points: int
    # TODO: figure out bounceback_points

"""Value wrapper for QBJ json"""
class QBJIntValue(TypedDict):
    value: int

"""Typing for `["match_teams"][n]["lineups"][n]` in a QBJ file"""
class QBJLineup(TypedDict):
    first_question: int
    players: List[QBJPlayer]

"""Typing for `["match_teams"][n]["match_players"][n]["answer_counts][n]` in a QBJ file"""
class QBJAnswerCount(TypedDict):
    answer: QBJIntValue
    number: int

"""Typing for `["match_teams"][n]["match_players"][n]` in a QBJ file"""
class QBJMatchPlayer(TypedDict):
    player: QBJPlayer
    tossups_heard: int
    answer_counts: List[QBJAnswerCount]

"""Typing for `["match_teams"][n]["team"]` in a QBJ file"""
class QBJTeam(TypedDict):
    name: str
    players: List[QBJPlayer]

""""Typing for the list elements of the `match_teams` entry of a QBJ file

This is not the same as a QBJTeam, which comes up lots of places — this one
is only for the `match_teams` list.
"""
class QBJMatchTeam(TypedDict):
    # probably pts from bonuses?
    bonus_points: int
    #...
    lineups: List[QBJLineup]
    match_players: List[QBJMatchPlayer]
    team: QBJTeam

"""Typing for `["match_questions"][n]["buzzes"][n]` in a QBJ file"""
class QBJBuzz(TypedDict):
    buzz_position: QBJBuzzPosition
    player: QBJPlayer
    team: QBJTeam
    result: QBJIntValue

"""Typing for `["match_questions"][n]["tossup_question"]` & `["match_questions"][n]["bonus"]["question"]` in a QBJ file"""
class QBJQuestionInfo(TypedDict):
    """1 for tossup, 3 for bonus, else wtf"""
    parts: int
    """`tossup` or `bonus`"""
    type: str
    """The corresponding question number"""
    question_number: int

"""Typing for `["match_questions"][n]["bonus"]` in a QBJ file"""
class QBJBonus(TypedDict):
    question: QBJQuestionInfo
    # WHY IS IT nOT JUST A LIST OF InTS....
    parts: List[QBJControlledPoints]

"""Typing for `["match_questions"][n]` in a QBJ file"""
class QBJMatchQuestions(TypedDict):
    """The number of the question."""
    question_number: int
    buzzes: List[QBJBuzz]
    tossup_question: QBJQuestionInfo
    bonus: QBJBonus

"""Typing for what you get when you json-parse a .qbj file."""
class QBJ(TypedDict):
    """The number of tossups read in the match."""
    tossups_read: int
    match_teams: List[QBJMatchTeam]
    match_questions: List[QBJMatchQuestions]
    # I'm not sure what this is, but it looks like an integer!
    _round: int
    """some kind of info about the packets read"""
    packets: str

"""Typing for `["tossups"][n]` in a packet .json"""
class PacketJSONTossup(TypedDict):
    question: str
    answer: str
    # vvv THIS is the category! vvv
    metadata: str

"""Typing for `["bonuses"][n]` in a packet .json"""
class PacketJSONBonus(TypedDict):
    leadin: str
    parts: List[str] # *should* be length 3
    answers: List[str]
    values: List[str]
    difficultyModifiers: List[str] # e, m, h
    # vvv THIS is the category! vvv
    metadata: str

"""Typing for what you get when you json-parse a packet .json file."""
class PacketJSON(TypedDict):
    tossups: List[PacketJSONTossup]
    bonuses: List[PacketJSONBonus]

def parseQBJ(filename: str) -> QBJ:
    """Parses a QBJ file from JSOn to raw QBJ object

    Args:
        filename (str): path of .qbj

    Returns:
        QBJ: QBJ json
    """
    with open(filename) as f:
        return json.load(f)

# with open("sample.qbj") as f:
#     qbj: QBJ = json.load(f)
#     print(qbj["match_questions"][3]["bonus"]["parts"][2]["controlled_points"])
#     print(qbj["match_questions"][3])