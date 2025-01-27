# This file contains the overall state tracker for a whole tournament.

from typing import List, Tuple, Dict, TypedDict, Set, Optional
from typing_extensions import Self
from ids import Player, Team, Category
from question import Tossup, Buzz
from parsing import QBJ, PacketJSON
from datetime import datetime
from os import path

# TODO:
#   * Sort players by team like we do for categories
#   * Make a top 5 buzzes per player HTML file.

# categories that are combos of other categories
BIG_CATEGORIES = [
    ("Science", ["Biology", "Chemistry", "Physics", "Other Science"]),
    ("Literature", [
        "American Literature", "British Literature", "European Literature",
        "World Literature", "Other Literature", "World/Other Literature",
        "Ancient/Other Literature",
    ]),
    ("History", [
        "American History", "World History", "European History", "Other History",
        "Ancient History", "Ancient/Other History"
    ]),
    ("Fine Arts", [
        "Painting/Sculpture", "Other Fine Arts", "Classical Music", "Visual Fine Arts",
        "Auditory Fine Arts"

    ]),
    ("RMPSS", ["Religion", "Mythology", "Social Science", "Philosophy"]),
]

def toID(s: str) -> str:
    return s.lower().replace(" ", "-")

class PlayerCatStat:
    """A player's statistics in a category."""
    points: int
    """The number of points the player has earned in this category."""
    powers: int
    """The number of +15 pts the player has earned in this category."""
    tens: int
    """The number of +10 pts the player has earned in this category."""
    negs: int
    """The number of tossups the player has incorrectly answered in this category."""
    buzzPositions: List[int]
    tossupsHeard: int

    def __init__(self) -> None:
        """Default initialization w/ no questions"""
        self.points = 0
        self.powers = 0
        self.tens = 0
        self.negs = 0
        self.tossupsHeard = 0
        self.buzzPositions = []

    def __str__(self) -> str:
        # TODO: average buzz position
        #averageBuzzPosition = sum(self.buzzPositions) / len(self.buzzPositions)
        return f"Points: {self.points} ({self.powers}/{self.tens}/{self.negs})" #, average buzz position: {averageBuzzPosition}"
    def __repr__(self) -> str:
        return f"'{str(self)}'"

    def __add__(self, other: Self):
        new = PlayerCatStat()
        new.points = self.points + other.points
        new.powers = self.powers + other.powers
        new.tens = self.tens + other.tens
        new.negs = self.negs + other.negs
        new.buzzPositions = self.buzzPositions + other.buzzPositions
        new.tossupsHeard = self.tossupsHeard + other.tossupsHeard
        return new

Lineup = Tuple[int, List[Player]]
"""int is the first question number the lineup starts on"""

class Tournament:
    """A tournament."""

    players: Dict[Player, int]
    """Every player in the tournament, where key is the number of games they've played"""

    tossups: List[Tossup]
    categories: Set[Category]

    playerStatsByCategory: Dict[Player, Dict[Category, PlayerCatStat]]
    overallPlayerStats: Dict[Player, PlayerCatStat]

    def __init__(self) -> None:
        """Default initialization."""
        self.players = {}
        self.tossups = []
        self.categories = set()
        self.playerStatsByCategory = {}
        self.overallPlayerStats = {}

    def addQBJAndPacket(self, qbj: QBJ, packet: PacketJSON) -> None:
        """Imports a QBJ parsed json object with associated parsed packet.

        Args:
            qbj (QBJ): parsed QBJ file
            packet (PacketJSON): packet that is the one used for the QBJ
        """
        # teams/lineups are per-QBJ
        teams: List[Tuple[Team, List[Lineup]]] = []

        # add players
        for rawTeam in qbj["match_teams"]:
            teamTuple = (
                rawTeam["team"]["name"], # name
                [(lu["first_question"], [p["name"] for p in lu["players"]]) for lu in rawTeam["lineups"]], # lineups
            )
            # sort lineups by starting question number
            teamTuple[1].sort(key=lambda x: x[0])
            teams.append(teamTuple)

            for rawPlayer in rawTeam["match_players"]:
                if rawPlayer["player"]["name"] not in self.players:
                    self.players[rawPlayer["player"]["name"]] = 0
                if rawPlayer["tossups_heard"] > 0:
                    self.players[rawPlayer["player"]["name"]] += 1 # increment games played

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
            if "- " in category:
                category = category.split("- ")[1]
            if " -" in category:
                category = category.split(" -")[1]
            # slight hack because MS is annoying
            if category == "World Literature":
                category = "World/Other Literature"
            if category == "Ancient History":
                category = "Ancient/Other History"
            if category == "Geography/Current Events/Other" or category == "Current Events":
                category = "Geography/Current Events/Other Academic"

            self.categories.add(category)

            # udpate tossups heard
            # TODO: make this work for substitutions by tracking 'lineups' properly
            for team in teams:
                playersWhoHeardIt: List[Player] = team[1][0][1]
                # get lineup with largest first question index smaller than this tossup's question number
                for possibleLineup in team[1]:
                    firstQuestionIdx, players = possibleLineup
                    if firstQuestionIdx >= rawTossup["question_number"]:
                        playersWhoHeardIt = players

                for p in playersWhoHeardIt:
                    if p not in self.playerStatsByCategory:
                        self.playerStatsByCategory[p] = {}
                    if category not in self.playerStatsByCategory[p]:
                        self.playerStatsByCategory[p][category] = PlayerCatStat()
                    if p not in self.overallPlayerStats:
                        self.overallPlayerStats[p] = PlayerCatStat()

                    for toUpdate in [self.playerStatsByCategory[p][category], self.overallPlayerStats[p]]:
                        toUpdate.tossupsHeard += 1

            correctBuzz = None
            incorrectBuzz = None
            # iterate over buzzes and look for gets/powers/negs
            for rawBuzz in rawTossup["buzzes"]:
                player = rawBuzz["player"]["name"]
                if player not in self.players:
                    print(f"Warning: (should never happen) player '{player}' buzzed on tossup with answerline '{answer}' but isn't in the player list")
                    continue

                points = rawBuzz["result"]["value"]
                position = rawBuzz["buzz_position"]["word_index"]
                buzz = Buzz(position, player, "teams aren't real yet", points)

                if points > 0:
                    if correctBuzz is not None:
                        print(f"Warning: multiple correct buzzes on tossup with answerline '{answer}'")
                    correctBuzz = buzz
                else:
                    # TODO rework incorrect buzz tracking — OK to have >1 0s but not >1 Negs
                    # if incorrectBuzz is not None:
                    #     print(f"Warning: multiple negs on tossup with answerline '{answer}' (this neg: {player})")
                    incorrectBuzz = buzz

                # update player stats
                if player not in self.playerStatsByCategory:
                    self.playerStatsByCategory[player] = {}
                if category not in self.playerStatsByCategory[player]:
                    self.playerStatsByCategory[player][category] = PlayerCatStat()
                if player not in self.overallPlayerStats:
                    self.overallPlayerStats[player] = PlayerCatStat()

                for toUpdate in [self.playerStatsByCategory[player][category], self.overallPlayerStats[player]]:
                    toUpdate.points += points
                    if points == 15:
                        toUpdate.powers += 1
                    elif points == 10:
                        toUpdate.tens += 1
                    elif points == -5:
                        toUpdate.negs += 1
                    elif points != 0:
                        print(f"Warning: unknown point value {points} on tossup with answerline '{answer}'")

                    if points > 0:
                        toUpdate.buzzPositions.append(position)
            self.tossups.append(Tossup(text, answer, correctBuzz, incorrectBuzz, playersWhoHeardIt))

    def generateCombinedStats(self) -> None:
        """Adds stats entries to playerStatsByCategory for the following "categories":

            * "Science" which is the sum of all science categories (including osci)
            * "Literature" which is the sum of all literature categories
            * "History" which is the sum of all history categories
            * "Fine Arts" which is the sum of all fine arts categories
            * "RMPSS" which is the sum of religion, myth, social science, and philosophy
        """

        for player in self.playerStatsByCategory:
            for newCat, constituents in BIG_CATEGORIES:
                if newCat not in self.playerStatsByCategory[player]:
                    self.playerStatsByCategory[player][newCat] = PlayerCatStat()
                    self.categories.add(newCat)
                else:
                    print("Warning: category '{newCat}' already exists for player '{player}'; skipping")
                    continue

                for constituent in constituents:
                    if constituent in self.playerStatsByCategory[player]:
                        self.playerStatsByCategory[player][newCat] += self.playerStatsByCategory[player][constituent]

    def statsToHTML(self, name: str) -> str:
        """Generates an HTML page showing statistics for this tournament.

        Args:
            name (str): the name of the tournament, e.g. "ACF Summer 1926 @ U of Q"
        Returns:
            str: The HTML
        """
        # cat stats
        html = '<h1 id="bycat">Best players in each category</h1>'
        html += '(<a href="#byplayer">jump to best categories for each player</a>)<br /><br/>'
        html += '<br/>$$catstats-navigation$$<hr/>'
        catstatsLinks = []

        # this is a little hacky but it means the "bigger" cats are first
        # things with underscores represent the start of a new line
        toListFirst = ["Overall"] + [x[0] for x in BIG_CATEGORIES]
        for bigCat, constituents in BIG_CATEGORIES:
            toListFirst.append("_" + bigCat)
            toListFirst += constituents
        toListFirst.append("_Other")

        for category in toListFirst + list(self.categories - set(toListFirst)):
            if category[0] == "_":
                print(category)
                catstatsLinks.append(f'<br /><hr/><b><i>{category[1:]}</i></b>:<br/>')
                continue
            curHTML = ""
            curHTML += f'<h2 id="{toID(category)}">{category} '
            curHTML += '<small><small><small><a href="#bycat">&#x21A9;</a></small></small></small></h2>'
            curHTML += '<table data-sortable class="sortable-theme-bootstrap">'
            curHTML += f"""<thead><tr>
                <th>Player</th>
                <th>{category} points/20 TUs</th>
                <th>+15</th>
                <th>+10</th>
                <th>-5</th>
                <th>Average buzz position</th></thead>"""
            playerStats: List[Tuple[
                Player,
                str, # PPTUH
                int, # Powers
                int, # gets
                int, # Negs
                str, # avg buzz position
            ]] = []
            # hack
            for player in self.playerStatsByCategory:
                cat: Optional[PlayerCatStat] = None
                if category in self.playerStatsByCategory[player]:
                    cat = self.playerStatsByCategory[player][category]
                elif category == "Overall":
                    cat = self.overallPlayerStats[player]
                if cat is None:
                    continue

                pptuh = "0"
                if cat.tossupsHeard != 0:
                    pptuh = str(round((cat.points / cat.tossupsHeard)*20, 2))
                powers = cat.powers
                tens = cat.tens
                negs = cat.negs
                avgBuzzPosition = "n/a"
                if len(cat.buzzPositions) > 0:
                    avgBuzzPosition = str(round(sum(cat.buzzPositions) / len(cat.buzzPositions), 2))
                    playerStats.append((player, pptuh, powers, tens, negs, avgBuzzPosition))
            # sort by PPG initially
            playerStats.sort(key=lambda x: float(x[1]), reverse=True)
            if len(playerStats) == 0:
                continue

            for stat in playerStats:
                curHTML += f"""<tr>
                    <td>{stat[0]}</td>
                    <td>{stat[1]}</td>
                    <td>{stat[2]}</td>
                    <td>{stat[3]}</td>
                    <td>{stat[4]}</td>
                    <td>{stat[5]}</td>
                </tr>"""
            curHTML += "</table>"

            catstatsLinks.append(f'<a href="#{toID(category)}">{category}</a>')
            html += curHTML


        html += '<h1 id="byplayer">Best categories for each player</h1>'
        html += '(<a href="#bycat">jump to best players in each category</a>)<br/><br/>$$catstats-navigation2$$'
        catstatsLinks2 = []
        for player in self.players.keys():
            catstatsLinks2.append(f'<a href="#{toID(player)}">{player}</a>')
            html += f'<h2 id="{toID(player)}">{player} '
            html += '<small><small><small><a href="#byplayer">&#x21A9;</a></small></small></small></h2>'

            html += '<table data-sortable class="sortable-theme-bootstrap">'
            html += f"""<thead><tr>
                <th>Category</th>
                <th>points/20 TUs</th>
                <th>+15</th>
                <th>+10</th>
                <th>-5</th>
                <th>Average buzz position</th></thead>"""
            categoryStats: List[Tuple[
                Category,
                str, # PPTUH
                int, # Powers
                int, # gets
                int, # Negs
                str, # avg buzz position
            ]] = []

            # show "synthetic" cats first
            for category in ["Overall"] + list(self.categories):
                cat = None
                if category in self.playerStatsByCategory[player]:
                    cat = self.playerStatsByCategory[player][category]
                elif category == "Overall":
                    cat = self.overallPlayerStats[player]
                if cat is None:
                    continue

                ppg = "0"
                if cat.tossupsHeard != 0:
                    ppg = str(round((cat.points / cat.tossupsHeard)*20, 2))
                powers = cat.powers
                negs = cat.negs
                avgBuzzPosition = "n/a"
                if len(cat.buzzPositions) > 0:
                    avgBuzzPosition = str(round(sum(cat.buzzPositions) / len(cat.buzzPositions), 2))
                categoryStats.append((category, ppg, powers, cat.tens, negs, avgBuzzPosition))
            # sort by PPG initially
            categoryStats.sort(key=lambda x: float(x[1]), reverse=True)

            for stat in categoryStats:
                html += f"""<tr>
                    <td>{stat[0]}</td>
                    <td>{stat[1]}</td>
                    <td>{stat[2]}</td>
                    <td>{stat[3]}</td>
                    <td>{stat[4]}</td>
                    <td>{stat[5]}</td>
                </tr>"""
            html += "</table>"


        # directory with qbjtool.py, and thus template.html, in it
        qbjtoolPyDir = path.dirname(path.realpath(__file__))
        TEMPLATE = open(path.join(qbjtoolPyDir, "template.html")).read()
        return TEMPLATE \
            .replace("$$gen_date$$", datetime.today().strftime('%m/%d/%Y')) \
            .replace("$$tour_name$$", name) \
            .replace("$$html$$", html) \
            .replace("$$catstats-navigation$$", " | ".join(catstatsLinks)
                     .replace("/> | ", "/> ")
                     .replace("| <br", "<br")
                     ) \
            .replace("$$catstats-navigation2$$", " | ".join(catstatsLinks2))

    def buzzpointsToHTML(self, name: str, n: int) -> str:
        """Generates an HTML page showing the best n buzzes per player for this tournament.

        Args:
            name (str): the name of the tournament, e.g. "ACF Summer 1926 @ U of Q"
            n (int): the number of buzzes to show per player
        Returns:
            str: The HTML
        """
        html = f'<center><h1>Earliest {n} buzzes for each player</h1>'
        html += '<br/>$$navigation$$<hr/></center>'
        links = []

        tossupsByPlayer: Dict[Player, List[Tossup]] = {}
        for tossup in self.tossups:
            if tossup.correctBuzz is None:
                continue
            if tossup.correctBuzz.player not in tossupsByPlayer:
                tossupsByPlayer[tossup.correctBuzz.player] = []
            tossupsByPlayer[tossup.correctBuzz.player].append(tossup)

        def buzzPosition(tossup: Tossup) -> float:
            if tossup.correctBuzz is None:
                return -1000
            return tossup.correctBuzz.position / len(tossup.text.split())

        for player in tossupsByPlayer:
            links.append(f'<a href="#{toID(player)}">{player}</a>')
            html += f'<center><h2 id="{toID(player)}">{player}'
            html += ' <small><small><small><a href="#">&#x21A9;</a></small></small></small></h2></center>'

            html += '<ol>'
            bestTossups = sorted(tossupsByPlayer[player], key=buzzPosition)[:n]
            for tu in bestTossups:
                if tu.correctBuzz is None:
                    continue
                position = tu.correctBuzz.position
                tossupWords = tu.text.split()
                if position < len(tossupWords):
                    tossupWords[position] = f"<u><mark>{tossupWords[position]}</u></mark>"
                    # tossupWords[position] += f"<small><small><i>&#8592;buzzed for +{tu.correctBuzz.points}</i></small></small>"
                else:
                    print(f"Warning: buzz position {position} out of bounds for tossup '{tu.text}'")
                html += f"<li>[after {(buzzPosition(tu) * 100):2.0f}% of the tossup] {' '.join(tossupWords)}"
                html += f"<br />ANSWER: {tu.answer}<br /></li>"
            html += '</ol>'

        qbjtoolPyDir = path.dirname(path.realpath(__file__))
        TEMPLATE = open(path.join(qbjtoolPyDir, "buzzpts_template.html")).read()
        return TEMPLATE \
            .replace("$$gen_date$$", datetime.today().strftime('%m/%d/%Y')) \
            .replace("$$tour_name$$", name) \
            .replace("$$html$$", html) \
            .replace("$$navigation$$", " | ".join(links))



