from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath

grace_root = FilePath(__file__).parent().parent()
tac_template = grace_root.child('grace.tac')

from grace.tac import getTac


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