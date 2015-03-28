EMPTY, SPAWN, WALL = xrange(3)


class Tile(object):
  def __init__(self, tile):
    self.tile = tile
    self.x = tile.x
    self.y = tile.y
    self.spawn = tile.type == SPAWN
    self.empty = tile.type == EMPTY
    self.wall = tile.type == WALL
    self.trap = None


