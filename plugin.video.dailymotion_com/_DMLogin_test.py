import bs4
import requests
import urllib
#import urllib2
#import xbmcvfs
import os,re
import xbmc,xbmcaddon
dmApiUrl = "https://api.dailymotion.com/%s%s%s?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=%s&%s" 
print dmApiUrl %("","","videos","recent",'bbbbbbbbbbbbbbbbbbbbbbbbbbb')
#import json
#import datetime
#addon = xbmcaddon.Addon('plugin.video.dailymotion_com')
#profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
#saved_cookie_file = os.path.join(profile, 'DM_login_cookie')
headers=dict({"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-GB,en;q=0.5","Accept-Encoding": "gzip, deflate, br","X-Requested-With" :"XMLHttpRequest","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Referer": "http://www.dailymotion.com/ca-en"})
#U = addon.getSetting('username')
#P = addon.getSetting('pass')
import cPickle as pickle
def yoursubscription(data):
    '''<a href="http://www.dailymotion.com/musicworldnetwork" class="js-track"><img src="http://s1.dmcdn.net/HpMOc/80x80-QG7.jpg" class="channel-avatar brd-rad-md" /></a>'''
    #url = "http://www.dailymotion.com/subscriptions/kalaphar/1"
    #data = getUrl2(url)
    #data = open("Fiddler_1-41-27.htm").read()
    from bs4 import BeautifulSoup as BS
    #soup = BS(data,'html.parser')("div", {"id":"content"})
    soup = BS(data,'html.parser')("div", {"class":"sd_user_channelbox brd-rad-md col-4 mrg-btm-xl"})
    print len(soup)
    
    for items in soup:
        print type(items)
        item_info = items("div", {"class":"font-sm mrg-btm-md mrg-top-md foreground2 counters"})
        if item_info:
            print "item_info"
            print item_info[0]("a",{"class":"alt-link"})[0].text
            print item_info[0]("a",{"class":"alt-link"})[0].text
        url_class = items("a",{"class":"js-track"})
        if url_class:
            print "url_class"
            url = url_class[0].get("href")
            print url
            
            print url_class[0]('img')[0].get("src")

login_url = "http://www.dailymotion.com/pageitem/authenticationForm?request=%2Fsignin"
def checkfile(saved_cookie_file,timeforfileinsec=24*2*3600):
        _time_limit = time.time() - int(timeforfileinsec)
        if os.path.isfile(saved_cookie_file):
            #xbmcvfs.Stat(filename).st_mtime()
            #xbmcvfs.File(filename).size()
            if os.stat(saved_cookie_file).st_mtime < _time_limit:
                xbmcvfs.delete(saved_cookie_file)        
        if os.path.isfile(saved_cookie_file) and os.path.getsize(saved_cookie_file) > 5:
            return True
        else:
            return False
def notification(header="", message="", sleep=3000):
    """ Will display a notification dialog with the specified header and message,
    in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i)" % ( header, message, sleep ))
#r = requests.post(url,data=body,cookies=cookiess,headers=headers,verify=False)
def your_subscriptions():
    url = "http://www.dailymotion.com/subscriptions/kalaphar/1"
    #cookiess = _login()
    #r=requests.get(url,cookies=cookiess,headers=headers)
    r=requests.get(url,headers=headers)
    yoursubscription(r.text)
#your_subscriptions()
def _login():
    if U == '' :
        notification(header="Add Email and Password", message="Please enter Dailymotion.com login info and then try again", sleep=3000)
        addon.openSettings()
        
        if U == '':
            return
        else:
            U = addon.getSetting('username')
            P = addon.getSetting('pass')
    if checkfile(saved_cookie_file,timeforfileinsec=24*2*3600):
            with open( saved_cookie_file, "rb") as f:
                cookiess = pickle.load(f)
                return cookiess
    else:
        session = requests.Session()
        rawbody = "form_name=dm_pageitem_authenticationform&_csrf={0}&_fid=&username={1}&authChoice=login&password={2}&from_request=%2Fsignin" # b/c fiddler
        r=session.get("http://www.dailymotion.com/signin",headers=headers)
        _csrf = re.compile(r'(?<=<input).+?id="_csrf".+?value="([^"]+)',re.DOTALL).findall(r.text)
        print '_csrf' + str(_csrf)
        if _csrf:
            body = rawbody.format(_csrf[0],U,P)
            body = dict((k,v) for k,v in [item.split("=")for item in body.split('&')])
            r = session.post(login_url,data = body,headers=headers)

            Cookie =  session.cookies.get_dict()      #str(r.headers['set-cookie'])
            print Cookie
            print r.text
        if re.search(r'Welcome back',r.text,re.I):
            notification('Login Succes','Succesfully loged_in to dailymotion.Com as %s ::.'%U,2000)
            #return r.cookies
            print 'Welcome back'
            pickle.dump( Cookie, open( saved_cookie_file, "wb" ) )
            return cookie
#_login()
#_csrf = u'''z2VV1oEAcMJBU8IU4NADR2KzFymd1plMzrV5M7W-TDU'''
#print type(_csrf),_csrf
#rawbody = "form_name=dm_pageitem_authenticationform&_csrf={0}&_fid=&username={1}&authChoice=login&password={2}&from_request=%2Fsignin"
#body = rawbody.format(_csrf,urllib.quote_plus(U),P)
#print body
#body = dict((k,v) for k,v in [item.split("=")for item in body.split('&')])
#print body