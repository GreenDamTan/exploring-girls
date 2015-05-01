import collections, datetime, hashlib, http.client, json, math, threading, zlib

username = "Your user name"
password = "Your password"
uid = "Your UID"
server = "s6.zj.p7game.com"

# Servers:
#   s2.zj.p7game.com  胡德
#   s3.zj.p7game.com  萨拉托加
#   s4.zj.p7game.com  俾斯麦
#   s5.zj.p7game.com  声望
#   s6.zj.p7game.com  纳尔逊
#   s7.zj.p7game.com  空想
#   s8.zj.p7game.com  突击者
#   s9.zj.p7game.com  海伦娜

class ExploringGirls:
    def __init__(self, username, password, uid, server):
        self.headers = collections.OrderedDict([
            ("charset", "UTF-8"),
            ("X-Unity-Version", "4.6.4f1"),
            ("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 6 Build/LRX21D)"),
            ("Host", "login.version.p7game.com"),
            ("Connection", "Keep-Alive"),
            ("Accept-Encoding", "gzip")
        ])
        # Meaningless, just make it looks like official client
        self.httpGet("login.version.p7game.com", "/index/checkVer/1.3.1/0/1")

        self.headers["Host"] = "login.alpha.p7game.com"
        # Still meaningless
        self.httpGet(server, "/index/getInitConfigs/")

        # Login with username and password
        url = "/index/passportLogin/" + username + "/" + password
        # Device ID offered by TalkingData library, randomly generated here
        params = '{"deviceId":"59d25ff4a002f1bc5884cc23a166e563c"}'
        response = self.httpPost("login.alpha.p7game.com", url, params)
        cookie = response.getheader("Set-Cookie").split(';')[0]
        if cookie.split('.')[0] != "hf_skey=" + uid :
            print("Error: UID mismatch!")
            return

        # Login with UID
        self.headers = collections.OrderedDict([
            ("charset", "UTF-8"),
            ("Cookie", cookie),
            ("X-Unity-Version", "4.6.4f1"),
            ("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 6 Build/LRX21D)"),
            ("Host", server),
            ("Connection", "Keep-Alive"),
            ("Accept-Encoding", "gzip")
        ])
        response = self.httpGet(server, "/index/login/" + uid, setCookie = True)

        # Game start, fetch data
        # Device ID offered by Unity3D, randomly generated here
        info = self.httpGet(server, "/api/initData/eb9b212e0594f8879fc9c4ea1b56050e/")

        # Make it looks like official client
        self.httpGet(server, "/active/getUserData")

        # Deal with remaining time
        info = info["pveExploreVo"]["levels"]
        print(info)
        cnt = 0
        for fleetInfo in info:
            # delay 20 more seconds to make it safer
            delay = ExploringGirls.calcRemainingTime(fleetInfo["endTime"]) + 20
            if delay <= 0:
                self.restartExplore(fleetInfo["fleetId"], fleetInfo["exploreId"])
            else:
                threading.Timer(delay, self.restartExplore, [fleetInfo["fleetId"], fleetInfo["exploreId"]]).start()
                log = "Fleet " + str(fleetInfo["fleetId"]) + " is exploring"
                log += ", coming back in " + str(math.floor(delay / 60)) + " minutes"
                print(log)
            cnt += 1
        if cnt < 4:
            print("Warning: only " + str(cnt) + " fleets are exploring")

    def restartExplore(self, fleet, exploreId):
        # Get fleet back
        self.httpGet(server, "/explore/getResult/" + exploreId)
        # Start exploring
        info = self.httpGet(server, "/explore/start/" + fleet + "/" + exploreId)
        info = info["pveExploreVo"]["levels"]
        for fleetInfo in info:
            if fleetInfo["fleetId"] == fleet:
                # delay 20 more seconds to make it safer
                delay = ExploringGirls.calcRemainingTime(fleetInfo["endTime"]) + 20
                threading.Timer(delay, self.restartExplore, [fleet, exploreId]).start()
                log = "Fleet " + fleet + " has gone to " + exploreId
                log += ", coming back in " + math.floor(delay / 60) + " minutes"
                print(log)
                return
        print("Error: failed to restart exploration!")

    def calcRemainingTime(timestamp):
        # It seems the server is using client's local time
        endtime = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()
        return (endtime - now).total_seconds()

    def httpGet(self, domain, url, setCookie = False):
        conn = http.client.HTTPConnection(domain)
        #conn = http.client.HTTPConnection("127.0.0.1:8080")
        #conn.set_tunnel(domain)
        url = ExploringGirls.completeUrl(url)
        conn.request("GET", url, None, self.headers)
        response = conn.getresponse()
        if setCookie:
            self.headers["Cookie"] = response.getheader("Set-Cookie").split(';')[0]
        data = zlib.decompress(response.read())
        return json.loads(data.decode("utf-8"))

    def httpPost(self, domain, url, params):
        conn = http.client.HTTPConnection(domain)
        #conn = http.client.HTTPConnection("127.0.0.1:8080")
        #conn.set_tunnel(domain)
        url = ExploringGirls.completeUrl(url)
        postHeader = self.headers
        postHeader["Content-Type"] = "application/x-www-form-urlencoded"
        postHeader["Content-Length"] = "48"
        conn.request("POST", url, params, postHeader)
        return conn.getresponse()

    def getT():
        # timestamp
        time_of_20150101 = 63555667200
        delta = datetime.datetime.now() - datetime.datetime(2015, 1, 1)
        seconds = delta.total_seconds() + time_of_20150101
        return str(math.trunc(seconds * 10000000))
    
    def getE(string):
        # checksum
        salt = "Mb7x98rShwWRoCXQRHQb"
        e = hashlib.md5((string + salt).encode("utf-8"))
        return e.hexdigest()
    
    def completeUrl(url):
        url += "&t=" + ExploringGirls.getT()
        url += "&e=" + ExploringGirls.getE(url[1:])
        return url + "&gz=1&market=0&channel=1&version=1.3.1"

obj = ExploringGirls(username, password, uid, server)
