# very WIP

import json
import sys
from parsing import QBJ, PacketJSON
from tournament import Tournament

qbjPaths = sys.argv[1:]
if len(qbjPaths) == 0:
    print("qbjtool: no input files", file=sys.stderr)
    print(f"Try running `{sys.argv[0]} round1.qbj round2.qbj ...`", file=sys.stderr)
    sys.exit(1)

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
    except:
        print(f"Error loading {qbjPath}", file=sys.stderr)
        continue
print(f"=> Loaded {qbjsLoaded} QBJ files")

print(str(t.playerStatsByCategory).replace("'", '"'))