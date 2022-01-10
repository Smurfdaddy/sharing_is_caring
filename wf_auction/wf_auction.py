import json, requests, copy, math, time

from bs4 import BeautifulSoup as bs4
from requests_html import HTMLSession
from tkinter import *

from custom_parser import custom_parser

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))

p = custom_parser()
class Network:

    def __init__(self):
        
        #warframe.market stuff
        self.riven_template_wm = {
            "starting_price":0,
            "buyout_price":0,
            "minimal_reputation":0,
            "private": False,
            "note":"",
            "item":{
                "weapon_url_name":"",
                "name":"",
                "type":"riven",
                "attributes": [],
                "mastery_level":8,
                "mod_rank":0,
                "re_rolls":0,
                "polarity":""
            }
        }
        self.attribute_template = {
            "url_name":"",
            "positive":True,
            "value":0
        }
        self.headers_wm = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Host": "api.warframe.market",
            "language": "en",
            "Origin": "https://warframe.market",
            "platform": "pc",
            "TE": "Trailers",
            "Referer": "https://warframe.market/",
            "authorization": "",
            "auth_type": "header"
        }
        self.WFM_API = "https://api.warframe.market/v1"

        #riven.market
        self.rm_session = requests.session() #needed for cookies
        # POST /sell HTTP/1.1
        # Host: riven.market
        # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0
        # Accept: */*
        # Accept-Language: en-GB,en;q=0.5
        # Accept-Encoding: gzip, deflate, br
        # Content-type: application/x-www-form-urlencoded
        # Content-Length: 258
        # Origin: https://riven.market
        # DNT: 1
        # Connection: keep-alive
        # Referer: https://riven.market/profile
        # Cookie: rm-persistent=JDJ5JDEwJHpEOVRrSXdGeHRIcmkvNHIxTE5iaS5LUWtwTHUxU3h0QkxidFZHLzFpRzhpUzI0YU1qd1Zh; rivenmarket-login=fqvmdvumpar1rss0qgl22ijhjl
        # Sec-Fetch-Dest: empty
        # Sec-Fetch-Mode: cors
        # Sec-Fetch-Site: same-origin
        self.headers_rm = {
            "Host": "riven.market",
            "Accept": "*/*",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-type": "application/x-www-form-urlencoded",
            "Origin": "https://riven.market",
            "DNT": "1",
            "Connection": "keep-alive",
            "Referer": "https://riven.market/profile/",
            "Cookie": "rm-persistent=?; rivenmarket-login=?",
        }
        self.riven_template_rm = { #platprice=600&sell=SELL&veiled=null&type=Primary&next=true&weapon=Phaedra&stat1=Toxin&stat2=Multi&stat3=CritChance&stat4=Puncture&stat1amount=146.7&stat2amount=72.0&stat3amount=110.5&stat4amount=83.0&name=Toxi-saticron&polarity=madurai&rerolls=0&rank=8&mastery=14
            "platprice": 0,
            "sell": "SELL",
            "veiled": "null",
            "type": "riven",
            "next": "true",
            "weapon": "",
            "stat1": "",
            "stat2": "",
            "stat3": "",
            "stat4": "",
            "stat1amount": 0,
            "stat2amount": 0,
            "stat3amount": 0,
            "stat4amount": 0,
            "name": "",
            "polarity": "",
            "rerolls": 0,
            "rank": 0,
            "mastery": 0
        }
        self.rivens = []
        self.unknown_auctions = []
        self.load()

    def login(self, user_email: str, user_password: str, platform: str = "pc", language: str = "en"):
        """
        Used for logging into warframe.market via the API.
        Returns (User_Name, JWT_Token) on success,
        or returns (None, None) if unsuccessful.
        """
        headers = {
            "Content-Type": "application/json; utf-8",
            "Accept": "application/json",
            "Authorization": "JWT",
            "platform": platform,
            "language": language,
        }
        content = {"email": user_email, "password": user_password, "auth_type": "header"}
        response = requests.post(f"{self.WFM_API}/auth/signin", data=json.dumps(content), headers=headers)
        if response.status_code != 200: print("WFM Login failed."); return None, None
        return (response.json()["payload"]["user"]["ingame_name"], response.headers["Authorization"])

    def load(self):
        user_data = {}
        session = HTMLSession()
        with open('settings.json') as json_file:
            user_data = json.load(json_file)
        ign, self.headers_wm["authorization"] = self.login(user_data["E-Mail"], user_data["PW"])
        self.headers_rm["Referer"] = self.headers_rm["Referer"]+ign
        #Getting rivens from RM:
        rivens = []
        rm_source = "https://riven.market/_modules/riven/showrivens.php?baseurl=Lw==&platform=PC&limit=500&recency=0&veiled=false&onlinefirst=false&polarity=all&rank=all&mastery=16&weapon=Any&stats=Any&neg=all&price=99999&rerolls=-1&sort=time&direction=ASC&user=REPLACE_ME&page=1"
        rm_source = rm_source.replace("REPLACE_ME", str(user_data["RM-ID"]))
        with session.get(rm_source) as html:
            soup = bs4(html.text, "html.parser")
            rivens = soup.find_all("div", class_ = "riven")
        print(len(rivens), "rivens found on RM")
        #Getting rivens from WM:
        wm_source = "https://warframe.market/profile/"+user_data["IGN"]+"/auctions"
        with session.get(wm_source) as html:
            relevant_section = bs4(html.text, "lxml").find(id = "application-state").text
            wm_rivens = json.loads(str(relevant_section))["payload"]["auctions"]

        temp_rivens = []
        for riven in rivens:
            new_riven = {
                "wm_id": 0,
                "wm_riven": None,
                "rm_id": 0,
                "rm_riven": None
            }

            try:
                rm_riven, rm_id = self.riven_to_json_rm(riven)
                new_riven["rm_id"] = rm_id
                new_riven["rm_riven"] = rm_riven
            except Exception as e: print("RM conversion failed:", e)

            try: 
                new_riven["wm_riven"] = self.riven_to_json_wm(riven)
            except Exception as e: print("WM conversion failed:", e)

            temp_rivens.append(new_riven)
        rivens = sorted(temp_rivens, key=lambda k: k["rm_riven"]["weapon"])

        #Adding WM-IDs to the RM rivens:
        for alt_riven in wm_rivens:
            match_found = False
            for riven in rivens:
                if riven["wm_riven"]["item"]["attributes"] == alt_riven["item"]["attributes"]:
                    riven["wm_id"] = alt_riven["id"]
                    match_found = True
            if not match_found:
                print("IDK", alt_riven["item"]["weapon_url_name"], alt_riven["item"]["name"]+":", alt_riven["item"]["attributes"], "\n")
                self.unknown_auctions.append(alt_riven["id"])
                
        self.rivens = rivens

    def riven_to_json_wm(self, riven):
        payload = copy.deepcopy(self.riven_template_wm)
        payload["starting_price"] = int(riven["data-price"])
        payload["buyout_price"] = int(riven["data-price"])
        payload["item"]["weapon_url_name"] = riven["data-weapon"].lower().replace("&", "and").replace("dark_split-sword", "dark_split_sword_(dual_swords)")
        payload["item"]["name"] = riven["data-name"].lower()
        payload["item"]["mastery_level"] = int(riven["data-mr"])
        payload["item"]["mod_rank"] = int(riven["data-rank"])
        payload["item"]["re_rolls"] = int(riven["data-rerolls"])
        payload["item"]["polarity"] = riven["data-polarity"]
        for x in range(1,5):
            the_key = "data-stat"+str(x)
            if riven[the_key+"val"] != "0.0":
                attribute = copy.deepcopy(self.attribute_template)
                attribute["url_name"] = p.dictionary[riven[the_key]]
                attribute["value"] = float(riven[the_key+"val"])
                if x == 4: #Negative stat
                    attribute["positive"] = False
                    if attribute["url_name"] != "recoil": #invert neg value
                        attribute["value"] = -attribute["value"]
                payload["item"]["attributes"].append(attribute)
        return(payload)

    def riven_to_json_rm(self, riven):
        payload = copy.deepcopy(self.riven_template_rm)
        payload["platprice"] = int(riven["data-price"])
        payload["weapon"] = riven["data-weapon"]
        payload["name"] = riven["data-name"]
        payload["mastery"] = int(riven["data-mr"])
        payload["rank"] = int(riven["data-rank"])
        payload["rerolls"] = int(riven["data-rerolls"])
        payload["polarity"] = riven["data-polarity"]
        payload["type"] = riven["data-wtype"]
        for x in range(1,5):
            the_key = "data-stat"+str(x)
            if riven[the_key+"val"] != "0.0":
                payload["stat"+str(x)] = riven[the_key]
                payload["stat"+str(x)+"amount"] = float(riven[the_key+"val"])
        return(payload, riven["id"].replace("riven_", ""))

    def upload_riven_wm(self, payload):
        response = requests.post("https://api.warframe.market/v1/auctions/create", data = json.dumps(payload, separators=(',', ':')), headers = self.headers_wm)
        if response.status_code != 200: print("Auction", payload["item"]["weapon_url_name"], payload["item"]["name"], "Creation Failed:", response.status_code)
        else: print("wm +")

    def delete_riven_wm(self, riven_id):
        response = requests.put("https://api.warframe.market/v1/auctions/entry/"+str(riven_id)+"/close", headers = self.headers_wm)
        if response.status_code != 200: print("Deletion failed:", riven_id)
        else: print("wm -")

    def delete_all_rivens_wm(self):
        for riven in self.rivens:
            if riven["wm_id"] != 0:
                self.delete_riven_wm(riven["wm_id"])
                time.sleep(0.5) #to prevent overloading wfm api       
    
    def upload_riven_rm(self, payload):
        #Fixing Cookie
        self.rm_session.get("https://riven.market/")
        rm_cookies = self.rm_session.cookies.get_dict()
        self.headers_rm["Cookie"] = ("rm-persistent="+rm_cookies["rm-persistent"]+"; rivenmarket-login="+rm_cookies["rivenmarket-login"])

        converted_payload = ""
        for key in payload:
            converted_payload = converted_payload+str(key)+"="+str(payload[key])+"&"
        converted_payload = converted_payload[:-1]
        print("header:", self.headers_rm)
        print("payload:", converted_payload)
        response = requests.post("https://riven.market/sell", data = json.dumps(payload, separators=(',', ':')), headers = self.headers_rm)
        
        if response.status_code != 200: print("Upload failed")
        else: print("rm +")
        
    def delete_riven_rm(self, riven_id):
        #Fixing Cookie
        self.rm_session.get("https://riven.market/")
        rm_cookies = self.rm_session.cookies.get_dict()
        self.headers_rm["Cookie"] = ("rivenmarket-login="+rm_cookies["rivenmarket-login"]+"; rivenmarket-login="+rm_cookies["rivenmarket-login"])

        response = requests.get("https://riven.market/_php/ajax.php?updateriven="+riven_id+"&state=deleted&time=0", headers = self.headers_rm)
        if response.status_code != 200: print("Deletion failed:", riven_id)
        else: print("rm -")

    def transfare_all(self, rivens: list):
        for riven in rivens:
            self.upload_riven_wm(riven["wm_riven"])
            time.sleep(0.5) #to prevent overloading wfm api
    
    def dual_upload(self, riven: dict):
        try:
            self.upload_riven_wm(riven["wm_riven"])
            self.upload_riven_rm(riven["rm_riven"])
        except Exception as e: print(e)

    def dual_delete(self, riven: dict):
        try:
            if riven["wm_id"] != 0: self.delete_riven_wm(riven["wm_id"])
            self.delete_riven_rm(riven["rm_id"])
        except Exception as e: print(e)

    def full_refresh(self):
        for riven in self.rivens:
            self.dual_delete(riven)
            time.sleep(0.5) #to prevent overloading wfm api
        print("All rivens deleted")
        for riven in self.rivens: 
            self.dual_upload(riven)
            time.sleep(0.5) #to prevent overloading wfm api
        print("All rivens uploaded")

    def rm_tester(self, index: int):
        self.upload_riven_rm(self.rivens[index]["rm_riven"])

class App:

    def __init__(self):
        self.window = Tk()
        self.window.title("Auction Creator")

        net = Network()
        print(len(net.unknown_auctions), "unknown auctions found.")

        Button(self.window, text="Transfare All Rivens (RM > WM)", justify="left", font="helvetica 9", command=lambda : net.transfare_all(net.rivens)).grid(row=0, column=0, sticky="w")
        Button(self.window, text="Delete All Auctions", justify="left", font="helvetica 9", command=lambda : net.delete_all_rivens_wm()).grid(row=0, column=1, sticky="w")
        #Button(self.window, text="Refresh All Rivens", justify="left", font="helvetica 9", command=lambda : net.full_refresh()).grid(row=0, column=2, sticky="w")
        #Button(self.window, text="RM test", justify="left", font="helvetica 9", command=lambda : net.rm_tester(1)).grid(row=0, column=3, sticky="w")
        
        #table head
        self.e = Entry(self.window, width=20, font="helvetica 9 bold")
        self.e.grid(row=1, column=0)
        self.e.insert(END, "Riven")
        self.e = Entry(self.window, width=20, font="helvetica 9 bold")
        self.e.grid(row=1, column=1)
        self.e.insert(END, "Price")
        self.e = Entry(self.window, width=20, font="helvetica 9 bold")
        self.e.grid(row=1, column=2)
        self.e.insert(END, "Auction?")

        for y in range(len(net.rivens)):
            rivens_per_row = 30
            gap = math.floor(y/rivens_per_row)

            tabled_riven = [
                net.rivens[y]["wm_riven"]["item"]["weapon_url_name"].capitalize().replace("_", " ")+" "+net.rivens[y]["wm_riven"]["item"]["name"],
                int(net.rivens[y]["wm_riven"]["buyout_price"]),
                ""
            ]
            if net.rivens[y]["wm_id"] != 0: tabled_riven[2] = "Y"
            for x in range(len(tabled_riven)):
                self.e = Entry(self.window, width=20, font="helvetica 9")
                self.e.grid(row=y+2-(gap*rivens_per_row), column=x+4*gap)
                self.e.insert(END, tabled_riven[x])
            button = Button(self.window, text="Create Auction", justify="left", font="helvetica 9", command=lambda y=y: net.upload_riven_wm(net.rivens[y]["wm_riven"]))
            button.grid(row=y+2-(gap*rivens_per_row), column=3+4*gap, sticky="w")

        self.window.mainloop()

app = App()