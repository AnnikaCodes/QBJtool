from typing import TypedDict, List
import json

# These types are for what you get from raw JSOn, slightly annoying for actual use

"""Player representation in the QBJ JSOn"""
class QBJPlayer(TypedDict):
    """The player's name."""
    name: str

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

""""Typing for the list elements of the `match_teams` entry of a QBJ file"""
class QBJMatchTeam(TypedDict):
    # probably pts from bonuses?
    bonus_points: int
    #...
    lineups: List[QBJLineup]
    match_players: List[QBJMatchPlayer]
    team: QBJTeam

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



with open("sample.qbj") as f:
    qbj = QBJ(json.load(f))
    print(qbj)