from twisted.trial.unittest import TestCase

from twisted.internet import defer, task, reactor
from twisted.python.filepath import FilePath
from twisted.python import log


import tempfile
import commands
import sys, os


grace_root = FilePath(__file__).parent().parent().parent()


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


    timeout = 5
    
    
    def setUp(self):
        self.old_env = os.environ.get('PYTHONPATH', None)
        if not self.old_env:
            os.environ['PYTHONPATH'] = ''
        os.environ['PYTHONPATH'] += ':' + grace_root.path


    def tearDown(self):
        if self.old_env is None:
            del os.environ['PYTHONPATH']
        else:
            os.environ['PYTHONPATH'] = self.old_env

    
    def kill(self, pid):
        import signal
        try:
            os.kill(int(pid), signal.SIGTERM)
        except Exception as e:
            log.msg('%s' % e)


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
        log.msg('fake_twistd: %s' % fake_twistd.getContent())
        fake_twistd.chmod(0777)
        runner._twistdBin = lambda: fake_twistd.path
        
        path = FilePath(self.mktemp())
        path.makedirs()
        
        d = runner.twistd(['foo', 'bar', 'baz'], env={'FOO': 'foo value'},
                      path=path.path)
        def check(result):
            out, err, code = result
            log.msg('out: %s' % out)
            log.msg('err: %s' % err)
            log.msg('code: %s' % code)
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

        # I'm getting AF_UNIX path too long errors using self.mktemp()
        base = FilePath(tempfile.mkdtemp())
        log.msg('tmpdir: %r' % base.path)
        root = base.child('root')
        src = base.child('src')
        dst = base.child('dst')
        
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
            self.assertEqual(kwargs['path'], root.path)
            self.assertEqual(kwargs['env'], None)
        return r.addCallback(check)


    def tailUntil(self, filename, text):
        """
        Tail a file until you see text
        """
        self.tail_d = defer.Deferred()
        def closefile(r, fh):
            fh.close()
            return r
        fh = open(filename, 'rb')
        self.tail_d.addCallback(closefile, fh)
        self.lc = task.LoopingCall(self._lookFor, fh, text)
        self.lc.start(0.1)
        return self.tail_d


    def _lookFor(self, fh, text):
        while True:
            line = fh.readline()
            if not line:
                break
            if text in line:
                self.lc.stop()
                self.tail_d.callback(text)
                log.msg('found: %r' % text)
                return
                

    @defer.inlineCallbacks
    def test_stop(self):
        """
        Stop will stop a running process.
        """
        runner = Runner()

        # I'm getting AF_UNIX path too long errors using self.mktemp()
        base = FilePath(tempfile.mkdtemp())
        log.msg('tmpdir: %r' % base.path)
        root = base.child('root')
        src = base.child('src')
        dst = base.child('dst')
        
        _ = yield runner.start(root.path, 'unix:'+src.path, 'unix:'+dst.path)
        
        # XXX this is a hack because runner.start does not wait for the server
        # to actually successfully start.  Once that's fixed, you can
        # remove this.
        _ = yield task.deferLater(reactor, 0.1, lambda:None)

        pidfile = root.child('grace.pid')
        pid = pidfile.getContent()
        self.addCleanup(self.kill, pid)
        _ = yield runner.stop(root.path)

        # tail the log until you see Server Shut Down
        # XXX stop should maybe do the same... so that it doesn't return until
        # the process has actually stopped.
        logfile = root.child('grace.log')
        self.assertTrue(logfile.exists())
        _ = yield self.tailUntil(logfile.path, 'Server Shut Down.')

        self.assertFalse(pidfile.exists(), "pidfile should be gone: %r" % pidfile.path)


    @defer.inlineCallbacks
    def test_ls(self):
        """
        Ls should work
        """
        runner = Runner()

        # I'm getting AF_UNIX path too long errors using self.mktemp()
        base = FilePath(tempfile.mkdtemp())
        log.msg('tmpdir: %r' % base.path)
        root = base.child('root')
        src = base.child('src')
        dst = base.child('dst')
        
        _ = yield runner.start(root.path, 'unix:'+src.path, 'unix:'+dst.path)
        
        # XXX this is a hack because runner.start does not wait for the server
        # to actually successfully start.  Once that's fixed, you can
        # remove this.
        _ = yield task.deferLater(reactor, 0.1, lambda:None)

        pidfile = root.child('grace.pid')
        pid = pidfile.getContent()
        self.addCleanup(self.kill, pid)
        r = yield runner.ls(root.path)
        self.assertEqual(r, [
            {
                'src': 'unix:'+src.path,
                'dst': 'unix:'+dst.path,
                'conns': 0,
                'active': True,
            }
        ])


    @defer.inlineCallbacks
    def test_switch(self):
        """
        Switch should work
        """
        runner = Runner()

        # I'm getting AF_UNIX path too long errors using self.mktemp()
        base = FilePath(tempfile.mkdtemp())
        log.msg('tmpdir: %r' % base.path)
        root = base.child('root')
        src = base.child('src')
        dst = base.child('dst')
        
        _ = yield runner.start(root.path, 'unix:'+src.path, 'unix:'+dst.path)
        
        # XXX this is a hack because runner.start does not wait for the server
        # to actually successfully start.  Once that's fixed, you can
        # remove this.
        _ = yield task.deferLater(reactor, 0.1, lambda:None)

        pidfile = root.child('grace.pid')
        pid = pidfile.getContent()
        self.addCleanup(self.kill, pid)
        r = yield runner.switch(root.path, 'unix:'+src.path, 'unix:/foo')
        r = yield runner.ls(root.path)
        self.assertEqual(r, [
            {
                'src': 'unix:'+src.path,
                'dst': 'unix:/foo',
                'conns': 0,
                'active': True,
            }
        ], "Should have switched")


