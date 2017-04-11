from selenium.webdriver import Firefox
from requests import Session
from lxml import etree
import pymongo
import json
import time
import os
import pickle
import re

class Weibo(object):
    def __init__(self, username, password, mysession, collection):
        self.username = username
        self.password = password
        self.mysession = mysession
        self.collection = collection
        self.firefox = Firefox()

    def login(self):
        if "cookies" not in os.listdir():
            self.firefox.get("http://www.weibo.com/")
            input("Press any key when login page finishes loading:")
            usernameinput = self.firefox.find_element_by_id("loginname")
            passwordinput = self.firefox.find_element_by_name("password")
            submit = self.firefox.find_element_by_xpath("//span[@node-type='submitStates']")
            usernameinput.click()
            usernameinput.send_keys(self.username)
            passwordinput.click()
            passwordinput.send_keys(self.password)
            submit.click()
            input("Press any key when you are logged in:")
            self.userid = re.findall('/u/(\d+)/home', self.firefox.current_url)[0]
            cookies = self.firefox.get_cookies()
            with open("cookies","wb") as f:
                f.write(pickle.dumps(cookies))
            with open("userid", "w") as f:
                f.write(self.userid)
        else:
            with open("cookies","rb") as f:
                cookies = pickle.loads(f.read())
            with open("userid", "r") as f:
                self.userid = f.read()
        for cookie in cookies:
            self.mysession.cookies.set(cookie['name'], cookie['value'])
        return True

    def crawl(self, layer=2, start_layer=None):
        if start_layer==None:
            self.craw_following_meta()
            start_layer=1
        for i in range(start_layer,layer):
            count = collection.find({"layer":i, "following":{"$size":0}}).count()
            query = collection.find({"layer":i, "following":{"$size":0}})
            for j, ele in enumerate(query):
                print("{0} of {1} users processed at layer {2}".format(j,count,i))
                try:
                    self.other_user_following(ele['_id'], i)
                    time.sleep(1)
                except Exception:
                    with open("Failed", "a") as f:
                        f.write("Failed user:" + str(ele['_id'])+'at leyer' + str(i) + '\n')
                    print("Failed User:" + str(ele['_id']))

    def craw_following_meta(self):
        resp = self.mysession.get("http://weibo.com/{0}/follow".format(self.userid))
        nike = re.findall(r"CONFIG\['nick'\]='(.*)'", resp.text)[0]
        useravatar = re.findall(r"CONFIG\['avatar_large'\]='(.*)'", resp.text)[0]
        try:
            self.collection.insert_one({"_id":self.userid, "nike":nike, "avatar":useravatar,'layer':0, 'following':[]})
        except Exception as e:
            print("user already exists")
            pass
        tree = self.parse_html_from_js(resp.text, 'pl.relation.myFollow.index')
        href_pattern, num_pages = Weibo.parse_pages(tree)
        for page in range(1,num_pages+1):
            url = "http://www.weibo.com" + href_pattern.format(page=str(page))
            resp = self.mysession.get(url)
            tree = self.parse_html_from_js(resp.text, 'pl.relation.myFollow.index')
            for img in tree.xpath("//img[@usercard]"):
                avatar=img.xpath("@src")[0]
                nike=img.xpath('@title')[0]
                userid=img.xpath("@usercard")[0][3:]
                try:
                    self.collection.update({"_id":self.userid},{"$addToSet":{"following":userid}})
                    self.collection.insert_one({"_id":userid, 'avatar':avatar, 'nike':nike,'layer':1, 'following':[]})
                except Exception:
                    print("user already exists")

    def other_user_following(self, uid, current_layer):
        print(uid.center(60,"-"))
        resp = self.mysession.get("http://weibo.com/u/{uid}".format(uid=uid))
        tree = self.parse_html_from_js(resp.text, "pl.content.homeFeed.index")
        weiboLevel = tree.xpath("//div[@class='PCD_person_info']/descendant::a[contains(@class,'W_icon_level')]/span")[0].text[3:]
        if len(tree.xpath("//span[contains(@class,'ficon_cd_place')]"))>0:
            location = tree.xpath("//span[@class='item_text W_fl']")[1].text.strip()
        else:
            location = None
        header = self.parse_html_from_js(resp.text,"pl.header.head.index")
        gender = header.xpath("//span[@class='icon_bed']/a/i/@class")[0]
        if "female" in gender:
            gender="female"
        else:
            gender="male"
        try:
            self.collection.update({"_id":uid},{"$set":{"weiboLevel":weiboLevel,"gender":gender, "location":location}})
        except:
            print("fail to update user profile")
        page_id = re.findall("\['page_id'\]='(\d*)'", resp.text)[0]
        url = "http://weibo.com/p/{0}/follow".format(page_id)
        resp = self.mysession.get(url)
        ns = "pl.content.followTab.index"
        tree = self.parse_html_from_js(resp.text,ns)
        href_pattern, num_pages = Weibo.parse_pages(tree)
        for page in range(1, num_pages+1):
            url = "http://www.weibo.com" + href_pattern.format(page=str(page))
            resp = self.mysession.get(url)
            ns = "pl.content.followTab.index"
            tree = self.parse_html_from_js(resp.text, ns)
            for img in tree.xpath("//img[@usercard]"):
                dl = img.getparent().getparent().getparent()
                location = dl.xpath("dd[1]/div[3]/span/text()")[0]
                gender = 'female' in dl.xpath("dd[1]/div[1]/a[3]/i/@class")
                if gender:
                    gender="female"
                else:
                    gender="male"
                userid = re.findall('id=(\d+)', img.xpath("@usercard")[0])[0]
                avatar = img.xpath("@src")[0]
                nike = img.xpath("@alt")[0]
                try:
                    self.collection.update({"_id":uid},{"$addToSet":{"following":userid}})
                    self.collection.insert_one({"_id":userid, "gender":gender, "location":location, "avatar":avatar, "nike":nike, "layer":current_layer+1, "following":[]})
                    print("user:" + nike)
                except:
                    print("user already exists")


    def parse_html_from_js(self, text, ns):
        followingstr = re.findall(r'{"ns":"' +ns+ '",.*}', text)[0]
        followingdict = json.loads(followingstr)
        htmlstr = followingdict['html']
        tree = etree.HTML(htmlstr)
        return tree

    @staticmethod
    def parse_pages(tree):
        href = tree.xpath('//div[@class="W_pages"]/a[@bpfilter]/@href')[0]
        href_pattern = re.sub('page=(\d+)', 'page={page}', href)
        num_pages = len(tree.xpath('//div[@class="W_pages"]/a')) - 2  # Don't know what happen if only only one page is available
        return href_pattern, num_pages

if __name__ == "__main__":
    from requests.packages.urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    mysession = Session()
    retries = Retry(total=5,backoff_factor=3)
    mysession.mount('http://', HTTPAdapter(max_retries=retries))
    connection = pymongo.MongoClient()
    db = connection.weibo
    collection = db.users
    weibo = Weibo("Use your username", "Use your password", mysession, collection)
    weibo.login()
    weibo.crawl()
