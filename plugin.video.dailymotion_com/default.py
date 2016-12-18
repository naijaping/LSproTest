#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import urllib
import urllib2
import xbmcplugin
import xbmcaddon
import xbmcgui
import sys
import os
import re
import json
import base64
import datetime
import unicodedata
import SimpleDownloader
import requests
import pickle
from operator import itemgetter
familyFilter = "1"
socket.setdefaulttimeout(60)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
channelFavsFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")
familyFilterFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/family_filter_off")
cookie_file = xbmc.translatePath("special://profile/addon_data/"+addonID+"/cookies")
if os.path.exists(familyFilterFile):
    familyFilter = "0"

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
    addon.openSettings()
#allowed values are (recent, visited, visited-hour, visited-today, visited-week, visited-month, commented, commented-hour, commented-today, commented-week, commented-month, relevance, random, ranking, trending, old, live-audience) for `sort'
forceViewModeNew = addon.getSetting("forceViewModeNew") == "true"
viewModeNew = str(addon.getSetting("viewModeNew"))
maxVideoQuality = addon.getSetting("maxVideoQuality")
downloadDir = addon.getSetting("downloadDir")
qual = ["480p", "720p", "1080p"]
maxVideoQuality = qual[int(maxVideoQuality)]
language = addon.getSetting("language")
languages = ["en_EN", "ar_ES", "au_EN", "be_FR", "be_NL", "br_PT", "ca_EN", "ca_FR", "de_DE", "es_ES", "es_CA", "gr_EL", "fr_FR", "in_EN", "ie_EN", "it_IT", "mx_ES", "ma_FR", "nl_NL", "at_DE", "pl_PL", "pt_PT", "ru_RU", "ro_RO", "ch_FR", "ch_DE", "ch_IT", "tn_FR", "tr_TR", "en_GB", "en_US", "vn_VI", "jp_JP", "cn_ZH"]
language = languages[int(language)]
dmUser = addon.getSetting("dmUser")
itemsPerPage = addon.getSetting("itemsPerPage")
itemsPage = ["25", "50", "75", "100"]
itemsPerPage = itemsPage[int(itemsPerPage)]
urlMain = "https://api.dailymotion.com"
sort_result_by = ["popular","recent","visited-hour","relevance", "alphaAZFullname", "random", "activity"] #rated-month
fields = ["id", "item_type", "name", "slug", "description", "created_time", "updated_time"]
urlfields="fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total"
dmApiUrl = "https://api.dailymotion.com/%s%s%s?%s&sort=%s&%s" 
dmApiUserUrl = "https://api.dailymotion.com/%s%s%s?sort=%s&%s&%s" 

other_part_OF_url =    "limit=%s&family_filter=%s&localization=%s&page=1" %(itemsPerPage,familyFilter,language)
def index():
    if dmUser:
        addDir(translation(30034), "", "personalMain", "")
    else:
        addFavDir(translation(30024), "", "favouriteUsers", "")
    addDir(translation(30006), "", 'listChannels', "")
    addDir(translation(30007), "", 'sortUsers1', "")
    #addDir(translation(30042), "ALL", 'listGroups', "")
    addDir(translation(30002), "", 'search', "")
    addDir(translation(30003), urlMain+"/videos?fields=id,thumbnail_large_url%2Ctitle%2Cviews_last_hour&filters=live&sort=visited-hour&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listLive', "")
    addDir(translation(30039), '3D:ALL', 'sortVideos1', '', '')
    xbmcplugin.endOfDirectory(pluginhandle)


def personalMain():
    addDir(translation(30041), dmApiUserUrl %("user/",dmUser,"/videos","recent",urlfields,other_part_OF_url), 'listVideos', "")
    addDir("Channel You Follow", dmApiUserUrl %("user/",dmUser,"/following","popular","fields=avatar_720_url,description,id,status,updated_time,username,videos_total,views_total", other_part_OF_url), 'listUsers', "")
    addDir(translation(30036), dmApiUserUrl % ("user/",dmUser,"/subscriptions","recent",urlfields,other_part_OF_url), 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listUserPlaylists(url):
    content = getUrl(url)
    content = json.loads(content)
    for item in content['list']:
        id = item['id']
        title = item['name'].encode('utf-8')
        vids = item['videos_total']
        addDir(title+" ("+str(vids)+")", urllib.quote_plus(str(id)+"_"+dmUser+"_"+title), 'showPlaylist', '')
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage+1
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listUserPlaylists', "")
    xbmcplugin.endOfDirectory(pluginhandle)

def channel_you_follow(url):
    content = getUrl(url)
    content = json.loads(content)
    for item in content['list']:
        id = item['id']
        title = item.get('name') or item.get('username').encode('utf-8')
        desc = item['description'].encode('utf-8')
        addDir(title, "group:"+id, 'sortVideos1', '', desc)
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage+1
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listGroups', "")
    xbmcplugin.endOfDirectory(pluginhandle)    
def listGroups(url):
    if url == "ALL":
        url = dmApiUrl % ("","","groups","popular","",other_part_OF_url)
    content = getUrl(url)
    content = json.loads(content)
    for item in content['list']:
        id = item['id']
        title = item['name'].encode('utf-8')
        desc = item['description'].encode('utf-8')
        addDir(title, "group:"+id, 'sortVideos1', '', desc)
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage+1
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listGroups', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def showPlaylist(id):
    url = urlMain+"/playlist/"+id+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    listVideos(url)


def favouriteUsers():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(channelFavsFile):
        fh = open(channelFavsFile, 'r')
        content = fh.read()
        match = re.compile('###USER###=(.+?)###THUMB###=(.*?)###END###', re.DOTALL).findall(content)
        for user, thumb in match:
            addUserFavDir(user, 'owner:'+user, 'sortVideos1', thumb)
        fh.close()
    xbmcplugin.endOfDirectory(pluginhandle)


def listChannels():
    url = dmApiUrl % ("","","channels","","popular",other_part_OF_url)
    #xbmc.log(url,xbmc.LOGNOTICE)
    content = getUrl(url.replace("&sort","sort"))
    content = json.loads(content)
    for item in content['list']:
        id = item['id']
        title = item['name'].encode('utf-8')
        desc = item['description'].encode('utf-8')
        addDir(title, 'channel:'+id, 'sortVideos1', '', desc)
    xbmcplugin.endOfDirectory(pluginhandle)

def sortVideos1(url):
    type = url[:url.find(":")]
    id = url[url.find(":")+1:]

    if type == "3D":
        url = urlMain+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&filters=3d&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    elif type == "group":
        url = urlMain+"/group/"+id+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"

#sort_result_by = ["popular","recent","visited-hour","relevance", "alphaAZFullname", "random", "activity"]
    else:
        url = urlMain+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&"+type+"="+id+"&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    addDir(translation(30008), url, 'listVideos', "")
    addDir("Trending", url.replace("sort=recent", "sort=trending"), 'listVideos', "")


    addDir('Visited', url.replace("sort=recent", "sort=visited"), 'sortVideos2', "")
    #addDir('Commented', url.replace("sort=recent", "sort=commented"), 'sortVideos2', "")

    if type == "owner":
        addDir("- "+translation(30038), urlMain+"/user/"+id+"/playlists?fields=id,name,videos_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listUserPlaylists', "")

    xbmcplugin.endOfDirectory(pluginhandle)


def sortVideos2(url): #works
    #":"Unrecognized value (commented), allowed values are (recent, visited, visited-hour, visited-today, visited-week, visited-month, relevance, random, ranking, trending, old, live-audience) for `sort' 
    if "sort=visited" in url:
        addDir("Within Last Hour", url.replace("sort=visited", "sort=visited-hour"), "listVideos", "")
        addDir(translation(30011), url.replace("sort=visited", "sort=visited-today"), "listVideos", "")
        addDir(translation(30012), url.replace("sort=visited", "sort=visited-week"), "listVideos", "")
        addDir(translation(30013), url.replace("sort=visited", "sort=visited-month"), "listVideos", "")
   #if "sort=commented" in url:
   #    addDir("Best commented in last hour", url.replace("sort=commented", "sort=commented-hour"), "listVideos", "")
   #    addDir(translation(30011), url.replace("sort=commented", "sort=commented-today"), "listVideos", "")
   #    addDir(translation(30012), url.replace("sort=commented", "sort=commented-week"), "listVideos", "")
   #    addDir(translation(30013), url.replace("sort=commented", "sort=commented-month"), "listVideos", "")    
    addDir(translation(30014), url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def sortUsers1():
    #allowed values are (mostpopular, recommended, official, creative, premium, promoted-on-games)
    url = urlMain+"/users?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    addDir(translation(30040), url, 'sortUsers2', "")
    addDir("Recommended", url+"&filters=recommended", 'sortUsers2', "")
    addDir("Premium", url+"&filters=premium", 'sortUsers2', "")
    addDir("promoted-on-games", url+"&filters=promoted-on-games", 'sortUsers2', "")
    addDir(translation(30017), url+"&filters=official", 'sortUsers2', "")
    addDir(translation(30018), url+"&filters=creative", 'sortUsers2', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def sortUsers2(url):
    #are (relevance, popular, alphaAZFullname, random, activity) 
    addDir(translation(30019), url, 'listUsers', "")
    addDir("Featured user activity", url.replace("sort=popular", "sort=activity"), 'listUsers', "")
    addDir("Featured A to Z", url.replace("sort=popular", "sort=alphaAZFullname"), 'listUsers', "")
    xbmcplugin.endOfDirectory(pluginhandle)

def debug(st, func=' ',linenum=' '):
    xbmc.log(func+'LINE#:'+linenum+str(st),xbmc.LOGNOTICE)
def listVideos(url):
    dmUser = None
    if not '://' in url:
        dmUser = url.split(":",1)[1]
        #debug(dmUser)
        url = dmApiUserUrl %("user/",dmUser,"/videos","recent",urlfields,other_part_OF_url)
        #debug(url)
        #url =  dmUserURL %(urlMain,url.split(":",1)[1],itemsPerPage,familyFilter,language)
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(url)
    content = json.loads(content)
    count = 1
    for item in content['list']:
        id = item['id']
        
        title = item['title'].encode('utf-8')
        desc = item['description'].encode('utf-8')
        duration = item['duration']
        user = item['owner.username']
        date = item['taken_time']
        thumb = item['thumbnail_large_url']
        views = item['views_total']
        xbmcduration = str(int(duration)/60+1)
        try:
            date = datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')
        except:
            date = ""
        temp = ("User: "+user+"  |  "+str(views)+" Views  |  "+date).encode('utf-8')
        try:
            desc = temp+"\n"+desc
        except:
            desc = ""
        debug(id)
        if user == "hulu":
            pass
        elif user == "cracklemovies":
            pass
        elif user == "ARTEplus7":
            addLink(title, id, 'playArte', thumb.replace("\\", ""), user, desc, xbmcduration, date, count,views)
            count+=1
        elif duration == 0:
            addLink(title, id, 'playLiveVideo', thumb.replace("\\", ""), user, desc, xbmcduration, date, count,views)
            count+=1
        else:
            addLink(title, id, 'playVideo', thumb.replace("\\", ""), user, desc, xbmcduration, date, count,views)
            count+=1
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage+1
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listVideos', "")
    if dmUser:
        addDir("Channel %s Follow" %dmUser, dmApiUserUrl %("user/",dmUser,"/following","popular","fields=avatar_720_url,description,id,status,updated_time,username,videos_total,views_total", other_part_OF_url), 'listUsers', "")
        addDir(translation(30036), dmApiUserUrl % ("user/",dmUser,"/subscriptions","recent",urlfields,other_part_OF_url), 'listVideos', "")    
    if forceViewModeNew:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNew+')')
        
    xbmcplugin.endOfDirectory(pluginhandle)


def listUsers(url):
    content = getUrl(url)
    content = json.loads(content)
    for item in content['list']:
        owner = item['username'].encode('utf-8')
        thumb = item.get('avatar_large_url') or item.get('avatar_720_url')
        videos = item['videos_total']
        if videos == 0:
            continue
        views = item.get('views_total')
        try:
            user = "%s [COLOR magenta]Videos[%s][/COLOR]" %(owner,str(videos))
        except:
            pass
        addUserDir(user, 'owner:'+owner, 'sortVideos1', thumb.replace("\\", ""), str(views),str(videos))
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage+1
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listUsers', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listLive(url):
    content = getUrl(url)
    content = json.loads(content)
    for item in content['list']:
        title = item['title'].encode('utf-8')
        id = item['id']
        thumb = item['thumbnail_large_url']
        views = item['views_last_hour']
        addLiveLink(title, id, 'playLiveVideo', thumb.replace("\\", ""), views)
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage+1
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listLive', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewModeNew:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNew+')')


def search():
    keyboard = xbmc.Keyboard('', translation(30002))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos(urlMain+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&search="+search_string+"&sort=relevance&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1")
        xbmcplugin.endOfDirectory(pluginhandle)


def playVideo(id,live=False):
    if live:
        url=getStreamUrl(id,live=True)
    else:
        url = getStreamUrl(id)
    print url
    if url and not '.f4mTester' in url:
        #print 'path found to beeeeeeeeeeee' , url
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)    

    elif url:
        xbmc.executebuiltin('XBMC.RunPlugin('+url+')')
    else:
        print 'No playable url found'

def BW_choice(stream):
    bandwidth =[]
    if re.search('BANDWIDTH', stream) :
        print 'Getting bandwidth'
        needle = "BANDWIDTH=(\d+)\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)"
        bw_url = re.compile(needle,re.DOTALL|re.IGNORECASE).findall(stream)
    elif re.search('RESOLUTION', stream):
        needle = 'RESOLUTION=(\d+)x\d{3}[^\n]*\W+([^\n]+.m3u8[^\n\r]*)'
        bw_url = re.compile(needle).findall(stream)
    if bw_url :
        newlist =  sorted(bw_url, key=itemgetter(0),reverse=True)
        return newlist[0] [1].split('#cell')[0]
def getStreamUrl(id,live=False):
    if familyFilter == "1":
        ff = "on"
    else:
        ff = "off"
    print 'The url is ::',url
    headers = {'User-Agent':'Android'}
    cookie = {'Cookie':"lang="+language+"; family_filter="+ff}
    r = requests.get("http://www.dailymotion.com/player/metadata/video/"+id,headers=headers,cookies=cookie)
    content = r.json()
    if content.get('error') is not None:
        Error = 'DailyMotion Says:[COLOR yellow]%s[/COLOR]' %(content['error']['title'])
        xbmc.executebuiltin('XBMC.Notification(Info:,'+ Error +' ,3000)')
        return
    else:

        cc= content['qualities']
        #xbmc.log(str(cc),xbmc.LOGNOTICE)
        if not live:
            xbmc.log('Not LIVE',xbmc.LOGNOTICE)#['380'][0]['url']
            #try:
             # 0 is x-mpeg dont work w/ kodi
            if cc.get('1080'):
                try:
                    url1080 = cc.get('1080')[1].get('url')
                    rr = requests.head(url1080,allow_redirects=True)
                    if not rr.headers.get('Content-Length') == '0' :
                        return url1080
                except:
                    pass
            
            if cc.get('720') :
            #ept Exception:
                try:
                    url1080 = cc.get('720')[1].get('url')
                    #xbmc.log('720: '+ str(url1080),xbmc.LOGNOTICE)
                    rr = requests.head(url1080,allow_redirects=True)
                    if not rr.headers.get('Content-Length') == '0'  :
                        #xbmc.log('720: HEAD Request found',xbmc.LOGNOTICE)
                        return url1080
                except:
                    pass
            if cc.get('480'):
                #xbmc.log('480 found : '+ str(cc.get('480')[1].get('url')),xbmc.LOGNOTICE)
                return cc.get('480')[1].get('url')
            if cc.get('380'):
                #xbmc.log('380 found : '+ str(cc.get('380')[1].get('url')),xbmc.LOGNOTICE)
                return cc.get('380')[1].get('url')
                
            
            
            try:
                return cc.get('240')[1].get('url')
            except:
                 return cc.get('auto')[1].get('url')
            #except Exception:
            #    pass
        else:
            m_url = cc.get('auto')[0].get('url')
            if m_url and '.m3u8?auth' in m_url:
                m_url = m_url.split('?auth=')
                the_url = m_url[0] + '?redirect=0&auth=' + urllib.quote(m_url[1])
                rr = requests.get(the_url,cookies=r.cookies.get_dict() ,headers=headers)
                if rr.headers.get('set-cookie'):
                    return rr.text.split('#cell')[0]+'|Cookie='+rr.headers['set-cookie']
                else:
                    return rr.text.split('#cell')[0]        
             
      


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def downloadVideo(id):
    downloader = SimpleDownloader.SimpleDownloader()
    content = getUrl2("http://www.dailymotion.com/embed/video/"+id)
    match = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)
    global downloadDir
    while not downloadDir:
        xbmc.executebuiltin('XBMC.Notification(Download:,'+translation(30110)+'!,5000)')
        addon.openSettings()
        downloadDir = addon.getSetting("downloadDir")
    url = getStreamUrl(id)
    filename = ""
    try:
        filename = (''.join(c for c in unicode(match[0], 'utf-8') if c not in '/\\:?"*|<>')).strip()
    except:
        filename = id
    filename+=".mp4"
    if not os.path.exists(os.path.join(downloadDir, filename)):
        params = { "url": url, "download_path": downloadDir }
        downloader.download(filename, params)
    else:
        xbmc.executebuiltin('XBMC.Notification(Download:,'+translation(30109)+'!,5000)')


def playArte(id):
    try:
        content = getUrl("http://www.dailymotion.com/video/"+id)
        match = re.compile('<a class="link" href="http://videos.arte.tv/(.+?)/videos/(.+?).html">', re.DOTALL).findall(content)
        lang = match[0][0]
        vid = match[0][1]
        url = "http://videos.arte.tv/"+lang+"/do_delegate/videos/"+vid+",view,asPlayerXml.xml"
        content = getUrl(url)
        match = re.compile('<video lang="'+lang+'" ref="(.+?)"', re.DOTALL).findall(content)
        url = match[0]
        content = getUrl(url)
        match1 = re.compile('<url quality="hd">(.+?)</url>', re.DOTALL).findall(content)
        match2 = re.compile('<url quality="sd">(.+?)</url>', re.DOTALL).findall(content)
        urlNew = ""
        if match1:
            urlNew = match1[0]
        elif match2:
            urlNew = match2[0]
        urlNew = urlNew.replace("MP4:", "mp4:")
        base = urlNew[:urlNew.find("mp4:")]
        playpath = urlNew[urlNew.find("mp4:"):]
        listitem = xbmcgui.ListItem(path=base+" playpath="+playpath+" swfVfy=1 swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_24-3188338-data-5168030.swf")
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    except:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30022)+' (Arte)!,5000)')


def addFav():
    keyboard = xbmc.Keyboard('', translation(30033))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        user = keyboard.getText()
        channelEntry = "###USER###="+user+"###THUMB###=###END###"
        if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(channelFavsFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
        xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30030)+'!,5000)')


def favourites(param):
    mode = param[param.find("###MODE###=")+11:]
    mode = mode[:mode.find("###")]
    channelEntry = param[param.find("###USER###="):]
    if mode == "ADD":
        if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(channelFavsFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
        xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30030)+'!,5000)')
    elif mode == "REMOVE":
        refresh = param[param.find("###REFRESH###=")+14:]
        refresh = refresh[:refresh.find("###USER###=")]
        fh = open(channelFavsFile, 'r')
        content = fh.read()
        fh.close()
        entry = content[content.find(channelEntry):]
        fh = open(channelFavsFile, 'w')
        fh.write(content.replace(channelEntry+"\n", ""))
        fh.close()
        if refresh == "TRUE":
            xbmc.executebuiltin("Container.Refresh")


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Android')
    #req.add_header('Accept:', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    #req.add_header('Accept-Encoding:', 'gzip, deflate')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def getUrl2(url):
    if familyFilter == "1":
        ff = "on"
    else:
        ff = "off"
    print 'The url is ::',url
    headers = {'User-Agent':'Android'}
    cookie = {'Cookie':"lang="+language+"; family_filter="+ff}
    r = requests.get(url,headers=headers,cookies=cookie)
    return r.text

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, user, desc, duration, date, nr,views):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Aired": date, "Duration": duration, "Episode": nr,"playcount": views})
    liz.setProperty('IsPlayable', 'true')
    entries = []
    entries.append((translation(30044), 'RunPlugin(plugin://'+addonID+'/?mode=downloadVideo&url='+urllib.quote_plus(url)+')',))
    entries.append((translation(30043), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',))
    entries.append(('Find ' + user + ' Other Videos', 'Container.Update(plugin://plugin.video.dailymotion_com/?mode=listVideos&url=user:'+user+',return)',))
    if dmUser == "":
        playListInfos = "###MODE###=ADD###USER###="+user+"###THUMB###=DefaultVideo.png###END###"
        entries.append((translation(30028), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addLiveLink(name, url, mode, iconimage, desc):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addUserDir(name, url, mode, iconimage, views,videos):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": views + "\nVideos:" + videos, "episode" : int(videos),"playcount":int(views)})
    if dmUser == "":
        playListInfos = "###MODE###=ADD###USER###="+name+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30028), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addFavDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(translation(30033), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=addFav)',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addUserFavDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if dmUser == "":
        playListInfos = "###MODE###=REMOVE###REFRESH###=TRUE###USER###="+name+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30029), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_PLAYCOUNT)
except:
    pass
if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLive':
    listLive(url)
elif mode == 'listUsers':
    listUsers(url)
elif mode == 'listChannels':
    listChannels()
elif mode == 'listGroups':
    listGroups(url)
elif mode == 'favourites':
    favourites(url)
elif mode == 'addFav':
    addFav()
elif mode == 'personalMain':
    personalMain()
elif mode == 'listPersonalUsers':
    listPersonalUsers()
elif mode == 'favouriteUsers':
    favouriteUsers()
elif mode == 'listUserPlaylists':
    listUserPlaylists(url)
elif mode == 'showPlaylist':
    showPlaylist(url)
elif mode == 'sortVideos1':
    sortVideos1(url)
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'sortVideos2':
    sortVideos2(url)
elif mode == 'sortUsers1':
    sortUsers1()
elif mode == 'sortUsers2':
    sortUsers2(url)
elif mode == 'playVideo':
    
    playVideo(url)
elif mode == 'playLiveVideo':
    playVideo(url,live=True)

elif mode == 'playArte':
    playArte(url)
elif mode == 'channel_you_follow':
    channel_you_follow(url)
elif mode == "queueVideo":
    queueVideo(url, name)
elif mode == "downloadVideo":
    downloadVideo(url)
elif mode == 'search':
    search()
else:
    index()