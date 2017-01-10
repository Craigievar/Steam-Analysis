##you dirty dogs don't get to know my key!
import time
from datetime import datetime

def scheduledPull():
	from caller import caller
	from configs import dbName, keyLoc
	with open(keyLoc, 'r') as keyFile:
	    key = keyFile.read().strip()
	c = caller(key, dbName)
	c.getGames()

log = open('./pullLog.txt', 'a')
log.write('\nattempting a pull at ')
log.write(str(datetime.fromtimestamp(time.time())))
log.close()
scheduledPull()
log = open('./pullLog.txt', 'a')
log.write('\nfinished a pull at ')
log.write(str(datetime.fromtimestamp(time.time())))
log.close()
