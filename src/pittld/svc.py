from threading import Thread

from pittld import logger


def associate(svcs):
    [x.associate([y for y in svcs if y != x])
     for x in svcs]


class BaseService(Thread):

    def __init__(self):
        super().__init__()

        self._associates = []
        self._kill = False

    def start(self):
        try:
            super().start()
        except Exception as e:
            self.kill()
            raise e

    def kill_associates(self):
        [x.kill() for x in self._associates]

    def kill(self):
        if self.is_alive():

            self._kill = True
            self.kill_associates()

    def associate(self, threads):
        self._associates = threads

