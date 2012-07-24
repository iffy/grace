from twisted.trial.unittest import TestCase

from twisted.internet import defer
from twisted.python.filepath import FilePath

import commands
import sys, os


from grace.cli import Runner
from grace.tac import getTac



class FakeRunner(Runner):


    def __init__(self, result=None):
        self.called = []
        self._result = result or ('', '', 0)


    def twistd(self, *a, **kw):
        self.called.append((a, kw))
        return defer.succeed(self._result)



class RunnerTest(TestCase):


    timeout = 3


    def test_twistd(self):
        """
        Should run twistd with the given arguments
        """
        runner = Runner()
        fake_twistd = FilePath(self.mktemp())
        fake_twistd.setContent('#!%s\n'
                                'import sys, os\n'
                                'print " ".join(sys.argv[1:])\n'
                                'print os.environ["FOO"]\n'
                                'print os.path.abspath(os.curdir)\n'
                                'sys.stdout.flush()\n'
                                'sys.stderr.write("error\\n")\n'
                                'print "stdout"\n'
                                'sys.exit(4)\n' % sys.executable)
        fake_twistd.chmod(0777)
        runner._twistdBin = lambda: fake_twistd.path
        
        path = FilePath(self.mktemp())
        path.makedirs()
        
        d = runner.twistd(['foo', 'bar', 'baz'], env={'FOO': 'foo value'},
                      path=path.path)
        def check(result):
            out, err, code = result
            self.assertEqual(code, 4)
            self.assertEqual(out, 
                'foo bar baz\n'
                'foo value\n'
                '%s\n'
                'stdout\n' % path.path)
            self.assertEqual(err, 'error\n')
        return d.addCallback(check)


    def test__twistdBin(self):
        """
        Should know what twistd to use.
        """
        runner = Runner()
        path = commands.getoutput('which twistd')
        self.assertEqual(runner._twistdBin(), path)


    def test_start(self):
        """
        Start will create a directory and call twistd for the created tac file
        """
        runner = FakeRunner()

        root = FilePath(self.mktemp())        
        src = FilePath(self.mktemp())
        dst = FilePath(self.mktemp())
        
        r = runner.start(root.path, 'unix:'+src.path, 'unix:'+dst.path)
        def check(response):
            self.assertTrue(root.exists(), "Should have made the root dir")
            tac = root.child('grace.tac')
            self.assertTrue(tac.exists(), "Should have made grace.tac")
            self.assertEqual(tac.getContent(),
                getTac(('unix:'+src.path, 'unix:'+dst.path)),
                "Should have made the tac file using getTac")
            self.assertEqual(len(runner.called), 1, "Should have called twistd")
            args, kwargs = runner.called[0]
            self.assertEqual(args, (
                ['--logfile=grace.log',
                 '--pidfile=grace.pid',
                 '--python=grace.tac'],
            ))
            self.assertEqual(kwargs, {
                'path': root.path,
                'env': None,
            })
        return r.addCallback(check)


