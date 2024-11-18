# very WIP

import json
import sys
import traceback
from parsing import QBJ, PacketJSON
from tournament import Tournament

if len(sys.argv) < 2:
    print("qbjtool: no input files", file=sys.stderr)
    print(f"Try running `{sys.argv[0]} <tournament name> round1.qbj round2.qbj ...`", file=sys.stderr)
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
                print(f"Warning: no packet found for {qbjPath} (checked {", ".join(packetPathsToTry)}); skipping this packet", file=sys.stderr)
    except Exception as e:
        print(f"Error loading {qbjPath}:", file=sys.stderr)
        traceback.print_exc()
        continue
print(f"=> Loaded {qbjsLoaded} QBJ files")

t.generateCombinedStats()
print(f"==> Generated stats for combined categories")
open("out.html", "w").write(t.statsToHTML(name))
print(t.players)