import sublime, sublime_plugin
import datetime

class ViewTracker(sublime_plugin.EventListener):
    instance = None
    def __init__(self):
        self.views = {}
        self.stack = []
        self.candidate = None
        self.candidateTime = None

        # An instance is create automatically by Sublime, keep it.
        ViewTracker.instance = self

    def checkCandidate(self):
        if not self.candidate in self.stack:
            return
        # There is no way to tell when the user released ctrl in a ctrl+tab sequence.
        # Promote a view only if it was activated for at least 1 second.
        now = datetime.datetime.now()
        if self.candidate and now - self.candidateTime > datetime.timedelta(milliseconds = 1000):
            self.stack.remove(self.candidate)
            self.stack.append(self.candidate)
            self.candidate = self.candidateTime = None

    def addUnknownViews(self):
        for w in sublime.windows():
            for v in w.views():
                if v.id() not in self.views:
                    self.views[v.id()] = v
                    self.stack.append(v.id())

    def on_activated(self, view):
        if not view.id() in self.views:
            # on_new isn't so reliable, check each time we find an unknown view instead.
            self.addUnknownViews()

        self.checkCandidate()
        self.candidate = view.id()
        self.candidateTime = datetime.datetime.now()

    def on_close(self, view):
        self.views.pop(view.id())
        self.stack.remove(view.id())
        if view.id() == self.candidate:
            self.candidate = self.candidateTime = None

    def closeOldest(self):
        self.checkCandidate()
        view = self.views[self.stack[0]]
        # FIXME: view.window() is None sometimes for some reason.
        sublime.active_window().focus_view(view)
        sublime.active_window().run_command("close")

class CloseOldestFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        ViewTracker.instance.closeOldest()