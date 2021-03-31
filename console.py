import time
import curses
import structure
import logging


class Console(object):
    """docstring for Console."""

    def __init__(self):
        super(Console, self).__init__()
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
        self.update({}, {})

    def update(self, units, missions):
        localtime = time.asctime( time.localtime(time.time()) )

        self.screen.clear()
        self.screen.refresh()
        missions_items = missions.items()
        self.screen.addstr(0, 0, 'Missionchief v2 [{}] - Active cads: {}'.format(localtime, len(missions_items)))

        height = 2
        width = 25
        column = 1
        widthset = 0
        for unit_id, unit in units.items():
            try:
                self.screen.addstr(height, widthset, '[{}] {} '.format(unit.state, unit.name), curses.color_pair(structure.STATE_COLOURS[unit.state]))
            except curses.error as e:
                widthset = width * column
                column = column + 1
                height = 2
                pass
            height += 1

        self.screen.refresh()
