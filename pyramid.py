from thief import Thief

class Pyramid(object):

  def __init__(self, player, intruder, width, height):
    self.intruder = intruder
    self.player = player
    self.spawns = []
    self.width = width
    self.height = height
    self.x_adj = width * player.id
    self.tiles = [[None for col in xrange(width)] for row in xrange(height)]
    self.thieves = {}
    self.traps = {}
    self.sarcophagus = None
    self.thiefCount = [0 for i in range(5)]

  def __getitem__(self, i):
    return self.tiles[i]

  def placeTile(self, tile):
    if tile.spawn:
      self.spawns.append(tile)

    self.tiles[tile.x - self.x_adj][tile.y] = tile

  def itertiles(self):
    for row in self.tiles:
      for tile in row:
        yield tile

  # real tile locations provided
  def spawnThief(self, x, y, type):
    self.intruder.purchaseThief(x, y, type)

  def initThief(self, thief):
    x, y = thief.x - self.x_adj, thief.y
    thief = Thief(thief, self)
    self.thiefCount[thief.thiefType] += 1
    thief.valid = True
    if (x, y) not in self.thieves:
      self.thieves[(x,y)] = [thief]
    else:
      self.thieves[(x,y)].append(thief)

  def validifyThief(self, thief):
    for coords, thieves in self.thieves.iteritems():
      for t in thieves:
        if t.id == thief.id:
          x, y = thief.x - self.x_adj, thief.y
          if (x, y) != coords:
            return False
          t.valid = True
          t.thief = thief
          return True

    return False

  def removeThief(self, thief):
    for coords, thieves in self.thieves.iteritems():
      for i, t in enumerate(thieves):
        if t.id == thief.id:
          del self.thieves[coords][i]
          return

  # move a thief as far along its path as it can go
  def advanceThief(self, thief):
    coords = None
    for x, y in thief.nextMoves():
      thief.move(x + self.x_adj, y)
      coords = x, y

    #move thief
    self.removeThief(thief)
    if coords not in self.thieves:
      self.thieves[coords] = [thief]
    else:
      self.thieves[coords].append(thief)

  def iterthieves(self):
    for coords, thieves in self.thieves.iteritems():
      for t in thieves:
        yield coords, t

  def reset(self):
    for thieves in self.thieves.itervalues():
      for thief in thieves:
        thief.valid = False

  def clean(self):
    invalid = []
    for coords, thieves in self.thieves.iteritems():
      for i, thief in enumerate(thieves):
        if not thief.valid or not thief.thief.alive:
          self.thiefCount[thief.thiefType] -= 1
          invalid.append(i)
      while(invalid):
        del self.thieves[coords][invalid.pop()]
  
  # real tile locations provided
  def placeTrap(self, x, y, type):
    self.player.placeTrap(x, y, type)


  def initTrap(self, trap):
    self.traps[(trap.x - self.x_adj, trap.y)] = trap
    if trap.trapType == 0:
      self.sarcophagus = (trap.x - self.x_adj, trap.y)

  # for testing
  def display(self):
    for tiles in self.tiles:
      row = ""
      for tile in tiles:
        if tile.empty:
          row += " "
        elif tile.wall:
          row += "#"
        elif tile.spawn:
          row += "S"
      print(row)