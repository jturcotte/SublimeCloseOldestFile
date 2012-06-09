import sublime, sublime_plugin

class ViewTracker(sublime_plugin.EventListener):
    instance = None
    def __init__(self):
        self.views = {}
        self.stack = []
        for w in sublime.windows():
            for v in w.views():
                self.views[v.id()] = v
                self.stack.append(v.id())

        # Close the last of unknown files first.
        self.stack.reverse()
        # An instance is create automatically by Sublime, keep it.
        ViewTracker.instance = self

    def on_activated(self, view):
        if not view.id() in self.stack:
            return
        self.stack.remove(view.id())
        self.stack.append(view.id())

    def on_close(self, view):
        self.views.pop(view.id())
        self.stack.remove(view.id())

    def on_new(self, view):
        self.views[view.id()] = view
        self.stack.append(view.id())

    def closeOldest(self):
        view = self.views[self.stack[0]]
        # FIXME: view.window() is None sometimes for some reason.
        sublime.active_window().focus_view(view)
        sublime.active_window().run_command("close")

class CloseOldestFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        ViewTracker.instance.closeOldest()