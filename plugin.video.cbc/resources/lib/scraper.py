# -*- coding: utf-8 -*-
# KodiAddon (CBC.ca)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import urllib2
import cookielib
import xbmcplugin
import xbmcgui
import datetime
import HTMLParser
import zlib
import sys
import xbmc
import os
import time

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


USERAGENT   = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
import bs4
from bs4 import BeautifulSoup as BS4
mainURL = 'https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/'

httpHeaders = {         'Pragma':'no-cache',
                        'Accept-Encoding':'gzip, deflate, sdch',
                        'Host':'v.watch.cbc.ca',
                        'Accept-Language':'en-US,en;q=0.8',
                        'Upgrade-Insecure-Requests' : '1',
                        'User-Agent': USERAGENT,
                        'Accept':"application/json, text/javascript, text/html,*/*",
                        'Cache-Control':'no-cache',
                        'Cookie':'AMCV_951720B3535680CB0A490D45%40AdobeOrg=793872103%7CMCIDTS%7C17031%7CMCMID%7C14784403900623197833646426667143476287%7CMCAID%7CNONE%7CMCAAMLH-1472055468%7C9%7CMCAAMB-1472055468%7Chmk_Lq6TPIBMW925SPhw3Q',
                        'Proxy-Connection':'keep-alive'
                       }


class myAddon(t1mAddon):

 def getRequest(self, url, udata=None, headers = httpHeaders, dopost = False, rmethod = None):
    self.log("getRequest URL:"+str(url))
    req = urllib2.Request(url.encode(UTF8), udata, headers)  
    if dopost == True:
       rmethod = "POST"
    if rmethod is not None: req.get_method = lambda: rmethod
    try:
      response = urllib2.urlopen(req)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         self.log("Content Encoding == gzip")
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
    except:
      page = ""
    return(page)


 def getAddonMenu(self,url,ilist):
   data = self.getRequest(mainURL,headers={})
   soup= BS4(data)('channel')
   for item in soup[0]('item'):
        infoList = {}
        itemart = {}
        link2 =  item.link
        if not link2:
            continue
        title =  item.title.text.encode("utf-8","ignore")
        infoList['genre'] = item.get('category') or item.get('clearleap:itemtype')
        #xbmc.log("cbc:title:%s" %title,#xbmc.logNOTICE)
        link2=link2.text.encode("utf-8","ignore")
        if title == 'Search':
            link2=link2.replace("search","suggest") + "?max=40&offset=0&query="

        ilist = self.addMenuItem(title,'GC', ilist, link2, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)


 def getAddonCats(self,lurl,ilist):
    if not '://' in lurl:
        lurl = mainURL + lurl   


    itemart = {}   
    infoList = {}
    if '/suggest/' in lurl:
        keyboard = xbmc.Keyboard('','Search CBC')
        keyboard.doModal()
        if not (keyboard.isConfirmed() == False):
                newStr = keyboard.getText()
                if len(newStr) == 0 :
                    return 
        lurl = lurl + qp(newStr)
    data  = self.getRequest(lurl,headers={})
    soup= BS4(data)('channel')    #[0]('item')
   #if 'media:content' in html:
    
  
    mediacontent = soup[0]('item')[0]('media:content')
    if mediacontent:
        print mediacontent
        fanart = soup[0].find("media:thumbnail",attrs={"profile":"CBC-HERO-3X"})
        if fanart :
            itemart['fanart'] =    fanart.get("url")
        genre =  soup[0]('category')
        if genre:
            
            infoList['genre'] = genre[0].text
        for item in soup[0]('item'):
                title =  item.title.text.encode("utf-8","ignore")
                nxurl = item('media:content')
                if nxurl :
                    nxurl =  nxurl[0].get('url')
                else:
                    continue
                thumb = item("media:thumbnail",attrs={"profile":"CBC-POSTER-2X"})
                if thumb:
                   itemart['thumb'] = thumb[0].get("url")
                plot = item.description
                if plot:
                    try:    infoList['Plot'] = h.unescape(plot.text.encode('utf-8'))
                    except: infoList['Plot'] = h.unescape(plot.text)
                infoList['TVShowTitle'] = item('clearleap:series')[0].text or title
                infoList['Title'] = title
                try:
                    #infoList['tagline'] = item('clearleap:shorttitle')[0].text or ''
                    infoList['season'] = int(item('clearleap:season')[0].text) 
                    infoList['episode'] = int(item('clearleap:episodeinseason')[0].text)
                except:
                    pass
                
                credit = item('media:credit')
                try:
                    for cc in credit:
                        if cc.get('role') == 'year':
                            infoList['year'] =  cc.text
                        if cc.get('role') == 'actor':
                            infoList['actor'] = cc.text
                except:
                    pass
                ilist = self.addMenuItem(title,'GV', ilist, nxurl, itemart.get('thumb',""), itemart.get('fanart',""), infoList, isFolder=False)
    else:
        for item in soup[0]('item'):
            title =  item.title.text.encode("utf-8","ignore")
            shortcuttoguid =  item('clearleap:shortcuttoguid')
            if shortcuttoguid:
                guid = shortcuttoguid[0].text
            elif item.guid:
                guid = item.guid.text
            else:
                
                #xbmc.log("No guid found for :%s" %title, level=#xbmc.logNOTICE)
                continue
            nxurl = "%s%s" %('https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/',guid)
            thumb = item("media:thumbnail",attrs={"profile":"CBC-HERO-3X"})
            if thumb:
                itemart['thumb'] = itemart['fanart'] = thumb[-1].get('url')
            plot = item.description
            if plot:
                try:    infoList['Plot'] = h.unescape(plot.text.encode('utf-8'))
                except: infoList['Plot'] = h.unescape(plot.text)            

            if title == "All" :
                ilist = self.addMenuItem(title,"GC",ilist,nxurl+"?offset=0&max=30", itemart.get("thumb",""), itemart.get("fanart",""), infoList,isFolder=True)
                continue
            ilist = self.addMenuItem(title,"GC",ilist,nxurl, itemart.get("thumb",""), itemart.get("fanart",""), infoList,isFolder=True)
        if  "?offset=" in lurl:
            import urlparse
            path = dict(urlparse.parse_qsl(lurl.split('?',1)[1]))
            lurl =lurl.split('?',1)[0] + "?offset=" +str(int(path.get('offset')) +30) + "&max=30"
            ilist = self.addMenuItem(title,"GC",ilist,lurl, itemart.get("thumb",""), itemart.get("fanart",""), infoList,isFolder=True)
    return(ilist)

  

 def getAddonShows(self,url,ilist):
   return(ilist)


 def getAddonEpisodes(self,url,ilist):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   self.defaultVidStream['width']  = 960
   self.defaultVidStream['height'] = 540

   url   = uqp(url)
   geurl, sname = url.split('|',1)
   geurl = urllib.quote(geurl)
   geurl = geurl.replace('%3A',':',1)
   meta = self.getAddonMeta()
   try:    i = len(meta[sname])
   except: meta[sname]={}
   html  = self.getRequest('http://www.cbc.ca%s' % geurl)
   html  = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html).group(1)
   if '<li class="active">' in html:
        return(self.getAddonShows(url, ilist))

   epis  = re.compile('<a href="(.+?)" aria-label="(.+?)".+?src="(.+?)".+?</a', re.DOTALL).findall(html)
   numShows = len(epis)
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, self.localLang(30101))
   pDialog.update(0)
   dirty = False
   for i,(url,name,img) in list(enumerate(epis, start=1)):
     name = name.decode('utf-8','replace')
     try:
         (name, img, infoList) = meta[sname][url] 
     except:
         infoList={}
         try:
            html = self.getRequest(url)
            try:
                plot = re.compile('<meta name="description" content="(.+?)"', re.DOTALL).search(html).group(1)
            except:
                plot = name
         except: plot=name
         infoList['TVShowTitle'] = sname
         infoList['Title'] = name
         try:    infoList['Plot'] = h.unescape(plot.decode('utf-8'))
         except: infoList['Plot'] = h.unescape(plot)

         meta[sname][url] = (name, img, infoList)
         dirty = True

     fanart = img
     ilist = self.addMenuItem(name,'GV', ilist, url, img, fanart, infoList, isFolder=False)
     pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)



 def getProxyRequest(self, url):
    USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
    headers = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 
    if (self.addon.getSetting('us_proxy_enable') == 'true'):
       us_proxy = 'http://%s:%s' % (self.addon.getSetting('us_proxy'), self.addon.getSetting('us_proxy_port'))
       proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
       if self.addon.getSetting('us_proxy_pass') <> '' and self.addon.getSetting('us_proxy_user') <> '':
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, us_proxy, self.addon.getSetting('us_proxy_user'), self.addon.getSetting('us_proxy_pass'))
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
       else:
            opener = urllib2.build_opener(proxy_handler)
    else:
       opener = urllib2.build_opener()
    urllib2.install_opener(opener)
    req = urllib2.Request(url.encode(UTF8), None, headers)
    try:
       response = urllib2.urlopen(req, timeout=120)
       page = response.read()
       if response.info().getheader('Content-Encoding') == 'gzip':
           page = zlib.decompress(page, zlib.MAX_WBITS + 16)

    except urllib2.URLError, e:
       xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (self.addonName, e , 5000) )
       page = ""
    return(page)

 def checkfile(self,timecheckofafile,timeforfileinsec):
        _time_limit = time.time() - int(timeforfileinsec)
        if os.path.isfile(timecheckofafile):
            
            

            if os.stat(timecheckofafile).st_mtime < _time_limit:
                xbmcvfs.delete(timecheckofafile)        
        if os.path.isfile(timecheckofafile):
            
            return True
        else:
            return False
 def getAddonVideo(self,lurl):
    profile = self.addon.getAddonInfo('profile').decode(UTF8)
    pdir  = xbmc.translatePath(profile).decode(UTF8)
    if not os.path.isdir(pdir):
        os.makedirs(pdir)
    tokenfile = xbmc.translatePath(os.path.join(profile, 'request_api_deviceid_token_CBC.ca')).decode(UTF8)
    if self.checkfile(tokenfile,24*2*60*60):
        data = open(tokenfile).read().split('\n')
        deviceId = data[0]
        deviceToken = data[1]
    else:    
        body = """<device><type>web</type></device>"""
        headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-GB,en;q=0.5","Accept-Encoding": "gzip, deflate, br","Content-Type": "application/xml","Referer": "http://watch.cbc.ca/the-nature-of-things/season-54/episode-9/38e815a-00918982176"}
        responseText = self.getRequest("https://api-cbc.cloud.clearleap.com/cloffice/client/device/register",udata=body,headers=headers,dopost=True)
        #xbmc.log("[addon.live.cbcplayertest-%s]: %s" %('responseText', str(responseText)),#xbmc.logNOTICE)

        try:
            deviceId = re.compile(r'<deviceId>(.+?)<',re.DOTALL).findall(responseText)[0]
            #xbmc.log("[addon.live.cbcplayertest-%s]: %s" %('', str(deviceId)),#xbmc.logNOTICE)
            deviceToken = re.compile(r'<deviceToken>(.+?)<',re.DOTALL).findall(responseText)[0]
            #xbmc.log("[addon.live.cbcplayertest-%s]: %s" %('', str(deviceToken)),#xbmc.logNOTICE)
            with open(tokenfile, 'w') as outfile: #SAVE TOKEN FOR A DAY
                outfile.write(deviceId+'\n'+deviceToken+'\n')
        except:
            #xbmc.log("[addon.live.cbcplayertest-%s]: %s" %('No deviceId or token found', 'Abortingg!!!'),#xbmc.logNOTICE)  
            return
    responseText=self.request_api_cbc_cloud_clearleap_com(lurl,deviceId,deviceToken)
    url = re.compile(r'<url>(.+?)<',re.DOTALL).findall(responseText)[0] 
    u = url.strip()
    liz = xbmcgui.ListItem(path=u)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)        
    
 def request_api_cbc_cloud_clearleap_com(self,url,deviceId,deviceToken):
    response = None

    try:
        req = urllib2.Request(url)

        req.add_header("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4")
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        req.add_header("Accept-Language", "en-GB,en;q=0.5")
        req.add_header("Accept-Encoding", "gzip, deflate, br")
        req.add_header("X-Clearleap-DeviceId", deviceId)
        req.add_header("X-Clearleap-DeviceToken", deviceToken)
        req.add_header("Referer", "http://watch.cbc.ca/the-nature-of-things/season-54/episode-9/38e815a-00918982176")
        req.add_header("Origin", "http://watch.cbc.ca")

        response = urllib2.urlopen(req)
        page = response.read()
        if response.info().getheader('Content-Encoding') == 'gzip':
             self.log("Content Encoding == gzip")
             page = zlib.decompress(page, zlib.MAX_WBITS + 16)        
        
    except urllib2.URLError, e:
        page =""

    return (page)
