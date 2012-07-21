Graceful swan takes flight.  Hunter eyes his prey.  KABLAM!  Hunter falls.  Swan holsters gun.  Server continues running.

``grace`` lets you restart your server without interrupting current users.  It's a runtime configurable, port forwarder.


## Installation ##

Install the dependencies:

    pip install Twisted

Then clone this or XXX download a file and:

    python setup.py install


## Usage ##

XXX no command line stuff is supported yet.  Well, except a meaningless message.


## Planned usage not yet supported ##

Start forwarding TCP traffic from port 9000 to port 7500 on the local machine:

    grace start tcp:9000 tcp:host=127.0.0.1:port=7500

Switch traffic from port 7500 to port 7600:

    grace switch tcp:host=127.0.0.1:port=7600

Switch traffic from port 7600 to port 7700 and wait for all connections to previous ports (7500 and 7600) to finish:

    grace switch --wait tcp:host=127.0.0.1:port=7700

Stop forwarding:

    grace stop

Upgrade ``grace`` to a new version and swap out the current ``grace`` process with a new one:

    grace restart



## Running the tests ##

Use ``trial`` to run the tests:

    trial grace


