# 微博爬虫 + 社交网络图可视化
先展示下结果再来解释代码：  
首先有个R语言生成的 [html](https://bigborg.github.io/WeiboSocialNetwork/Rvisualization.html)
- 里面可以看到爬取的数据大致信息，比如爬取的有5017个用户，而0到1,1到2级的关注关系一共有5784个。  
- 男性用户5003,女性13,还有个应该是空白的字符串。天，基本全是男性啊。。。就算扩展到二级而全是男性啊。。。被这比例吓到了，不过后面在可视化的图上大概看了下数据应该是没错的。。。  
- R 里可以很方便的调出你关注的人的关注列表哦，最后还有个被共同关注数最多的用户，好绕，就是统计 你和你直接关注的人 的共同关注，不包括二级底下的关注哦，因为没爬，再爬数据就太多了。  

使用 Cytoscape 进行可视化的结果：
整个社交网络图，包括了二级关注，是不是很像烟花都要炸了：
![all](https://github.com/BigBorg/WeiboSocialNetwork/raw/master/img/all.png)

在 Cytoscape 里还可以用节点的属性设置元素颜色，用层级设置颜色就能很直观的区分出你，你的一级关注，二级关注。该图中红色为本人，蓝色为一级关注，其余为二级关注。什嘛，看不清？其实用 Cytoscape 是可交互的，可以放大缩小，可以拖拽节点，并且可以生成svg哦！用svg存打开也是可以放大到看的清每个用户的昵称的。为什么不直接插入svg？我怕我的好友会杀了我。。。
![me](https://github.com/BigBorg/WeiboSocialNetwork/raw/master/img/me.png)

用用户的性别设置颜色就能很清楚地挑出女性用户了，下图中蓝色为男性，红色为女性。全是蓝的有没有。。。
![gender](https://github.com/BigBorg/WeiboSocialNetwork/raw/master/img/female-male.png)

Cytoscape 社交网络图还有个很不错的用处，可以选择你的好友，然后右键选中所有直接邻居，这样就能看到你的某个特定好友都关注什么了。
![xinlang](https://github.com/BigBorg/WeiboSocialNetwork/raw/master/img/xinlang.png)

Cytoscape 使用上是有UI的，所以不需要代码哦，直接把R代码生成的 Networkdata.csv 导入就好了，注意设置好每个列的属性就好了。具体使用使用可以去[官网](http://www.cytoscape.org/)查找文档。

## 代码运行

- WeiboCrawler.py
首先需要在 WeiboCrawler.py 文件里填上你的用户名，密码。也可以更改爬取的深度，但不建议更改毕竟两层数据量就挺大了，再大可视化的时候也不好弄了。

- process.py
这个主要是整理好数据，写入到csv文件里方便R语言读入。直接运行就好。

- Location.py
这是用来搜索地理位置获取坐标的，只是放着要是要进行地图上的可视化可以使用，地图可视化可以参照我的招聘信息[scrpay项目](https://github.com/BigBorg/Scrapy-playground)。里面使用了高德地图api，所以要用的话需要自己去申请key哦。

- Rvisualization.Rmd
本来想用 R 可视化来着，不过数据量太大了，用 R 可视化的网络图节点全都重叠在一起了。该文件其实主要是进一步处理数据，调整好格式以供 Cytoscape 导入。

使用python 3, selenium调用火狐浏览器进行登录操作，登录完成后把 cookie 导入到 requests 的 session 里，之后使用 requests 进行爬取，这样就避免了全部使用 selenium 导致的效率低问题，同时又省去了逆向微博的登录机制。确保安装好 python 和 R 需要的依赖包，还有记得打开 Mongod 服务。依次运行完 WeiboCrawler.py, process.py 和 Rvisualization.Rmd，这样就有了一份简略的分析报告（html格式）生成，同时生成 Networkdata.csv 文件供 Cytoscape 导入。

## 爬虫代码
主要介绍下爬虫代码。WeiboCrawler.py 里实现了个 Weibo 类。以下一个个介绍方法

### __init__, login
```python
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
```
实例化时候需要提供用户名，密码，requests的Session对象，pymongo的集合。__init__时会用 Selenium 打开 Firefox 浏览器。  
login函数用于登录，首先检查是否存在文件“cookies”，没有才登录，登录后保存一份 cookie 省得每次都需要登录。登录时火狐自动打开微博登录页面，当页面加载完成时候输入任意字符，代码就会自动进行登录，登录完成后再输入任意键继续。此处 selenium 使用还算比较简单，find_element_by_* 方法提供了多种选择来选择元素。在页面元素上可以通过 send_keys 实现输入，click 点击。主要是 cookie 的导出导入，firefox 使用 get_cookies 进行导出。requests session 使用 session.cookies.set(name,value) 来设置 cookie。

### crawl
```python
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
```
crawl 方法是实际运行爬虫的入口方法，layer代表爬取的深度，start_layer为开始爬取的深度，不建议修改参数，因为两层的数据量就挺大了。该方法内对 mongodb 数据库的读取使用了 {"layer":i, "following":{"$size":0}} 的选择器，即读取 i 层并且还未爬取关注列表的用户进行爬取，这样就每次开始运行就可以从上次停止的进度继续了。

### parse_html_from_js, parse_pages 
```python
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
```
其实这里 parse_html_from_js 也应该是静态方法的，只是先这样写了也在别处调用了就懒得改了。parse_html_from_js 方法主要是处理微博返回的数据，生成 etree 对象。微博爬取返回的并不是你看到的页面，而是用 js 生成页面，实际 html 是在 js 的参数里的。所以需要先用正则把 html 对应的字符串拿出来再生成etree。因为微博页面都是这种风格，所以会频繁使用故独立成函数，不同页面对应的 ns 则会不同，如底下的截图：
![response](https://github.com/BigBorg/WeiboSocialNetwork/raw/master/img/SinaResponse.png)

parse_pages 则是从 etree 中获取关注列表对应的网址，不过我关注数是三页，没观察过关注页只有一页的情况是否规则相同。

### craw_following_meta， other_user_following
```python
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
```
该方法是从代码使用者本人开始爬取的，因为页面规则跟其它用户的关注页面不同，所以分成两个函数。其实这里也没什么好说的，都是些xpath和pymongo，就讲重点～比如xpath的“contains(@class,'ficon_cd_place')”用法，可以用于使用了多个类的元素。还有 mongodb 的 $addToSet 操作符，可以防止关注列表重复。不过其实这里还可以更改，因为此处只插入了用户的id，但是我们可视化的时候需要的是用户名，所以其实这里完全可以把关注用户的用户名一并加上，比如这样：  
{  
  "userid":userid,  
  "username":username  
}  
以这样的形式作为一个元素插入进行存储，可以避免后期读取的时候频繁进行跨表查询，毕竟内嵌就是 Mongodb 用来提升效率的一个方法，不然都用成 mysql 了。。。

### Weibo类整体使用
```python
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
```
都写好了，只要改下用户名，密码就好了，实例化后只需要调用 login 和 crawl 方法。
