import urllib
import json, sqlite3, time, random
import sys
from datetime import datetime
import traceback
import pprint

class caller:
    def __init__(self, key, dbName):
        self.key = key
        self.conn = sqlite3.connect('/home/csexauer/t2.db')

    def getResp(self, userId, domain, method, version):

        if(method == "GetPlayerSummaries"): idName = "&steamids="
        elif(method=="GetFriendList"): idName = "&relationship=friend&steamid="
        else: idName = "&steamid="

        url = "http://api.steampowered.com/" +\
            domain +\
            "/" +\
            method +\
            "/" +\
            version +\
            "/?key=" +\
            self.key +\
            idName +\
            str(userId) +\
            "&format=json"
        if(method == "GetOwnedGames"): url = url + "&include_played_free_games=1"

        resp = urllib.urlopen(url)
        parsedResp = json.loads(resp.read().decode('ascii', 'ignore'))
        return parsedResp

    def insertArray(self, values):
        cur = self.conn.cursor()
        #print(queryString)
        cur.executemany("INSERT INTO user_games VALUES (?,?,?,?)", values)
        self.conn.commit()

    def getUserGames(self, userId):
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" +\
            self.key + "&steamid=" + str(userId) + "&format=json&include_played_free_games=1"
        resp = urllib.urlopen(url)
        parsedResp = json.loads(resp.read().decode('ascii', 'ignore'))
        return parsedResp

    def getGames(self):
        cursor = self.conn.cursor()
        idList = cursor.execute('SELECT distinct user_id from users order by user_id').fetchall()
        ids = [entry[0] for entry in idList]
        ct = 0
        # just pulled all the ids from our id list. Steam chokes @100k calls a day so we'll do 30k x 3
        for userId in ids:
            try:
                gameListParsed = self.getUserGames(userId)
                if('games' in gameListParsed['response']):
                    timeIns = str(datetime.fromtimestamp(time.time()))
                    gameList = gameListParsed['response']['games']
                    insertList = [[userId, g['appid'], timeIns, g['playtime_forever']] 
                                    for g in gameList if int(g['playtime_forever']) > 0 ]
                    self.insertArray(insertList)
                    #pprint.pprint(insertList)
            except:
                traceback.print_exc()
                #print("Error updating " + str(userId))

    def getUsers(self, userIds):
        userInfoParsed = self.getResp(userIds, "ISteamUser", "GetPlayerSummaries", "v0002")
        #communityvisibilitystate = 3 means public,1 means private, need public. Record this.
        playerlist = userInfoParsed['response']['players']
        testct = 0
        for p in playerlist:
            if p['communityvisibilitystate'] == 3 and 'lastlogoff' in p and time.time() - p['lastlogoff'] <= 1209600:
                testct = testct + 1
                #user info
                thisId = p['steamid']

                if 'loccountrycode' in p:
                    country = p['loccountrycode']
                else:
                    country = ''
                #friend list
                friendListParsed = self.getResp(thisId, "ISteamUser", "GetFriendList", "v0001")
                friendList = friendListParsed['friendslist']['friends']
                friendCount = 0
                with self.conn:
                    cur = self.conn.cursor()
                    for f in friendList:
                        friendCount = friendCount + 1

                    cur.execute("INSERT INTO users VALUES("+\
                        str(thisId)+","+\
                        str(friendCount)+",'"+\
                        str(country)+"',"+\
                        str(p['timecreated'])+")")
        #so we don't go over the steam call limit when collecting info
        return testct
