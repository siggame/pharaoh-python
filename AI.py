#-*-python-*-
from BaseAI import BaseAI
from GameObject import *
from pyramid import Pyramid
from thief import Thief
from tile import Tile

BOMBER, DIGGER, NINJA, GUIDE, SLAVE = xrange(5)
SARCOPHAGUS, SNAKES, SWINGING, BOULDER, SPIDER, SAND, OIL, ARROW, WIRE, MERCURY, MUMMY, FAKE = xrange(12)

class AI(BaseAI):
  """The class implementing gameplay logic."""
  @staticmethod
  def username():
    return "Shell AI"

  @staticmethod
  def password():
    return "password"

  def neighbors(self, coords):
    offsets = (1, 0), (-1, 0), (0, 1), (0, -1)
    results = []
    for x, y in offsets:
      x, y = coords[0] + x, coords[1] + y
      if 0 > x or x >= self.width:
        continue

      if 0 > y or y >= self.mapHeight:
        continue

      if not self.enemy_pyramid[x][y].empty:
        continue

      yield x, y


  def pathfind(self, start, goal):
    frontier = [start]
    came_from = dict(start=None)

    while(frontier):
      current = frontier.pop(0)

      if current == goal:
        break

      for next in self.neighbors(current):
        if next not in came_from:
          frontier.append(next)
          came_from[next] = current

    path = self.buildPath(start, goal, came_from)
    return path


  def buildPath(self, start, goal, came_from):
    current = goal
    path = [current]

    while current != start:
      current = came_from[current]
      path.insert(0, current)

    path.pop(0)
    return path

  def reset(self):
    self.my_pyramid = Pyramid(self.me, self.enemy, self.width, self.mapHeight)
    self.enemy_pyramid = Pyramid(self.enemy, self.me, self.width, self.mapHeight)

    for tile in self.tiles:
      tile = Tile(tile)
      if self.playerID == 0:
        if tile.x < self.width:
          self.my_pyramid.placeTile(tile)
        else:
          self.enemy_pyramid.placeTile(tile)
      else:
        if tile.x < self.width:
          self.enemy_pyramid.placeTile(tile)
        else:
          self.my_pyramid.placeTile(tile)

  def loadTraps(self):
    self.my_pyramid.traps = {}
    self.enemy_pyramid.traps = {}
    for trap in self.traps:
      if trap.owner == self.playerID:
        self.my_pyramid.addTrap(trap)
      else:
        self.enemy_pyramid.addTrap(trap)

  def loadThieves(self):
    self.my_pyramid.reset()
    self.enemy_pyramid.reset()
    my_thieves = {}
    enemy_thieves = {}

    for thief in self.thiefs:
      if thief.owner == self.playerID:
        if not self.enemy_pyramid.validifyThief(thief):
          self.enemy_pyramid.initThief(thief)
          
      else:
        if not self.my_pyramid.validifyThief(thief):
          self.my_pyramid.initThief(thief)

    self.my_pyramid.clean()
    self.enemy_pyramid.clean()

  ##This function is called once, before your first turn
  def init(self):
    self.me = self.players[self.playerID]
    self.enemy = self.players[self.playerID^1]

    # sort by type for easy referring later
    self.thiefTypes.sort(key=lambda t: t.type)
    self.trapTypes.sort(key=lambda t: t.type)

    self.width = self.mapWidth/2
    self.turn = -1
              
  ##This function is called once, after your last turn
  def end(self):
    pass

  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
  def run(self):
    if self.roundTurnNumber == 1 or self.roundTurnNumber == 0:
      print("NEW ROUND")
      self.reset()
      self.my_pyramid.display()
      # trap placement
      return 1

    self.loadThieves()
    self.loadTraps()

    my_pyramid = self.my_pyramid
    enemy_pyramid = self.enemy_pyramid
    slaveCount = self.enemy_pyramid.thiefCount[SLAVE]

    for spawn in enemy_pyramid.spawns:
      if slaveCount >= self.thiefTypes[SLAVE].maxInstances:
        break

      enemy_pyramid.spawnThief(spawn.x, spawn.y, SLAVE)
      slaveCount += 1

    thieves = []
    for coords, thief in enemy_pyramid.iterthieves():
      if not thief.path:
        thief.path = self.pathfind(coords, enemy_pyramid.sarcophagus)
      thieves.append(thief)

    for thief in thieves:
      thief.advance()
      
    return 1

  def __init__(self, conn):
    BaseAI.__init__(self, conn)