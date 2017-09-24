# uppit is possible post then play
import platform
print 'platform.python_version()',platform.python_version()
import sys
import xbmcgui
import xbmcplugin,xbmcvfs
import xbmcaddon,xbmc,os
import urllib
import urllib2
import requests
import re
import settings
import time
import ast

try:
    from sqlite3 import dbapi2 as database
except:
    from pysqlite2 import dbapi2 as database
try:
    import json
except:
    import simplejson as json
from bs4 import BeautifulSoup
#import httplib2
import cPickle as pickle
headers=dict({'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; rv:32.0) Gecko/20100101 Firefox/32.0'})

addonID = 'plugin.video.BDdoridro'
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
addon = xbmcaddon.Addon(id='plugin.video.BDdoridro')
handle = int(sys.argv[1])
logopath = os.path.join( addonUserDataFolder, 'logos')
cacheDir = os.path.join( addonUserDataFolder, 'cache')

metadata_uls=os.path.join(cacheDir,'metadata_uls.txt')

home = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
Doridro_USER = settings.doridro_user()
Doridro_PASSWORD = settings.doridro_pass()
cookie_jar = settings.cookie_jar()
#http://www.moviesfair24.com/category/natok-telefilm-bangla/
if not cacheDir.startswith(('smb://', 'nfs://', 'upnp://', 'ftp://')) and not os.path.isdir(cacheDir)== 1 :
    os.mkdir(cacheDir)


if not logopath.startswith(('smb://', 'nfs://', 'upnp://', 'ftp://')) and not os.path.isdir(logopath)== 1 :
    os.mkdir(logopath)
forum_url = "http://doridro.com/forum/viewforum.php?f={0}"
xbmcplugin.setContent(handle, 'movies')



def get_match(data, regex) :
    match = "";
    m = re.search(regex, data)
    if m != None :
        match = m.group(1) #.group() method to extract specific parts of the match
    else:
        match = ''
    return match

def check_login(source,username):

    #the string you will use to check if the login is successful.
    #you may want to set it to:    username     (no quotes)
    logged_in_string = username

    #search for the string in the html, without caring about upper or lower case
    if re.search(logged_in_string,source,re.IGNORECASE):
        return True
    else:
        return False
def down_url(url,filename=None):
    print 'found download path::', addon.getSetting('download_path')
    if addon.getSetting('download_path') == '':
            addon.openSettings()
    get_file_name = url.split('/')[-1]
    file_name = os.path.join(addon.getSetting('download_path').encode('utf-8'),get_file_name)
    if os.path.exists(file_name):
        notification('File already exists','Same file has been found as %s' %get_file_name)
        return
    pDialog = xbmcgui.DialogProgress()
    #pDialog = xbmcgui.DialogProgressBG()
    pDialog.create('Downloading ......', 'File to download: %s ...' %get_file_name)
    size = 0
    block_sz = 8192
    req = urllib2.Request(url,None,headers)
    song = urllib2.urlopen(req)
    meta = song.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)
    with open(file_name, 'wb') as f:    
        while True:
            buffer = song.read(block_sz)
            if not buffer or pDialog.iscanceled():
                break

            size += len(buffer) 
            f.write(buffer)
            
            pDialog.update(int(size * 100. / file_size),'[COLOR yellow]{0}%[/COLOR]  Done...\nWill be SaveTo:\n{1}'.format(str(int(size * 100. / file_size)),file_name.rsplit('\\',1)[0]))
    pDialog.close()
def _login():
    if Doridro_USER == '' :
        notification('Need Doridro.com User pass','Please register & login in the settings ::.',2000)
        return
    

    if os.path.exists(cookie_jar) and (time.time()-os.path.getmtime(cookie_jar) < 60*60*10) and os.path.getsize(cookie_jar) > 5:
        #notification('Already Logged IN','Logged In to doridro.Com as %s ::.'%Doridro_USER,2000)
        print 'Logged in for A day'
    else:
        session = requests.Session()
        login_url='http://doridro.com/forum/ucp.php?mode=login'
        body = {'username' : '%s' %Doridro_USER,'password' : '%s' %Doridro_PASSWORD,'autologin' : '1','login' : 'login'}
        r = session.post(login_url,data = body,headers=headers)

        Cookie =  session.cookies.get_dict()      #str(r.headers['set-cookie'])
        #print r.cookies
        loged_in = check_login(r.text,'%s' %Doridro_USER)
        if loged_in == True:
            notification('Login Succes','Succesfully loged_in to doridro.Com as %s ::.'%Doridro_USER,2000)
            #return r.cookies
            pickle.dump( Cookie, open( cookie_jar, "wb" ) )
        #with open(cookie_jar,'w') as f:
           #f.write(str(Cookie))

def get_soup(url,content=None,ref=None,post=None,mobile=False,data=None):
    if not url == '' :
        if ref:
            print 'we got ref',ref
            headers.update({'Referer': '%s'%ref})
        else:
            headers.update({'Referer': '%s'%url})
        if mobile:
            headers.update({'User-Agent' : 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7'})
        req = urllib2.Request(url,None,headers)
        resp = urllib2.urlopen(req)
        content = resp.read()
        resp.close()
        if data:
            return content
    try:
        soup = BeautifulSoup(content,'html.parser')
        print 'using html.parser'
    except:
        soup = BeautifulSoup(content)


    print len(soup)

    return soup



def CATEGORIES(name):
    itemart={}
    item_info={}
    if not Doridro_USER == '' :
        _login()
        item_info["title"] = "Natok & Telefilms"
        item_info["genre"] = "Natok"
        
        addDir("Natok & Telefilms", '155',3,itemart,item_info)
        item_info["title"] = "Bangla/Bengali Movies"
        item_info["genre"] = "Bangla/Bengali Movies"
         
        addDir("Bangla Movies", '106',3,itemart,item_info)
        item_info["title"] = "Bangla/Bengali Music"
        item_info["genre"] = "Music"
        
        addDir("Music[Download ONLY]", '166',3,itemart,item_info)
        item_info["title"] = "Bangla/Bengali Music"
        item_info["genre"] = "Bangla/Bengali Music"
        
        addDir("Kolkutta Music[Download ONLY]", '192',3,itemart,item_info)
    item_info["title"] = "LiveTv"
    item_info["genre"] = "TV"
        
    addDir("Live TV", 'http://www.jagobd.com/category/bangla-channel',1,itemart,item_info)
    #addDir("Drama Serials", 'http://doridro.com/forum/viewforum.php?f=99',99,'','')

    



def LiveBanglaTV(url):
    content,new = cache(url,duration=6)
    soup = get_soup('',content=content)
    #l= soup('a' ,{'rel':"bookmark"})
    l= soup("div" ,{"class":"ancol-sm-3 col-xs-6"})
    for data in l:
        a = data("a")[0]
        url = a.get('href')
        deg(url)
        #print url
        try:
            img = a('img')[0]['src']
        except Exception:
            img = ''
        #print img
        name = data("div" ,{"class":"antitle"})[0].text
        liz=xbmcgui.ListItem(name)
        liz.setInfo( type="Video", infoLabels={ "Title": name})
        liz.setArt({ 'thumb': img, 'fanart' : img })
        liz.setIconImage(img)
        u = sys.argv[0] + '?mode=2' + '&url=' + urllib.quote_plus(url)\
            + '&name=' + urllib.quote_plus(name)
        #print u
        xbmcplugin.addDirectoryItem(handle, u, liz, True)
def playlive(url,name):
    embed_url_pat = 'http://www.tv.jagobd.com/embed.php?u={0}&vw=100%&vh=400'

    content,new = cache(url,duration=3)
    
    match = re.compile(r'''jagobd\.com/embed\.php\?u=([^&]+)''',re.DOTALL).findall(content)
    print match
    if len(match) > 1 :
        dialog = xbmcgui.Dialog()
        index = dialog.select('Choose a video source', match)
        if index >= 0:
            print 'index choosen', str(index),match[1]
            
            final_url = livetv(embed_url_pat.format(match[index]),ref=url)
        else:
            return
    else :
        final_url = livetv(embed_url_pat.format(match[0]),ref=url)
    #soup = get_soup('',content=content)
    #embed_url=soup('div', {'class':"stremb"})[0]('a')[0].get('href')
    ##embed_url=soup('area', {'shape':"rect"}).get('href')
    #print 'the embed_url',embed_url
    #if addon.getSetting('typeofstream') == 0:
    #    final_url = 'http://' + livetv(embed_url,ref=url)
    #else:
    #    final_url = livetv(embed_url,ref=url)
    #play_url = makeRequest(final_url,mobile=True,ref=url)
    if not final_url == 'None':
        listitem = xbmcgui.ListItem(name)
        listitem.setInfo(type='Video', infoLabels={'Title':name})
        xbmc.Player().play(final_url,listitem)
def livetv(embed_url,ref=None):
    token1 = '%xqdrde(nKa@#.'
    token2 = '%pwrter(nKa@#.'
    soup = get_soup(embed_url,ref=ref,data='1')
    m= re.compile(r'return\((.*?)\.join\(""\)\W+(.*?)\.join\(""\).*?getElementById\("([^"]+)').findall(soup)
    
    for i,j,z in m:
        if "[" in i:
            k= ast.literal_eval(i)
            k= "".join(k)
            if "http" in k:
                p=re.compile(j+r'\W+(\[[^\]]+]);').findall(soup)
                deg(str(p))
                pp=re.compile(z+r'>(.*?)<').findall(soup)
                deg(str(pp))
                if p and pp:
                    k= k+"".join(ast.literal_eval(p[0])) +pp[0]
                return k.replace("\\","") +'|Origin=http://tv.jagobd.com'
    else:
        return None


def removeNonAscii(s): return "".join(filter(lambda x: ord(x)<128, s))
tabsurls= {}
def make_colorful(name,new=False):
    if new:
        return "[COLOR hotpink]%s[/COLOR]" %name
    return "[COLOR skyblue]%s[/COLOR]" %name

def natok_tabs(name,tab,url,info_source_match,allsources,img,premiered):
    info=[]
    name = cleanname(name)
    try:

        content,new = cache(url,duration=0,need_cookie='login') 
        #allsources = re.compile(r'''class="postlink"\s*[href=]?.*?(https?://[^<"]+)''',re.DOTALL).findall(content)
        soup = get_soup('',content)
        l = soup('div' ,{'class':'content'})
        _exclude=["shink.com","ouo.io"]
        if l:
            for i in l:

                blockquote = i("blockquote",attrs= {"class":"uncited"})

                info=["\n"+j.text for index,j in  enumerate(blockquote) if j]
                if not info:
                    info=[name]
                imgs= i("img", attrs={"src":re.compile(r"\.jpg")})
                imgs= [img.get("src") for img in imgs if img.get("src")]
                postlinks= i("a",attrs={"class":"postlink"})
                
                postlinks= [(postlink.text,postlink.get("href")) for postlink in postlinks if not any(i in postlink.get("href","nolink") for i in _exclude) ]
                #info = "\n".join(info)
                tabsurls[str(tab)] = {"url":url,"sources":postlinks,"arts":imgs,"info":info,"name":name,"premiered":premiered}
                break
        else:
            raise
    except Exception:
        tabsurls[str(tab)] = {"name":name,"premiered":premiered}
 
        
import workers
def processthreads(threads,pDialog,timeout=10):
    for index,i in enumerate(threads):
        i.start()
        i.join()
        pDialog.update(index+10,"Remaining threads: %s" %(60-index))

        #[i.start() for i in threads]
        #timeout = timeout*2*60
        #for i in range(0, timeout ): #timeout=3600 . then 3600*.5*1/60 = 30s
        #    try:
        #        if xbmc.abortRequested == True: return sys.exit()
        #        if pDialog.iscanceled(): break
        #    except:
        #        pass            
        #    pDialog.update(30,"Please Wait %s Seconds" %str(i))
        #    is_alive = [x.is_alive() for x in threads]
        #    if all(x == False for x in is_alive)  : break
         #   time.sleep(0.5)
        #[i.join() for i in threads] #This will wait until all the processed return something independent of time
def deg(string,level=xbmc.LOGNOTICE):
        try:
            xbmc.log("[Doridro::]: %s" %str(string),level)
        except:
            traceback.print_exc()
            pass
def getpremiered(date_reg,plot):
    monthDict={'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
                        'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}    
    dateinfo = date_reg.findall(plot)
    deg(dateinfo)
    if dateinfo:
        dateinfo = dateinfo[0]
        month = dateinfo[1][:3]
    
        if month in monthDict:
            month = monthDict[month]
        else:
            month = '01'
    
        premiered=  '%s-%s-%s' %(str(dateinfo[2]),month,str(dateinfo[0])) 
    
    else:
        premiered = '1969-01-01'
    return premiered    

 
    
def createNAthread(url,pDialog):
            global tabsurls
            tabsurls={}
            threads=[]
            info_source_match = re.compile(r'<div class="content"><div class="center-block text-center"><img (.*?)</div></div>',re.IGNORECASE | re.DOTALL)
            img = re.compile(r'src="(https?[^"]+)"', re.IGNORECASE | re.DOTALL)
            allsources = re.compile(r'''class="postlink"\s*[href=]?.*?[<|"](https?://[^<"]+)''',re.DOTALL)

            date_reg=re.compile(r"\W+(\d{2})\s*(\w+)\s*(\d{4})", re.IGNORECASE | re.DOTALL)
       
            uurl = forum_url.format(url)
            content,new = cache(uurl, duration=0)
            soup = get_soup('',content=content)
            #soup = get_soup(url)
            l = soup('div' ,{'class':'desc-wrapper'})[9:70]
            #deg( "Number of titles")
            #deg( len(l))
    
            for index,i in enumerate(l):
                href=i('a' ,{'class':'topictitle'})[0]
                href1= href.get('href').split('&sid=')[0]
                name = removeNonAscii(href.text).encode('utf-8','ignore')
                tab= href1.replace('&amp;','&').replace('./','')
                url= 'http://doridro.com/forum/' + tab
                premiered=getpremiered(date_reg,i("small")[0].text)
                #natok_tabs(tab,url,info_source_match,allsources,img)
                    #deg(name)
                    #deg(tab)
                threads.append(workers.Thread(natok_tabs, name,tab,url,info_source_match,allsources,img,premiered))
            deg("#of threads")
            deg(len(threads))    
            if len(threads) >0 :
                    processthreads(threads,pDialog,timeout=30)
                    #processthreads(threads,pDialog) 
            return tabsurls

def natok(url):
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Getting ', 'Downloading may be necessary.\nPlease Wait ...')
        start=0
        if "start" in url:
            orig_url,start= url.split("&start=")
        else:
            orig_url=url
            
        #pDialog.close()
        if orig_url == "155":
           doridro_source=os.path.join(cacheDir,'doridro_source_natok.db')
        elif orig_url == "106":
           doridro_source=os.path.join(cacheDir,'doridro_source_movies.db')
        elif orig_url == "166" or orig_url == "192":
           doridro_source=os.path.join(cacheDir,'doridro_source_music.db')        
        
        #if not os.path.isfile(doridro_source):
        #
        #    with open(doridro_source,"w") as f:
        #        f.write("")
        #        #createNAthread(url,pDialog,doridro_source,update=False)
        
        #pDialog.update(50, 'Finish the source File')
        deg('Finish the source File')  
        #try:
        Update_needed = True
        dbcon = database.connect(doridro_source)
        dbcur = dbcon.cursor()

        dbcur.execute("CREATE TABLE IF NOT EXISTS up_source (url TEXT, start INTEGER ,added TEXT)")
        dbcur.execute("CREATE TABLE IF NOT EXISTS rel_src (""source TEXT, ""name TEXT, ""url TEXT, ""itemart TEXT, ""item_info TEXT, ""added TEXT, ""UNIQUE(source)"");")
        #dbcur.execute('INSERT INTO up_source(url,start,added) VALUES(?,?,?) ' , ["155",start,int(time.time())])
        #dbcur.execute('INSERT INTO up_source(url,start,added) VALUES(?,?,?) ' , ["155&start=60",60,int(time.time())])
        #dbcur.execute('INSERT INTO up_source(url,start,added) VALUES(?,?,?) ' , ["155&start=120",120,int(time.time())])
        #dbcur.execute('INSERT INTO up_source(url,start,added) VALUES(?,?,?) ' , ["155&start=180",180,int(time.time())])
        dbcur.execute("SELECT * FROM up_source WHERE url=?", [url] )
        added = dbcur.fetchone()
        if added:
            if int(time.time()) > (int(added[2]) + 5*24*60*60) and not 'start' in added[0] :
                dbcur.execute('DELETE FROM up_source WHERE url=? AND start=?' , [url,0])
                #dbcur.execute('INSERT INTO up_source(url,start,added) VALUES(?,?,?) ' , [url,start,int(time.time())])
            else:
                pDialog.update(90, 'Update Not necessary')

                start = dbcur.execute("SELECT MAX(start) FROM up_source  " )
                start = dbcur.fetchone()[0]
                dbcur.execute("SELECT * FROM rel_src  " )
                #match = dbcur.fetchone()
                oldlinks = dbcur.fetchall()
                #deg(str(tabsurls))
                dated=re.compile(r"date\W+.*?(\d{4})", re.IGNORECASE | re.DOTALL)
                for source,name,url,itemart,item_info,added in oldlinks:
                    mode = "5"
                    if not url or len(url) <1:
                        mode="53"
                        url='plugin://plugin.video.youtube/search/?q='
                        item_info["status"]="No Source found. Play from Youtube"            
                    liz=xbmcgui.ListItem(name)
                    liz.setInfo( type="Video", infoLabels=json.loads(item_info))
                    #liz.setMimeType('mkv')
                    liz.setArt(json.loads(itemart))
                    #print 'name to pass to videolinks', name
                    u = sys.argv[0] + '?mode='+mode + '&url=' + urllib.quote_plus(url)\
                        + '&name=' + urllib.quote_plus(name)
                    #print u
                    xbmcplugin.addDirectoryItem(handle, u, liz, True)
                Update_needed=False
        deg(str(Update_needed))
        if Update_needed:
            pDialog.update(10, 'Need to Update. ')
            tabsurls = createNAthread(url,pDialog)
            dbcur.execute('INSERT INTO up_source(url,start,added) VALUES(?,?,?) ' , [url,start,int(time.time())])
            for index,i in enumerate(tabsurls):
                itemart={}
                item_info={}
                mode="5"
                name= tabsurls[i]["name"]
                
                if tabsurls[i].get("sources"):
                    url= "|||".join([source for s_name,source in tabsurls[i]["sources"]])
                else:
                    mode="53"
                    url='plugin://plugin.video.youtube/search/?q='
                    item_info["status"]="No Source found. Play from Youtube"
                                    
                    
                if tabsurls[i].get("arts") :
                    itemart['thumb'] = tabsurls[i]["arts"][0]
                    try:
                        itemart['fanart']  = tabsurls[i]["arts"][1]
                    except Exception:
                        itemart['fanart']  = itemart['thumb'] 
                else:
                    itemart['thumb'] =itemart['fanart']  = os.path.join(home,'icon.png')
                
                try:
                    plot=item_info['plot']="\n".join(tabsurls[i]["info"])
#https:/    /github.com/vonH/plugin.video.iplayerwww/blob/3c5e08e845cd756a9b17a66e45882fd82b90472e/resources/lib/ipwww_video.py#L181
            
                    if "Writers" in plot:
                        director = re_me(plot,r"Writers\W+([^&]+)",flags=re.I)
                        if "File" in director:
                            director= director.split("File")[0]
                        item_info['director']=  director                
                except Exception:
                    item_info["plot"] = name
                name = cleanname(name)
                dateadded=item_info["dateadded"] =item_info["premiered"] = tabsurls[i].get("premiered")
#repr(r)        

                dbcur.execute("INSERT OR IGNORE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (i.rsplit('=',1)[1], name, url, json.dumps(itemart), json.dumps(item_info), dateadded))
                
                pDialog.update(int((index*50)/len(tabsurls)), 'Adding: %s  ...' %name)
                #name = name.split(')')[0].replace('(','')
                liz=xbmcgui.ListItem(name)
                liz.setInfo( type="Video", infoLabels=item_info)
                #liz.setMimeType('mkv')
                liz.setArt(itemart)
                #print 'name to pass to videolinks', name
                u = sys.argv[0] + '?mode='+mode + '&url=' + urllib.quote_plus(url)\
                    + '&name=' + urllib.quote_plus(name)
                #print u
                xbmcplugin.addDirectoryItem(handle, u, liz, True)
            
            



        addDir("Next Page (%s)" %str(int(int(start)/60)+2), orig_url+"&start="+str(int(start)+60),3,{},{})    
        pDialog.close()
        dbcon.commit()
        dbcon.close()
        #addDir("[COLOR yellow]Next Page > >[/COLOR]",orig_url+"&start="+str(int(start)+60),3,"","")
        #xbmcplugin.endOfDirectory(handle)
            #xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True )
def cleanname(name,keepcolor=True):
    try:
        if keepcolor:
            name = re.sub(r"(?!\[/?c)\[.*?\]","",name,flags=re.I)
        else:
            name = re.sub(r"\[.*?\]","",name)
        name = re.sub(r"\d+\s*(mb|p)","",name,flags=re.I)
        name = re.sub(r"mkv|hevc","",name,flags=re.I)
        name =re.sub(r"(web|hdtv|vcd|hd|tv|dvd|scr)(\W?rip)","",name,flags=re.I)
        name =re.sub(r"(dvd|scr|rip|hq|tv|web)","",name,flags=re.I)
        name = re.sub(r"(\d{3,4}p)","", name,flags=re.I)
        name = re.sub(r"(x\d{3})","", name,flags=re.I)
        name = re.sub(r"(\d(cd|dvd))","", name,flags=re.I)
        name = re.sub(r"\s+",r" ",name)
        name = re.sub(r"-","",name)

    except:
        pass
    return name
def re_me(data, re_patten,flags=0):
    match = ''
    m = re.search(re_patten, data,flags=flags)
    if m != None:
        match = m.group(1)
    else:
        match = ''
    return match
def solve_fileshare_url(link):
    import urlresolver
    host = urlresolver.HostedMediaFile(link)
    extracted_url = ''
    if host :
        try:
            stream_url = host.resolve()
            if stream_url and isinstance(stream_url, basestring):
                return stream_url
                #xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Urlresolver donot support this domain. - ,5000)")
                #raise Exception()
            elif stream_url and isinstance(stream_url,list):
                for k in stream_url:
                    if k['quality'] == '1080p' :
                        return k['url']                    
                    elif k['quality'] == 'HD'  :
                        return k['url']
                    elif k['quality'] == 'SD' :
                        return k['url']

        except Exception:
            pass    
    if 'indishare' in link or 'bdupload' in link:
        extracted_url = indishare(link)
    elif 'uptobox' in link:
        extracted_url = uptobox(link)
    elif 'seenupload' in link:
        extracted_url = seenupload(link,url)
    elif 'uppit' in link:
        extracted_url = uppit(link,url)
    print 'extracted_url for :', link,extracted_url
    return extracted_url

def morelinks(name,url):
    print ('Building morevideolinks')
    print url
    #net.set_cookies(cookie_jar)
    req = urllib2.Request(url)
    req.add_header('Host','doridro.com')
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
    req.add_header('Accept-Encoding','gzip, deflate')
    req.add_header('Accept','text/html, application/xhtml+xml, */*')
    req.add_header('Content-Type','application/x-www-form-urlencoded')
    req.add_header('Referer','http://doridro.com/forum/')
    resp = urllib2.urlopen(req)
    contents = resp.read()
    resp.close()

    playurl = get_match(contents,'<a href="(.*?)"')
    print playurl
    item = xbmcgui.ListItem(name)
    item.setInfo(type="Video", infoLabels={"Title": name})
    #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    playlist.add(url=playurl, listitem=item)
    if not xbmc.Player().isPlayingVideo():
         xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(playlist)

def getVideolinks(name,url):
    music = False
    if 'f=166' in url or 'f=192' in url:
        music = True
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Getting Music links', 'Please wait ...')
    else:
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Getting Video links', 'Please wait ...')    
    #return
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    domains = ['seenupload','uptobox','share.jong.li','indishare','uppit','bdupload']
    final_url = []
    tracks=[]
    allsources = [i for i in url.split("|||") if not "arabloads.net" in i]
    
    if len(allsources) >0:
        
        for i in allsources:
            if i == "YT":
                name = re.sub(r"\[.*?\]","",name)
                final_url.append('plugin://plugin.video.youtube/search/?q='+ urllib.quote_plus(name))
            #elif i == "DM" :
                
            if music :
                import urlparse
                d_name= '[' + urlparse.urlparse(i).netloc + '] ' +   urllib.unquote_plus(i.split('/')[-1])
                tracks.append(d_name)            
            elif 'share.jong.li' in i :
                extracted_url = jongli(i,ref=url)
                if extracted_url :
                    final_url.append(extracted_url)
                else:
                    continue
            elif not any(x in i for x in domains):
                
                allsources.remove(i)
            else:
                continue
        print 'url list now:::',allsources
        #deg(final_url)
        if len(final_url) >0:
            for stream in final_url:
                if not 'rar' in stream or not 'zip' in stream:
                    info = xbmcgui.ListItem('%s' %name)
                    playlist.add(stream, info)
            xbmc.Player().play(playlist)        
        
        elif len(tracks) >0 :
            dialog = xbmcgui.Dialog()
            index = dialog.select('Choose a Audio source', tracks)
            if index >= 0:
                if 'share.jong.li' in tracks[index] :
                #print 'share.jong.li found'
                    extracted_url = jongli(allsources[index],ref=url)
                else:
                    extracted_url = solve_fileshare_url(allsources[index])
                if len(extracted_url) >0:
                    down_url(extracted_url)
                
       
        else:
            #name = re.sub(r"\[.*?\]","",name)
            allsources.append('Search In Youtube') 
            deg("allsources found as list:")
            #deg(allsources)
            if len(allsources) == 1:
                    if "." in name:
                        name = cleanname(name.split(".")[1].strip(), keepcolor=False) + " bangla"           
                    url ='plugin://plugin.video.youtube/search/?q='+urllib.quote_plus(name)
          
                    xbmc.executebuiltin('Container.Update(%s,return)' %url)
                    return
            dialog = xbmcgui.Dialog()
            index = dialog.select('Choose a video source', allsources)
            
            if index >= 0:
                if  allsources[index].startswith("Search"):
                    #name2 = re.sub(r"\d\.","",name)
                    #name2 = cleanname(name2, keepcolor=False)
                    if "." in name:
                        name = cleanname(name.split(".")[1].strip(), keepcolor=False) + " bangla"
                    #listitem = xbmcgui.ListItem( name )
                    url ='plugin://plugin.video.youtube/search/?q='+urllib.quote_plus(name)
      
                    xbmc.executebuiltin('Container.Update(%s,return)' %url)

                else:
                    extracted_url = solve_fileshare_url(allsources[index])
                #if len(extracted_url) >0:
                    xbmc.Player().play(extracted_url)
        #    notification("failed to Play", "[COLOR yellow]Failed to extract video links[/COLOR]", sleep=1000)

    else:
        notification("NO Link found", "[COLOR yellow]There is no video for this link[/COLOR]", sleep=1000)
def jongli(link,ref=None):
    content,new = cache(link,duration=2,ref=url)
    #print soup
    print new
    match = re.compile(r'''<a\s*href="(\S+)">Click here to download''',re.DOTALL).findall(content)   
    print 'match found for jongli',match
    if match :
    #print len(l),l
        return match[0]
    else:
        return

def uppit(link,ref=None): #http://uppit.com/53lbeaylge7m/Bojhena_Se_Bojhena_&
    idd = link.rsplit('/',2)
    print idd
    id = idd[1]
    body = dict(method_free=' ',op="download1",usr_login=' ',id=id,fname='',referer='http://uppit.com')
    headers.update({'Referer':link,'Content-Type': 'application/x-www-form-urlencoded','Accept-Encoding': 'gzip, deflate','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    rr = requests.post(link,data=body,headers=headers)
    soup = BeautifulSoup(rr.text,'html.parser')
    print 'uppit soup',len(soup)
    l = soup('a',{'class':'m-btn big blue'})[0].get('href')
    print len(l),l
    url = urllib.quote(l,':/')
    return url

def seenupload(link,ref=None):
    main_url = 'http://seenupload.com/seenupload.html'
    s = requests.Session()

    r = s.get(link,headers=headers,verify=False,allow_redirects=True)
    #headers.update({'Cookie': r.headers['set-cookie']})

    soup = BeautifulSoup(r.text)
    #print len(soup)
    fname= soup('input',{'name': 'fname'})[0].get('value')
    #print fname
    id = link.split('/')
    id = id[-1].replace('.html','')
    body = dict(method_free=' ',op="download1",usr_login='',id=id,fname=fname,referer='')
    s.headers.update({'Referer':main_url,'Accept-Encoding': 'gzip, deflate','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    rr = s.post(main_url,data=body,headers=headers)
    soup = BeautifulSoup(rr.text,'html.parser')
    print 'seenupload soup',len(soup)
    ran_value= soup('input',{'name': 'rand'})[0].get('value')
    print ran_value
    if ran_value:
        body = dict(op="download2",id=id,down_direct='1',rand=ran_value,referer=ref)
        rrr = s.post(main_url,data=body,headers=headers,verify=False)
        soup = BeautifulSoup(rrr.text,'html.parser')
        l = soup(href=re.compile('http://88'))
        print l
        for i in l:
            url = urllib.quote(i.get('href'))
            url = url.replace('%3A',':')
            print 'playing:seenupload:',url
        return url


def cache(url, duration=0,ref=None,post=None,body={},need_cookie=None):
    if addon.getSetting('nocache') == 'true':
        duration = 0
    new = 'true'
    #url = url.encode('utf-8')
    if len(body) > 1:
        f_name_posturl = url + json.dumps(body)
        cacheFile = os.path.join(cacheDir,''.join(c for c in unicode(f_name_posturl.encode('utf-8','ignore'), 'utf-8') if c not in '/\\:?"*|<>')[:150].strip())
    else:
        cacheFile = os.path.join(cacheDir,''.join(c for c in unicode(url.encode('utf-8'), 'utf-8') if c not in '/\\:?"*|<>')[:150].strip())
    if need_cookie:
        #getcookiefile = os.path.join(cookie_jar, '%s' %need_cookie)
        with open( cookie_jar, "rb") as f:
            cookiess = pickle.load(f)
    if ref:
        headers.update({'Referer': '%s'%ref})
    if os.path.exists(cacheFile) and duration!=0 and (time.time()-os.path.getmtime(cacheFile) < 60*60*24*duration):
        fh = xbmcvfs.File(cacheFile, 'r')
        content = fh.read()
        fh.close()
        new = 'false'
        return content,new
    elif post and need_cookie:

        r = requests.post(url,data=body,cookies=cookiess,headers=headers,verify=False)
        content = r.text
    elif post:

        r = requests.post(url,data=body,headers=headers,verify=False)
        content = r.text
    elif need_cookie:
        r = requests.get(url,cookies=cookiess,headers=headers,verify=False)
        content =r.text

    else:
        #print headers
        r = requests.get(url,headers=headers,verify=False)
        content =r.text
    if not duration == 0:
        fh = xbmcvfs.File(cacheFile, 'w')
        fh.write(removeNonAscii(content).encode('utf-8'))
        fh.close()
    return content,new
def indishare(url): #limit of 120 minutes/day
    pDialog = xbmcgui.DialogProgress()
    pDialog.create('Extracting Idishare Link ......', 'Pleas wait:  ...' )
    id = url.split('/')
    id = id[-1]
    content,new = cache(url, duration=1) #cache(url, duration=0,post=None,body={},need_login=None)
    soup = get_soup('',content=content)
    WAIT_PAT = r'>(\d+)</span> seconds<'
    match = re.search(WAIT_PAT,content)
    if match:
        wait_for = match.group(1)
        pDialog.create('Extracting Idishare Link ......', 'Pleas wait for %s Seconds:  ...' %wait_for )
        count = 1
        while count <= int(wait_for) :
            xbmc.sleep(1000)
            pDialog.create('Extracting Idishare Link ......', 'Remaining time [COLOR gold]%s Seconds[/COLOR] ...' %str(int(wait_for) - count) )
            count += 1
    #id="countdown_str">Wait.*?>(\d+).*?seconds
    print 'indishare soup',len(soup)
    ran_value= soup('input',{'name': 'rand'})[0].get('value')

    body = dict(op="download2",id=id,rand=ran_value,down_script='1')
    content,new = cache(url,1,post = 'post',body=body)

    href = re.compile(r'<a\s*href="(http://[\w]+\.indi(?:file|world)s\.com[^">]+)',re.DOTALL).findall(content)[0]
    #print len(href),href
    pDialog.close()
    return href.replace(' ','%20')
def uptobox(url): #limit of 120 minutes/day # Not every link uptostream
    content,new = cache(url,duration=0.5)
    #url2 = url.replace('uptobox','uptostream')
    print len(content)
    form_values = {}
    for i in re.finditer('<input.*?name="(.*?)".*?value="(.*?)">', content):
        form_values[i.group(1)] = i.group(2)
    headers.update({'Referer':url})
    WAIT_PAT = r'>(\d+)</span> seconds<'
    content = requests.post(url,data=form_values,headers=headers)
    streamurl = re.compile(r'''DOWNLOAD\s*BUTTON.*?(https?://\w+\.uptobox\.com/d/.*?)">''',re.DOTALL).findall(content.text)[0]

    print 'playing:uptobox:',streamurl
    #streamurl = urllib.quote_plus(streamurl)
    return streamurl.replace(' ','%20')

def notification(header="", message="", sleep=3000):
    """ Will display a notification dialog with the specified header and message,
    in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i)" % ( header, message, sleep ))
def addDir(name,url,mode,itemart={},item_info={}):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)
    liz.setInfo( type="Video", infoLabels=item_info )
    liz.setArt(itemart)
    ok=xbmcplugin.addDirectoryItem(handle,url=u,listitem=liz,isFolder=True)
    return ok
def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string
def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
            string = unicode(string, encoding, 'ignore')
    return string
def removeNonAscii(s): return "".join(filter(lambda x: ord(x)<128, s))

def sendJSON( command):
    data = ''
    try:
        data = xbmc.executeJSONRPC(uni(command))
    except UnicodeEncodeError:
        data = xbmc.executeJSONRPC(ascii(command))

    return uni(data)

def pluginquerybyJSON(queryurl,method="Files.GetDirectory",give_me_result=None,addtoplaylist=False):
    #xbmc.log("playlist: %s" %url)
    #method = "GUI.ActivateWindow" #queryurl="plugin%3A%2F%2Fplugin.video.sastatv%2F%3Findex%3D4%26mode%3D10%26name%3DHindi%26origurl%3Dhttp%3A%2F%2Fsastatv.com%2Fsecured%2Fxml%2Flive-root.xml%26thumb%3Dhttp%3A%2F%2Fsastatv.com%2Fimages%2Flogo%2FSastaLive_hindi.jpg%26url%3Dhttp%3A%2F%2Fsastatv.com%2Fsecured%2Fphp%2FfetchLiveFeeds.php%3Fid%3De-hindi.xml"
    deg("searching json_query :"+queryurl)
    if  method.startswith("GUI"):
        if "ActivateWindow" in method:
            json_query = uni('{"jsonrpc":"2.0","method":"GUI.ActivateWindow","id":1,"params":{"window":"videos","parameters": ["\\"%s\\""]}}') %queryurl
        elif "ShowNotification" in method:
            json_query = uni('{"jsonrpc":"2.0","method":"GUI.ShowNotification","params":{"title":"","message":""},"id":12}') %queryurl
    
    elif method == "Input.SendText" :
        json_query = uni('{"jsonrpc":"2.0","method":"Input.SendText","params":{"text":"%s"},"id":1}') %queryurl 
    
    elif 'audio' in queryurl:
        json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params": {"directory":"%s","media":"video", "properties": ["title", "album", "artist", "duration","thumbnail", "year"]}, "id": 1}') %queryurl
    else:
        json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","media":"video","properties":[ "plot","playcount","director", "genre","votes","duration","trailer","premiered","thumbnail","title","year","dateadded","fanart","rating","season","episode","studio","mpaa"]},"id":1}') %queryurl
        
    json_folder_detail = json.loads(sendJSON(json_query))
    #deg(json_folder_detail)
    if json_folder_detail.has_key('error'):
        xbmc.executebuiltin("XBMC.Notification(BD Doridro,Plugin Json Request failed. - "+"this"+",4000,"+icon+")")
        return    
    if json_folder_detail["result"] == "OK":
        return
    else:
        total=len(json_folder_detail['result']['files'])
        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create("PlayList","Adding")        
        for i in json_folder_detail['result']['files'] :
            itemart=item_info={}
            url = i['file']
            name = removeNonAscii(i['label'])
            itemart['thumb'] = removeNonAscii(i.get('thumbnail'))
            itemart['fanart'] = removeNonAscii(i.get('fanart'))
            item_info = dict((k,v) for k, v in i.iteritems() if not v == '0' or not v == -1 or v == '')
            
            if i['filetype'] == 'file':
                    addLink(url,name,itemart,item_info,None,total)
                    #xbmc.executebuiltin("Container.SetViewMode(500)")
                    if i['type'] and i['type'] == 'tvshow' :
                        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
                    elif i['episode'] > 0 :
                        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
            else:
                #deg("dir")
                if not "plugin://" in url:
                    
                    mas = re.compile(r"[&|;]url=([^&\n\r]+)",re.IGNORECASE | re.DOTALL).findall(url)
                    url = url.replace(mas[0],urllib.quote_plus(url))
                addDir(name,url,53,itemart,item_info)
        pDialog.close()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
def addLink(url,name,itemart,item_info,regexs=None,total=1,setCookie=""):
        #print 'url,name',url,name,iconimage
        mode="12"
     
        try:
            name = name.encode('utf-8')
        except: pass
        ok = True
        isFolder=False
        u=sys.argv[0]+"?"
        playlist = item_info.get('playlist',None)
        u += "url="+urllib.quote_plus(url)+"&mode="+mode
        item_info["Title"] = name

        liz=xbmcgui.ListItem(name)
        iconimage = itemart.get('thumb')
        
        if not iconimage:
            iconimage=itemart['thumb'] = icon
        try:
            u += "&thumb="+urllib.quote_plus(iconimage)
        except: pass
        try:
            u += "&plot="+ urllib.quote_plus(item_info["plot"]) 
        except: pass
        #u += "&iconimage="+urllib.quote_plus(iconimage)        
        liz.setInfo(type="Video", infoLabels=item_info)
        liz.setArt(itemart)        
        #print 'adding',name
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total,isFolder=isFolder)

        #print 'added',name
        return ok          
def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]

        return param
params=get_params()

url=None
name=None
mode=None
iconimage=None
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass




try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass
try:
        iconimage=urllib.unquote_plus(params["iconimage"])
except:
        pass
try:
        start=urllib.unquote_plus(params["start"])
except:
        pass


if mode==None:
        #_login()
        CATEGORIES(name)
        xbmcplugin.endOfDirectory(handle)
elif mode==1:
    LiveBanglaTV(url)
    xbmcplugin.endOfDirectory(handle)

elif mode==2:
    playlive(url,name)      
elif mode==3:
    print ('gettting Natok')
    natok(url)
    xbmcplugin.endOfDirectory(handle)
elif mode==4:
    print ('gettting musiclinks')
    getVideolinks(name,url,'music')
elif mode==5:
    print ('gettting videolinks')
    getVideolinks(name,url)
    #xbmcplugin.endOfDirectory(handle)
elif mode==7:
    print ('playin')
    morelinks(name,url)    
#elif mode==106:
#    print ('gettting Movies')
#    BMovies(url)
#    xbmcplugin.endOfDirectory(handle)
elif mode==99:
    Dramaserials(url)
    xbmcplugin.endOfDirectory(handle)
elif mode==53:
    name = cleanname(name, keepcolor=False)
    pluginquerybyJSON(url+name.replace(" ", "+" ))
elif mode==6:
    print ('gettting multiplelinks')
    getmultiplelinks(url)
    xbmcplugin.endOfDirectory(handle)
elif mode==12:
        deg(url)
        if "plugin.video.youtube" in url:
            xbmc.Player().play(url)
        #if not url.startswith("plugin://plugin"):#not url.startswith("plugin://plugin.video.f4mTester") :
            #xbmc.Player().play(url)
            #else: 
                #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        
        #else:
    #        print 'Not setting setResolvedUrl'
        else:
            xbmc.executebuiltin('XBMC.RunPlugin('+url+')')    



