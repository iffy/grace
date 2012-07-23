from twisted.trial.unittest import TestCase
from twisted.application import service


from grace.plumbing import Plumber
from grace.pipe import Pipe



class PlumberTest(TestCase):

    timeout = 1


    def test_defaults(self):
        """
        A Plumber should have these defaults
        """
        p = Plumber()
        self.assertEqual(p.pipeFactory, Pipe)
        self.assertTrue(isinstance(p.pipe_services, service.MultiService))


    def test_addPipe(self):
        """
        Adding a pipe should create a new service using the pipeFactory and
        add the service to the list of services.
        """
        listen = 'unix:'+self.mktemp()
        connect = 'unix:path='+self.mktemp()
        
        p = Plumber()
        s = p.addPipe(listen, connect)
        services = list(p.pipe_services)
        self.assertEqual(len(services), 1, "Should have added a service")
        self.assertEqual(s, services[0], "Should have returned the service")
        self.assertTrue(isinstance(s.factory, Pipe))
        self.assertEqual(s.factory.dst, connect, "Should have set the "
                         "destination on the Pipe")


    def test_rmPipe(self):
        """
        You can remove pipes by endpoint name
        """
        listen = 'unix:'+self.mktemp()
        connect = 'unix:path='+self.mktemp()
        
        p = Plumber()
        s = p.addPipe(listen, connect)
        d = p.rmPipe(listen)
        
        def check(result):
            self.assertEqual(list(p.pipe_services), [])
            self.assertEqual(s.parent, None)        
        return d.addCallback(check)


    def test_getPipe(self):
        """
        You can get the Pipe itself using the src endpoint as a key.
        """
        listen = 'unix:'+self.mktemp()
        connect = 'unix:path='+self.mktemp()
        
        p = Plumber()
        p.addPipe(listen, connect)
        
        pipe = p.getPipe(listen)
        self.assertTrue(isinstance(pipe, Pipe))
        self.assertEqual(pipe, list(p.pipe_services)[0].factory)


    def test_pipeCommand(self):
        """
        You can execute things on the Pipe with a key
        """
        listen = 'unix:'+self.mktemp()
        connect = 'unix:path='+self.mktemp()
        
        p = Plumber()
        p.addPipe(listen, connect)
        pipe = p.getPipe(listen)
        
        called = []
        def fake(*a, **kw):
            called.append((a, kw))
            return 'result'
        pipe.foo = fake
        
        r = p.pipeCommand(listen, 'foo', 'arg1', 'arg2', kw1='foo', kw2='bar')
        self.assertEqual(r, 'result', "Should return whatever the Pipe's "
                         "method returned")
        self.assertEqual(called, [
            (('arg1', 'arg2'), {'kw1':'foo', 'kw2':'bar'}),
        ], "Should have passed all the appropriate args through")



