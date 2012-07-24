from twisted.application import service, strports
from twisted.python.filepath import FilePath

application = service.Application('grace')

d = FilePath(__file__).parent()

#------------------------------------------------------------------------------
# control
#------------------------------------------------------------------------------
from grace.plumbing import Plumber
plumber = Plumber()

from grace.control import ServerFactory
control_factory = ServerFactory(plumber)
control_ep = 'unix:'+d.child('grace.socket').path
control_service = strports.service(control_ep, control_factory)
control_service.setServiceParent(application)

#------------------------------------------------------------------------------
# Pipes
#------------------------------------------------------------------------------
# plumber.addPipe(src, dst)