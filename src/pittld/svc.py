from threading import Thread


def group(svcs):
    for x in svcs:
        x.madden([y for y in threads if y != x])


class BaseService(Thread):

    def __init__(self):
        super().__init__()

        self._associates = []
        self._kill = False

    def start(self):
        try:
            super().start()
        except Exception as e:
            self.kill_associates()
            raise e

    def kill_associates(self):
        [x.kill() for x in self._associates]

    def kill(self):
        if self.is_alive():
            self._kill = True
            self.kill_associates()

    def MADden(self, threads):
        self._associates = threads

