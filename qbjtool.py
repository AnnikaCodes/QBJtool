# very WIP

import json
import sys
import traceback
from parsing import QBJ, PacketJSON
from tournament import Tournament

if len(sys.argv) < 2:
    print("Error: no input files", file=sys.stderr)
    print(f"Try running `{sys.argv[0]} <tournament name> round1.qbj round2.qbj ...`", file=sys.stderr)
    print("You should run QBJtool in the directory which contains your packet .json files.", file=sys.stderr)
    sys.exit(1)
name = sys.argv[1]
qbjPaths = sys.argv[2:]

t = Tournament()

# do ""smart""" packet location
qbjsLoaded = 0
for qbjPath in qbjPaths:
    try:
        with open(qbjPath) as f:
            qbj: QBJ = json.load(f)
            packetname = qbj["packets"]
            packetPathsToTry = [f"{packetname}.json"]

            added = False
            for path in packetPathsToTry:
                try:
                    with open(path) as f:
                        packet: PacketJSON = json.load(f)
                        t.addQBJAndPacket(qbj, packet)
                        # print(f"Added QBJ {qbjPath} with packet {path}")
                        added = True
                        qbjsLoaded += 1
                        break
                except FileNotFoundError:
                    continue
            if not added:
                print(f"Warning: no packet found for {qbjPath} (checked {', '.join(packetPathsToTry)}); skipping this packet", file=sys.stderr)
    except Exception as e:
        print(f"Error: could not load {qbjPath}. Here's the Python error trace:\n", file=sys.stderr)
        traceback.print_exc()
        continue
print(f"=> Loaded {qbjsLoaded} QBJ files")
print(f"Alphabetical list of categories:\n\t* {'\n\t* '.join(sorted(list(t.categories)))}")
byLastWord = '\n\t* '.join(sorted(list(t.categories), key=lambda x: x.split()[-1]))
print(f"Alphabetical by last word list of categories:\n\t* {byLastWord}")

t.generateCombinedStats()
print(f"==> Generated stats for combined categories")
open(f"{name} (cat stats).html", "w").write(t.statsToHTML(name))
print(f"===> Wrote stats to {name}.html")

open(f"{name} (buzzes).html", "w").write(t.buzzpointsToHTML(name, 5))
print(f"===> Wrote best buzzes to {name} (buzzes).html")
