import collections, datetime, hashlib, http.client, json, math, os.path, random, threading, zlib

class ExploringGirls:
    def __init__(self):
        self.server = ""
        self.headers = { }

    def start(self, config):
        # Meaningless, just make it looks like official client
        self.server = "login.version.p7game.com"
        self.headers = collections.OrderedDict([
            ("charset", "UTF-8"),
            ("X-Unity-Version", "4.6.4f1"),
            ("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 6 Build/LRX21D)"),
            ("Host", "login.version.p7game.com"),
            ("Connection", "Keep-Alive"),
            ("Accept-Encoding", "gzip")
        ])
        self.httpGet("/index/checkVer/1.3.1/0/1")

        # Still meaningless
        self.server = "login.alpha.p7game.com"
        self.headers["Host"] = self.server
        self.httpGet("/index/getInitConfigs/")

        # Login with username and password
        url = "/index/passportLogin/" + config["username"] + "/" + config["password"]
        # Device ID offered by TalkingData library, randomly generated here
        params = '{"deviceId":"' + config["talkingDataId"] + '"}'
        response = self.httpPost(url, params)
        cookie = response.getheader("Set-Cookie").split(';')[0]
        uid = cookie.split('=')[1].split('.')[0]
        if not ("uid" in config):
            input("请确认您的UID是" + uid + "，按回车键继续")
        elif uid != config["uid"]:
            print("Error: UID Missmatch!")
            return

        # Login with UID
        self.server = config["server"]
        self.headers = collections.OrderedDict([
            ("charset", "UTF-8"),
            ("Cookie", cookie),
            ("X-Unity-Version", "4.6.4f1"),
            ("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 5.1; Nexus 6 Build/LRX21D)"),
            ("Host", self.server),
            ("Connection", "Keep-Alive"),
            ("Accept-Encoding", "gzip")
        ])
        response = self.httpGet("/index/login/" + uid, setCookie = True)

        # Game start, fetch data
        # Device ID offered by Unity3D, randomly generated here
        info = self.httpGet("/api/initData/" + config["unity3dId"] + "/")

        # Make it looks like official client
        self.httpGet("/active/getUserData")

        # Deal with remaining time
        info = info["pveExploreVo"]["levels"]
        cnt = 0
        for fleetInfo in info:
            # delay 20 more seconds to make it safer
            delay = ExploringGirls.calcRemainingTime(fleetInfo["endTime"]) + 20
            if delay <= 0:
                self.restartExplore(fleetInfo["fleetId"], fleetInfo["exploreId"])
            else:
                threading.Timer(delay, self.restartExplore, [fleetInfo["fleetId"], fleetInfo["exploreId"]]).start()
                log = datetime.datetime.now().strftime("%H:%M:%S")
                log += " 舰队" + str(fleetInfo["fleetId"]) + "正在远征，"
                log += "剩余" + str(math.floor(delay / 60)) + "分钟"
                print(log)
            cnt += 1
        if cnt < 4:
            print("Warning: only " + str(cnt) + " fleets are exploring")

        return uid

    def restartExplore(self, fleet, exploreId):
        # Get fleet back
        self.httpGet("/explore/getResult/" + exploreId)
        # Start exploring
        info = self.httpGet("/explore/start/" + fleet + "/" + exploreId)
        info = info["pveExploreVo"]["levels"]
        for fleetInfo in info:
            if fleetInfo["fleetId"] == fleet:
                # delay 20 more seconds to make it safer
                delay = ExploringGirls.calcRemainingTime(fleetInfo["endTime"]) + 20
                threading.Timer(delay, self.restartExplore, [fleet, exploreId]).start()
                log = datetime.datetime.now().strftime("%H:%M:%S")
                log += " 舰队" + str(fleetInfo["fleetId"]) + "开始远征，"
                log += "剩余" + str(math.floor(delay / 60)) + "分钟"
                print(log)
                return
        print("Error: failed to restart exploration!")

    def calcRemainingTime(timestamp):
        # It seems the server is using client's local time
        endtime = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()
        return (endtime - now).total_seconds()

    def httpGet(self, url, setCookie = False):
        #conn = http.client.HTTPConnection(self.server)
        conn = http.client.HTTPConnection("127.0.0.1:8080")
        conn.set_tunnel(self.server)
        url = ExploringGirls.completeUrl(url)
        conn.request("GET", url, None, self.headers)
        response = conn.getresponse()
        if setCookie:
            self.headers["Cookie"] = response.getheader("Set-Cookie").split(';')[0]
        data = zlib.decompress(response.read())
        return json.loads(data.decode("utf-8"))

    def httpPost(self, url, params):
        #conn = http.client.HTTPConnection(self.server)
        conn = http.client.HTTPConnection("127.0.0.1:8080")
        conn.set_tunnel(self.server)
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

serverNames = [ "", "", "胡德", "萨拉托加", "俾斯麦", "声望", "纳尔逊", "空想", "突击者", "海伦娜" ]

if os.path.isfile("config.json"):
    configFile = open("config.json", "r")
    config = json.load(configFile)
    ExploringGirls().start(config)

else:
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    print("服务器代码:")
    for i in range(2, 9):
        print("  " + str(i) + " " + serverNames[i])
    serverCode = input("请选择服务器: ")
    server = "s" + serverCode + ".zj.p7game.com"
    print("已选择服务器: " + serverNames[int(serverCode)])

    config = {
        "username": username,
        "password": password,
        "server": server,
        "talkingDataId": "".join([random.choice("0123456789abcdef") for x in range(33)]),
        "unity3dId": "".join([random.choice("0123456789abcdef") for x in range(32)]),
    }

    uid = ExploringGirls().start(config)

    config["uid"] = uid
    configFile = open("config.json", "w")
    json.dump(config, configFile)
    configFile.close()
