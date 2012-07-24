from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath

grace_root = FilePath(__file__).parent().parent()
tac_template = grace_root.child('grace.tac')

from grace.tac import getTac, setupDir


class getTacTest(TestCase):


    def test_nopipes(self):
        """
        You can get the tacfile without any extra Pipes.
        """
        s = getTac()
        self.assertEqual(s, tac_template.getContent())


    def test_onepipe(self):
        """
        You can add a pipe to the tac file
        """
        s = getTac(('src', 'dst'))
        expected = tac_template.getContent()
        expected += "\nplumber.addPipe('src', 'dst')\n"
        self.assertEqual(s, expected)



class setupDirTest(TestCase):


    def test_dne(self):
        """
        If the directory does not exist, it will create the directory and
        put a tac file in it.
        """
        tmp = FilePath(self.mktemp())
        setupDir(tmp.path, ('foo', 'bar'))
        self.assertTrue(tmp.exists(), "Should make the directory")
        tac = tmp.child('grace.tac')
        self.assertTrue(tac.exists(), "Should make the tac file")
        self.assertEqual(tac.getContent(), getTac(('foo', 'bar')),
                         "Should copy the tac template in")


    def test_exists(self):
        """
        If the directory and a file already exist, overwrite them
        """
        tmp = FilePath(self.mktemp())
        setupDir(tmp.path, ('ape', 'gorilla'))
        setupDir(tmp.path, ('foo', 'bar'))
        
        self.assertTrue(tmp.exists(), "Should make the directory")
        tac = tmp.child('grace.tac')
        self.assertTrue(tac.exists(), "Should make the tac file")
        self.assertEqual(tac.getContent(), getTac(('foo', 'bar')),
                         "Should copy the tac template in")