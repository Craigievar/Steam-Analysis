import urllib
import json, sqlite3, time, random
import sys
from datetime import datetime
import traceback
import pprint

class caller:
    def __init__(self, key, dbName):
        self.key = key
        self.conn = sqlite3.connect(dbName)
        print(dbName)
        print(key)

    def getUser(self, userIds):
        url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries" +\
            "/v0002/?key=" + self.key + "&steamids=" + str(userIds) + "&format=json"
        resp = urllib.urlopen(url)
        parsedResp = json.loads(resp.read().decode('ascii', 'ignore'))
        return parsedResp

    def insertArray(self, values, cur):
        cur.executemany("INSERT INTO user_games VALUES (?,?,?,?)", values)
        self.conn.commit()

    def getUserGames(self, userId):
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" +\
            self.key + "&steamid=" + str(userId) + "&format=json&include_played_free_games=1"
        resp = urllib.urlopen(url)
        readResp = resp.read()
        parsedResp = json.loads(readResp.decode('ascii', 'ignore'))
        return parsedResp['response']

    def getGameList(self, ids, failThresh):
        cursor = self.conn.cursor()
        failure_count = 0
        total_failures = 0
        empty_count = 0
        fail_ids = []
        testct = 0

        for userId in ids:
            testct += 1
            try:
                gameListResponse = self.getUserGames(userId)
                if('games' in gameListResponse):
                    failure_count = 0
                    timeIns = str(datetime.fromtimestamp(time.time()))
                    gameList = gameListResponse['games']
                    insertList = [[userId, g['appid'], timeIns, g['playtime_forever']]
                                    for g in gameList if int(g['playtime_forever']) > 0 ]
                    if len(insertList) > 0:
                        self.insertArray(insertList, cursor)
                    else:
                        empty_count += 1

                else:
                    failure_count += 1
                    total_failures += 1
                    fail_ids.append(userId)

                    if failThresh and failure_count >= 5:
                        print('{} errors in a row at {}, time = {}'.format(
                            failure_count, testct-4,datetime.fromtimestamp(time.time())))
                        #if it's systematically failing, wait for reset
                        time.sleep(35*60)
                        failure_count = 0

            except:
                print(userId)
                print("http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" +\
                    self.key + "&steamid=" + str(userId) + "&format=json&include_played_free_games=1")
                #traceback.print_exc()

        print("Attempted to insert {}, actually inserted {} ({} empty)".format(
            testct, testct-total_failures, empty_count))
        return fail_ids


    def getGames(self):
        cursor = self.conn.cursor()
        idList = cursor.execute('SELECT distinct user_id from users order by user_id').fetchall()
        ids = [entry[0] for entry in idList]
        fail_ids = self.getGameList(ids, True)
        time.sleep(35*60)

        fail_ids_old = []
        while len(fail_ids_old) != len(fail_ids):
            print("Last run {} vs new run {}".format(len(fail_ids_old), len(fail_ids)))
            fail_ids_old = fail_ids
            fail_ids = self.getGameList(fail_ids, False)


    def getUsers(self, userIds):
        userInfoParsed = self.getUser(userIds)
        #communityvisibilitystate = 3 means public,1 means private, need public. Record this.
        playerlist = userInfoParsed['response']['players']
        testct = 0
        for p in playerlist:
            if p['communityvisibilitystate'] == 3 and 'lastlogoff' in p and time.time() - p['lastlogoff'] <= 1209600:
                userId = p['steamid']
                gameListParsed = self.getUserGames(userId)
                if('games' in gameListParsed['response']):
                    gameList = gameListParsed['response']['games']
                    gameCount = len([g for g in gameList if int(g['playtime_forever']) > 0 ])
                    if gameCount > 0:
                        testct = testct + 1
                        if 'loccountrycode' in p:
                            country = p['loccountrycode']
                        else:
                            country = ''
                        with self.conn:
                            cur = self.conn.cursor()

                            cur.execute("INSERT INTO users VALUES("+\
                                str(userId)+","+\
                                str(country)+"',"+\
                                str(p['timecreated'])+")")
        #so we don't go over the steam call limit when collecting info
        return testct
