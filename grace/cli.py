from twisted.internet import protocol, defer, reactor, utils
import commands


from grace.tac import setupDir



class Runner:

    
    def _twistdBin(self):
        """
        Get the path to the twistd executable.
        """
        # XXX what problems will this cause by blocking?
        return commands.getoutput('which twistd')


    def twistd(self, *args, **kwargs):
        twistd = self._twistdBin()
        return utils.getProcessOutputAndValue(twistd, *args, **kwargs)


    def start(self, basedir, src, dst):
        setupDir(basedir, (src, dst))
        return self.twistd(['--logfile=grace.log', '--pidfile=grace.pid',
                            '--python=grace.tac'], env=None, path=basedir)