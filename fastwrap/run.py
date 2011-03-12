#!/usr/bin/python
import os, sys, shutil, subprocess, time
ROBODIR = "/tmp/robot"

# Log to /tmp/fastlog in case one wants to examine what's happening.
sys.stderr = sys.stdout = open("/tmp/fastlog", "at", 1)
start_time = time.time()

# We're in $SOMEWHERE/run.py
# robot.zip is at $SOMEWHERE/../robot.zip

if os.path.exists(ROBODIR):
    "Clean any existing state"
    shutil.rmtree(ROBODIR)
os.mkdir(ROBODIR)

# Extract robot.zip from the fastwrapped robot.zip
subprocess.call( "./fastwrap-extract ../robot.zip /tmp/robot.zip",
                 shell = True )

# Unzip robot.zip
subprocess.call( "unzip -o /tmp/robot.zip -d %s" % ROBODIR,
                 shell = True )

# Remove robot.zip to reduce memory consumption
os.remove( "/tmp/robot.zip" )

# Hack around zips not storing permission bits
subprocess.call( "find %s -type f | xargs chmod u+x" % ROBODIR, shell = True )

logdir = os.getcwd()
os.chdir( ROBODIR )

print "Unwrapping into %s took %f seconds" % (ROBODIR, time.time() - start_time)
sys.stdout.flush()
os.execlp( "python", "python", os.path.join( ROBODIR, "run.py" ),
           "--log-dir", logdir )
