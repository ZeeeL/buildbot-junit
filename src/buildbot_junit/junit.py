import os
import stat
import xunitparser
from buildbot.status.results import SUCCESS, WARNINGS, FAILURE
from buildbot.steps.shell import ShellCommand
from buildbot.process import buildstep


class JUnitShellCommand(ShellCommand):

    """A ShellCommand that sniffs junit output.
    """
    def __init__(self, report_dir, *args, **kwargs):
        ShellCommand.__init__(self, *args, **kwargs)
        self.report_dir = report_dir

    def commandComplete(self, cmd):
        cmd = buildstep.RemoteCommand('stat', {'file': os.path.join(self.getWorkdir(), self.report_dir)})

        d = self.runCommand(cmd)
        d.addCallback(lambda res: self.findReportsDir(cmd))
        d.addErrback(self.failed)
        return d

    def findReportsDir(self, cmd):
        if cmd.didFail():
            self.step_status.setText(["Reports not found."])
            self.finished(WARNINGS)
            return

        s = cmd.updates["stat"][-1]
        if not stat.S_ISDIR(s[stat.ST_MODE]):
            self.step_status.setText(["This not a directory"])
            self.finished(WARNINGS)
            return

        cmd = buildstep.RemoteCommand('glob', {'path': os.path.join(self.getWorkdir(), self.report_dir, '*.xml')})

        d = self.runCommand(cmd)
        d.addCallback(lambda res: self.findReportsFiles(cmd))
        d.addErrback(self.failed)
        return d

    def findReportsFiles(self, cmd):
        if cmd.didFail():
            self.step_status.setText(["Find report files failed."])
            self.finished(WARNINGS)
            return
        files = cmd.updates["files"][-1]
        if len(files) == 0:
            self.step_status.setText(["No junit report files found"])
            self.finished(WARNINGS)
            return

        self.parseReportFiles(files)

    def parseReportFiles(self, files):
        self.failures = []
        self.errors = []
        self.skips = []
        self.total = 0
        for report_file in files:
            with open(report_file) as report:
                ts, tr = xunitparser.parse(report)
                self.failures.extend(tr.failures)
                self.errors.extend(tr.errors)
                self.skips.extend(tr.failures)
                self.total += tr.testsRun

        failures_count = len(self.failures)
        errors_count = len(self.errors)
        skips_count = len(self.skips)
        total = self.total

        count = failures_count + errors_count

        text = [self.name]
        text2 = ""

        if not count:
            results = SUCCESS
            if total:
                text += ["%d %s" %
                         (total,
                          total == 1 and "test" or "tests"),
                         "passed"]
            else:
                text += ["no tests", "run"]
        else:
            results = FAILURE
            text.append("Total %d test(s)" % total)
            if failures_count:
                text.append("%d %s" %
                            (failures_count,
                             failures_count == 1 and "failure" or "failures"))
            if errors_count:
                text.append("%d %s" %
                            (errors_count,
                             errors_count == 1 and "error" or "errors"))
            text2 = "%d %s" % (count, (count == 1 and 'test' or 'tests'))

        if skips_count:
            text.append("%d %s" % (skips_count,
                                   skips_count == 1 and "skip" or "skips"))

        self.results = results
        self.text = text
        self.text2 = [text2]

    def evaluateCommand(self, cmd):
        if cmd.didFail():
            return FAILURE
        return self.results

    def createSummary(self, loog):
        problems = ""
        for test, err in self.errors + self.failures:
            problems += "%s\n%s" % (test.id(), err)
        if problems:
            self.addCompleteLog("problems", problems)

    def getText(self, cmd, results):
        return self.text

    def getText2(self, cmd, results):
        return self.text2
