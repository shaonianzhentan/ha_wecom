
class EventEmit:
    def __init__(self):
        self.handlers = {}

    def on(self, name, fn):
        if name not in self.handlers:
            self.handlers[name] = []
        self.handlers[name].append(fn)

    def emit(self, name, data):
        for fn in self.handlers.get(name, []):
            fn(data)

    def off(self, name, fn):
        handlers = self.handlers.get(name)
        if not handlers:
            return
        if fn is None:
            handlers.clear()
        else:
            try:
                index = handlers.index(fn)
                if index >= 0:
                    del handlers[index]
            except ValueError:
                pass