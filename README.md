Graceful swan takes flight.  Hunter eyes his prey.  KABLAM!  Hunter falls.  Swan holsters gun.  Server continues running.

``grace`` lets you restart your server without interrupting current users.  It's a runtime configurable, port forwarder.

[![Build Status](https://secure.travis-ci.org/iffy/grace.png)](http://travis-ci.org/iffy/grace)

## Installation ##

Install the dependencies:

    pip install Twisted
    pip install PyOpenSSL # if you want SSL support

Either clone repo:

    git clone https://github.com/iffy/grace.git grace.git
    cd grace.git

Or download a tar:

    wget https://github.com/iffy/grace/tarball/master
    tar xf master
    cd iffy-grace-*

Then install:

    python setup.py install


## Usage ##

Start forwarding TCP traffic from port 9000 to port 7500 on the local machine:

    grace start tcp:9000 tcp:host=127.0.0.1:port=7500


Switch traffic from port 7500 to port 7600 (without disconnecting anyone still connected to port 7500):

    grace switch tcp:9000 tcp:host=127.0.0.1:port=7600


List forwarding rules:

    grace ls

Wait for previous forwards to finish:

    grace wait

Stop forwarding:

    grace stop


## It's not just for HTTP ##

Because ``grace`` uses [Twisted's excellent endpoints](http://twistedmatrix.com/documents/current/api/twisted.internet.endpoints.serverFromString.html), you can forward just about any traffic to just about anywhere.  Here's SSL to TCP:

    grace start ssl:443:privateKey=key.pem:certKey=crt.pem tcp:host=127.0.0.1:port=7500

TCP to SSL:

    grace start tcp:9000 ssl:host=www.google.com:port=443:caCertsDir=/etc/ssl/certs

TCP to domain socket:

    grace start tcp:9000 unix:/var/foo/bar

Domain socket to TCP:

    grace start unix:/var/foo/bar tcp:host=127.0.0.1:port=7500


## Planned usage not yet supported ##

Upgrade ``grace`` to a new version and swap out the current ``grace`` process with a new one:

    grace restart

Specify where logs, pid and control socket go (XXX needs more explanation):

    grace -d /tmp/foo start tcp:9000 tcp:host=127.0.0.1:port=7500


## Running the tests ##

Use ``trial`` to run the tests:

    trial grace


