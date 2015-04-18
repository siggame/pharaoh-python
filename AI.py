#-*-python-*-
from BaseAI import BaseAI
from GameObject import *
import random
import copy
import collections
from sets import Set

class Point:
  x, y = None, None
  def __init__(self, x, y):
    self.x = x
    self.y = y

class AI(BaseAI):
  """The class implementing gameplay logic."""
  @staticmethod
  def username():
    return "Shell AI"

  @staticmethod
  def password():
    return "password"

  ##This function is called once, before your first turn
  def init(self):
    #find which player I am
    self.me = self.players[self.playerID]

  ##This function is called once, after your last turn
  def end(self):
    pass

  ##This function is called each time it is your turn
  ##Return true to end your turn, return false to ask the server for updated information
  def run(self):
    #lists for sarcophagi
    mySarcophagi = []
    enemySarcophagi = []
    #if it's tiem to place traps...
    if self.roundTurnNumber == 0 or self.roundTurnNumber == 1:
      #find my sarcophagi
      for trap in self.traps:
        if trap.owner == self.playerID and trap.trapType == TrapType.SARCOPHAGUS:
          mySarcophagi.append(trap)
      #find the first open tiles and place the sarcophagi there
      sarcophagusCount = len(mySarcophagi)
      for tile in self.tiles:
        #if the tile is on my side and is empty
        if self.onMySide(tile.x) and tile.type == Tile.EMPTY:
          #move my sarcophagus to that location
          self.me.placeTrap(tile.x, tile.y, TrapType.SARCOPHAGUS)
          sarcophagusCount -= 1
          if sarcophagusCount == 0:
            break
      #make sure there aren't too many traps spawned
      trapCount = [0]*len(self.trapTypes)
      #continue spawning traps until there isn't money to spend
      for tile in self.tiles:
        #if the tile is on my side
        if self.onMySide(tile.x):
          #make sure there isn't a trap on that tile
            if self.getTrap(tile.x, tile.y) is None:
              #select a random trap type (make sure it isn't a sarcophagus)
              trapType = random.randint(1, len(self.trapTypes) - 1)
              #make sure another can be spawned
              if trapCount[trapType] < self.trapTypes[trapType].maxInstances:
                #if there are enough scarabs
                if self.me.scarabs >= self.trapTypes[trapType].cost:
                  #check if the tile is the right type
                  if self.trapTypes[trapType].canPlaceOnWalls and tile.type == Tile.WALL:
                    self.me.placeTrap(tile.x, tile.y, trapType)
                    trapCount[trapType] += 1
                  elif not self.trapTypes[trapType].canPlaceOnWalls and tile.type == Tile.EMPTY:
                    self.me.placeTrap(tile.x, tile.y, trapType)
                    trapCount[trapType] += 1
    #otherwise it's time to move and purchase
    else:
      #find my sarcophagi and the enemy scarcophagi
      for trap in self.traps:
        if trap.trapType == TrapType.SARCOPHAGUS:
          if trap.owner != self.playerID:
            enemySarcophagi.append(trap)
          else:
            mySarcophagi.append(trap)
      #find my spawn tiles
      spawnTiles = self.getMySpawns()
      #select a random thief type
      thiefNo = random.randint(0, len(self.thiefTypes) - 1)
      #if you can afford the thief
      if self.me.scarabs >= self.thiefTypes[thiefNo].cost:
        #make sure another can be spawned
        max = self.thiefTypes[thiefNo].maxInstances
        count = 0
        for thief in self.getMyThieves():
          if thief.thiefType == thiefNo:
            count += 1
        #only spawn if there aren't too many
        if count < max:
          #select a random spawn location
          spawnLoc = random.randint(0, len(spawnTiles) - 1)
          #spawn a thief there
          spawnTile = spawnTiles[spawnLoc]
          self.me.purchaseThief(spawnTile.x, spawnTile.y, thiefNo)
      #move my thieves
      for thief in self.getMyThieves():
        #if the theif is alive and not frozen
        if thief.alive and thief.frozenTurnsLeft == 0:
          xChange = [-1, 1, 0, 0]
          yChange = [0, 0, -1, 1]
          #try to dig or use a bomb before moving
          if thief.thiefType == ThiefType.DIGGER and thief.specialsLeft > 0:
            for i in range(4):
              #if there is a wall adjacent and an empty space on the other side
              checkX = thief.x + xChange[i]
              checkY = thief.y + yChange[i]
              wallTile = self.getTile(checkX, checkY)
              emptyTile = self.getTile(checkX + xChange[i], checkY + yChange[i])
              #must be on the map, and not trying to dig to the other side
              if wallTile is not None and emptyTile is not None and not self.onMySide(checkX + xChange[i]):
                #if there is a wall with an empty tile on the other side
                if wallTile.type == Tile.WALL and emptyTile.type == Tile.EMPTY:
                  #dig through the wall
                  thief.useSpecial(checkX, checkY)
                  #break out of the loop
                  break
          elif thief.thiefType == ThiefType.BOMBER and thief.specialsLeft > 0:
            for i in range(4):
              #the place to check for things to blow up
              checkX = thief.x + xChange[i]
              checkY = thief.y + yChange[i]
              #make sure that the spot isn't on the other side
              if not self.onMySide(checkX):
                #if there is a wall tile there, blow it up
                checkTile = self.getTile(checkX, checkY)
                if checkTile is not None and checkTile.type == Tile.WALL:
                  #blow up the wall
                  thief.useSpecial(checkX, checkY)
                  #break out of the loop
                  break
                #otherwise check if there is a trap there
                checkTrap = self.getTrap(checkX, checkY)
                #don't want to blow up the sarcophagus!
                if checkTrap is not None and checkTrap.trapType != TrapType.SARCOPHAGUS:
                  #blow up the trap
                  thief.useSpecial(checkX, checkY)
                  #break out of the loop
                  break
          #if the thief has any movement left
          if thief.movementLeft > 0:
            #find a path from the thief's location to the enemy sarcophagus
            endX = enemySarcophagi[0].x
            endY = enemySarcophagi[0].y
            path = self.pathFind((thief.x, thief.y), (endX, endY))
            #if a path exists then move forward on the path
            if path:
              new = path.pop()
              thief.move(new[0], new[1])
    #do things with traps now
    for trap in self.getMyTraps():
      xChange = [-1, 1, 0, 0]
      yChange = [0, 0, -1, 1]
      #make sure trap can be used
      if trap.active:
        #if trap is a boulder
        if trap.trapType == TrapType.BOULDER:
          #if there is an enemy thief adjacent
          for i in range(4):
            enemyThief = self.getThief(trap.x + xChange[i], trap.y + yChange[i])
            #roll over the thief
            if enemyThief is not None:
              trap.act(xChange[i], yChange[i])
              break
        elif trap.trapType == TrapType.MUMMY:
          #move around randomly if a mummy
          dir = random.randint(0, 3)
          checkX = trap.x + xChange[dir]
          checkY = trap.y + yChange[dir]
          checkTile = self.getTile(checkX, checkY)
          checkTrap = self.getTrap(checkX, checkY)
          #if the tile is empty, and there isn't a sarcophagus there
          if checkTrap is None or checkTrap.trapType != TrapType.SARCOPHAGUS:
            if checkTile is not None and checkTile.type == Tile.EMPTY:
              #move on that tile
              trap.act(checkX, checkY)

    return 1

  ##returns true if the position is on your side of the field
  def onMySide(self, x):
    if self.playerID == 0:
      return (x < self.mapWidth/2)
    else:
      return (x >= self.mapWidth/2)

  ##returns the first thief encountered on x, y or None if no thief
  def getThief(self, x, y):
    if x < 0 or x >= self.mapWidth or y < 0 or y >= self.mapHeight:
      return None
    for thief in self.thiefs:
      if thief.x == x and thief.y == y:
        return thief
    return None

  ##returns the tile at the given x,y position or None otherwise
  def getTile(self, x, y):
    if x < 0 or x >= self.mapWidth or y < 0 or y >= self.mapHeight:
      return None
    return self.tiles[y + x * self.mapHeight]

  ##returns the trap at the given x,y position or None otherwise
  def getTrap(self, x, y):
    if x < 0 or x >= self.mapWidth or y < 0 or y >= self.mapHeight:
      return None
    for trap in self.traps:
      if trap.x == x and trap.y == y:
        return trap
    return None

  ##returns a list of all of your traps
  def getMyTraps(self):
    toReturn = []
    for trap in self.traps:
      if trap.owner == self.playerID:
        toReturn.append(trap)
    return toReturn

  ##returns a list of all of you enemy's traps
  def getEnemyTraps(self):
    toReturn = []
    for trap in self.traps:
      if trap.owner != self.playerID:
        toReturn.append(trap)
    return toReturn

  ##returns a list of all of your thieves
  def getMyThieves(self):
    toReturn = []
    for thief in self.thiefs:
      if thief.owner == self.playerID:
        toReturn.append(thief)
    return toReturn

  ##returns a list of all of your enemy thieves
  def getEnemyThieves(self):
    toReturn = []
    for thief in self.thiefs:
      if thief.owner != self.playerID:
        toReturn.append(thief)
    return toReturn

  ##returns a list of all of your spawn tiles
  def getMySpawns(self):
    toReturn = []
    for tile in self.tiles:
      if not self.onMySide(tile.x) and tile.type == Tile.SPAWN:
        toReturn.append(tile)
    return toReturn

  ##returns a path from start to end, or nothing if no path is found.
  def findPath(self, startPoint, endPoint):
    toReturn = collections.deque()
    #the set of open tiles to look at
    openSet = collections.deque()
    #points back to parent tile
    parent = dict()
    #push back the starting tile
    openSet.append(self.getTile(startPoint.x, startPoint.y))
    #the start tile has no parent
    parent[self.getTile(startPoint.x, startPoint.y)] = None
    #the end tile
    endTile = self.getTile(endPoint.x, endPoint.y)
    #as long as the end tile has no parent
    while endTile not in parent:
      #if there are no tiles in the openSet then there is no path
      if len(openSet) == 0:
        return toReturn
      #check tiles from the front and remove it
      curTile = openSet.pop()
      xChange = [0, 0, -1, 1]
      yChange = [-1, 1, 0, 0]
      #look in all directions
      for i in range(4):
        loc = Point(curTile.x + xChange[i], curTile.y + yChange[i])
        toAdd = self.getTile(loc.x, loc.y)
        #if there's a tile there
        if toAdd is not None:
          #if it's an open tile and it doesn't have a parent
          if toAdd.type == Tile.EMPTY and toAdd not in parent:
            #add the tile to the open set; and mark its parent as the current tile
            openSet.append(toAdd)
            parent[toAdd] = curTile
    #find the path back
    tile = endTile
    while parent[tile] is not None:
      toReturn.appendleft(Point(tile.x, tile.y))
      tile = parent[tile]
    return toReturn
  
  def neighbors(self, tile):
      n = []
      if tile[1] - 1 >= 0 and self.path(tile[0], tile[1] - 1, tile[0], tile[1]):
        n.append((tile[0], tile[1] - 1))
      if tile[1] + 1 < self.mapHeight and self.path(tile[0], tile[1] + 1, tile[0], tile[1]):
        n.append((tile[0], tile[1] + 1))
      if tile[0] - 1 >= 0 and self.path(tile[0] - 1, tile[1], tile[0], tile[1]):
        n.append((tile[0] - 1, tile[1]))
      if tile[0] + 1 < self.mapWidth and self.path(tile[0] + 1, tile[1], tile[0], tile[1]):
        n.append((tile[0] + 1, tile[1]))
      return n
    
  def pathFind(self, start, end):
      Open = collections.deque()
      Open.append(start)
      Closed = Set(start)
      parentMap = dict()
      path = []
      while Open:
        current = Open.pop()
        if current == end:
          while current != start:
            path.append(current)
            current = parentMap[current]
          return path
        for neighbor in self.neighbors(current): 
          if neighbor not in Closed:
            parentMap[neighbor] = current
            Closed.add((neighbor))
            Open.appendleft((neighbor))
      pass

  def setEnds(self):
    ends = collections.deque()
    for trap in self.traps:
      if trap.owner != self.playerID and trap.trapType == TrapType.SARCOPHAGUS:
        ends.appendleft((trap.x, trap.y))
    return ends

  def path(self, x, y, startx, starty):
      if x >= 0 and x < self.mapWidth and y >= 0 and y < self.mapHeight:
        if ((self.onMySide(startx)) == (self.onMySide(x))):
          return self.tiles[x * self.mapHeight + y].type != Tile.WALL
  
  me = None


  def __init__(self, conn):
    BaseAI.__init__(self, conn)
