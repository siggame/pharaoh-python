class Thief(object):
  def __init__(self, thief, pyramid):
    self.thief = thief
    self.owner = thief.owner
    self.x = thief.x
    self.y = thief.y
    self.id = thief.id
    self.thiefType = thief.thiefType
    self.maxMovement = thief.maxMovement
    self.path = []
    self.pyramid = pyramid
    self.valid = True

  # yield next coords a thief can move to on its path
  # coords are based on indexes in pyramids grid
  def nextMoves(self):
    times = self.maxMovement
    while(times and self.path):
      times -= 1
      yield self.path.pop(0)

  def advance(self):
    self.pyramid.advanceThief(self)

  def move(self, x, y):
    self.x = x
    self.y = y
    self.thief.move(x, y)