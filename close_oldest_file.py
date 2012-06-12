import sublime, sublime_plugin
import datetime
import os.path

class WindowData(object):
    def __init__(self, window):
        self.window = window
        self.views = {}
        self.stack = []
        self.candidate = None
        self.candidateTime = None
        self.addUnknownViews()

    def checkLastSeenCandidate(self):
        if not self.candidate in self.stack:
            return
        # There is no way to tell when the user released ctrl in a ctrl+tab sequence.
        # Promote a view as last seen only if it was activated for at least 1 second
        # to make sure we don't touch views that we just pass by.
        now = datetime.datetime.now()
        if self.candidate and now - self.candidateTime > datetime.timedelta(milliseconds = 1000):
            self.stack.remove(self.candidate)
            self.stack.append(self.candidate)
            self.candidate = self.candidateTime = None

    def addUnknownViews(self):
        for v in self.window.views():
            if v.id() not in self.views:
                self.views[v.id()] = v
                self.stack.append(v.id())

    def on_activated(self, view):
        if not view.id() in self.views:
            # on_new isn't so reliable, check each time we find an unknown view instead.
            self.addUnknownViews()

        self.checkLastSeenCandidate()
        self.candidate = view.id()
        self.candidateTime = datetime.datetime.now()

    def on_close(self, view):
        self.views.pop(view.id())
        self.stack.remove(view.id())
        if view.id() == self.candidate:
            self.candidate = self.candidateTime = None

    def closeOldest(self):
        self.checkLastSeenCandidate()
        # Search for a non-dirty view first.
        viewToClose = None
        for viewId in self.stack:
            view = self.views[viewId]
            if not view.is_dirty():
                viewToClose = view
                break
        # If all remaining views are dirty, pick the oldest one.
        if not viewToClose and self.stack:
            viewToClose = self.views[self.stack[0]]

        if viewToClose:
            viewDir,viewName = os.path.split(viewToClose.file_name())
            activeGroup = self.window.active_group()
            self.window.focus_view(viewToClose)
            self.window.run_command("close")
            sublime.status_message("Closed [%s] (in %s)" % (viewName, viewDir))
            # The last focused view will be restored automatically when closed, but not the group.
            self.window.focus_group(activeGroup)

class ViewTracker(sublime_plugin.EventListener):
    instance = None
    def __init__(self):
        self.windows = {}
        # An instance is created automatically by Sublime, keep it.
        ViewTracker.instance = self

    def getWindowData(self, window):
        if window.id() in self.windows:
            return self.windows[window.id()]
        else:
            data = WindowData(window)
            self.windows[window.id()] = data
            return data

    def on_activated(self, view):
        # Looks like view.window() is None here sometimes, probably a bug in Sublime.
        # Use active_window() which should always match anyway.
        data = self.getWindowData(sublime.active_window())
        data.on_activated(view)

    def on_close(self, view):
        data = self.getWindowData(sublime.active_window())
        data.on_close(view)

class CloseOldestFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        ViewTracker.instance.getWindowData(self.window).closeOldest()