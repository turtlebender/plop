Plop
----------------

Support git-based deploys.  Just plop your code in the repo.

Plop consists of a git pre-receive hook as well as a server component.

The git hook builds the application into a new virtualenv using the 
requirements.txt which is in the directory, then tars the virutalenv
and sends a notification that the build is done.

The server component listens for build completion notifications and
stores the packaged application in S3.

Finally, a client program (which simply uses ssh) deploys the application
to servers by removing the specified server from any load balancers (ELB
at this point), copying the application to the server, tests the deploy
and finally adds the server back into the load balancer.
