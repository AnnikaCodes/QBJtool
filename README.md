# QBJtool
QBJtool is a Python program which produces statistics about [Quiz Bowl](https://en.wikipedia.org/wiki/Quiz_bowl) games from `.qbj` files (which is a common format for buzz information at various collegiate Quiz Bowl tournaments) and packet `.json` files.

Right now, it only creates "cat stats": for each category, a list of which players scored the best in that category (as measured by points from tossups in that category per 20 tossups heard in that category); and for each player, a list of which categories they stored best in.
However, it should be pretty easy to add more functionality; buzzpoints are already read from the QBJ files, and there is typing for looking at bonuses.

## Usage
You should run QBJtool from the directory which contains your packet `.json` files (and they should have the names they are given in the QBJ files). Then you can run QBJtool like this: ```bash
python3 qbjtool.py <name of tournament> [list of QBJ files]
```
For example, ```bash
python3 qbjtool.py 'ACF Winter 2024 @ U of Somewhere' *.qbj
```