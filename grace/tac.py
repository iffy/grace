from twisted.python.filepath import FilePath

grace_root = FilePath(__file__).parent()
tac_template = grace_root.child('grace.tac')


def getTac(pipedef=None):
    """
    Get the content of a tac file.
    
    @param pipedef: (optional) a tuple of strings that will be expanded and
        passed to L{grace.plumbing.Plumber.addPipe} in the tac file.
        
    @return: A string suitable for use as the contents of a tac file.
    """
    template = tac_template.getContent()
    if pipedef:
        template += '\nplumber.addPipe(%r, %r)\n' % pipedef
    return template



def setupDir(dirname, pipedef):
    """
    Create a grace directory.
    
    @param dirname: XXX
    @param pipedef: XXX
    """
    fp = FilePath(dirname)
    fp.makedirs()
    fp.child('grace.tac').setContent(getTac(pipedef))