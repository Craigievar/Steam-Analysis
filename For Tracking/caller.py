from urllib import request
import json, sqlite3, time, random
import sys

class caller:
    def __init__(self, key, dbName):
        self.key = key
        self.conn = sqlite3.connect(dbName)

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

        resp = request.urlopen(url)
        parsedResp = json.loads(resp.read().decode('ascii', 'ignore'))
        return parsedResp

    def getGames(self):
        ts = time.time()
        cursor = self.conn.cursor()
        idList = cursor.execute('SELECT distinct user_id from users').fetchall()
        ids = [entry[0] for entry in idList]
        ct = 0 
        # just pulled all the ids from our id list. Steam chokes @100k calls a day so we'll do 30k x 3
        for userId in ids:
            ct = ct + 1
            try:
                gameListParsed = self.getResp(userId, "IPlayerService", "GetOwnedGames", "v0001")   
                if('games' in gameListParsed['response']):
                    gameList = gameListParsed['response']['games']
                    with self.conn:
                        cur = self.conn.cursor()
                        for g in gameList:
                            cur.execute("INSERT INTO user_games VALUES("+\
                                str(userId)+","+\
                                str(g['appid'])+","+\
                                str(ts)+","+\
                                str(g['playtime_forever'])+")")
            except: 
                print("Error updating " + str(userId))
            if ct%5000 == 0:
                    print(ct)


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
