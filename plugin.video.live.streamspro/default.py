
import _lspro

import urlparse,sys,urllib,xbmc,xbmcplugin,xbmcaddon,traceback
import time
g_ignoreSetResolved=['plugin.video.dramasonline','plugin.video.f4mTester','plugin.video.shahidmbcnet','plugin.video.SportsDevil','plugin.stream.vaughnlive.tv','plugin.video.ZemTV-shani']


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
def deg(string,level=xbmc.LOGNOTICE):
        try:
            if isinstance(string,list):
                string= "\n".join(string)        
            xbmc.log("[LSPRO::]: %s" %str(string),level)
        except:
            traceback.print_exc()
            pass
def addon_log(string,level=xbmc.LOGNOTICE):
    debug = False
    if debug:
        try:
            xbmc.log("[addon.live.streamspro-%s]: %s" %('addon_version', string),level)
        except:
            pass
url=None
name=None
mode=None
playlist=None
iconimage=None
thumb = None
fanart=None
fav_mode=None
regexs=None
params=get_params()
plot = None
try:
    url=urllib.unquote_plus(params["url"]).decode('utf-8')
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
    
except:
    pass
try:
    thumb=urllib.unquote_plus(params["thumb"])
    
except:
    pass
try:
    plot=urllib.unquote_plus(params["plot"]) or name
    
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
    
except:
    pass
try:
    fanart=urllib.unquote_plus(params["fanart"]) 
    
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    playlist=eval(urllib.unquote_plus(params["playlist"]).replace('||',','))
except:
    pass
try:
    fav_mode=int(params["fav_mode"])
except:
    pass
try:
    regexs=params["regexs"]
except:
    pass

playitem=''

try:
    playitem=urllib.unquote_plus(params["playitem"])
except:

    pass
if not playitem =='':
    from _lspro import getSoup,getItems
    s=getSoup('',data=playitem)
    name,url,regexs=getItems(s,None,dontLink=True)

    if regexs:
        mode=117
    else:
        mode=12
if mode==None:
    #addon_log("getSources")
    
    _lspro.getSources()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==1:
    #addon_log("getData")
    data=None
    if regexs and len(regexs)>0:
        
        data,setresolved=_lspro.getRegexParsed(regexs, url)
    #print data
    #url=''
        if data.startswith('http') or data.startswith('smb') or data.startswith('nfs') or data.startswith('/'):
            url=data
            data=None
        #create xml here
    ss=_lspro.getData(url,fanart,data)
    #deg("ssssssssssssssss")
    #deg(ss)
    if not ss:
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


elif mode==2:
    #addon_log("getChannelItems")
    _lspro.getChannelItems(name,url,fanart)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==3:
    #addon_log("getSubChannelItems")
    _lspro.getSubChannelItems(name,url,fanart)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==4:
    #addon_log("getFavorites")
    _lspro.getFavorites()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==5:
    #addon_log("addFavorite")
    try:
        name = name.split('\\ ')[1]
    except:
        pass
    try:
        name = name.split('  - ')[0]
    except:
        pass
    _lspro.addFavorite(name,url,iconimage,fanart,fav_mode)

elif mode==6:
    #addon_log("rmFavorite")
    try:
        name = name.split('\\ ')[1]
    except:
        pass
    try:
        name = name.split('  - ')[0]
    except:
        pass
    _lspro.rmFavorite(name)

elif mode==7:
    #addon_log("addSource")
    _lspro.addSource(url)

elif mode==8:
    #addon_log("rmSource")
    _lspro.rmSource(name)

elif mode==9:
    #addon_log("download_file")
    _lspro.download_file(name, url)

elif mode==10:
    #addon_log("getCommunitySources")
    _lspro.getCommunitySources()

elif mode==11:
    #addon_log("addSource")
    _lspro.addSource(url)

elif mode==12:
    #addon_log("setResolvedUrl")
    #if url.endswith((".mkv",".m3u8",".ts",".f4m",".flv",".mp4",".avi",".mp3")) or "?wmsAuthSign=" in url or url.startswith("rtmp"):
    #_lspro.urlresolvers(url).resolve()
    
    if url.startswith("$pyFunction:"):
        url = _lspro.Func_in_externallink(url)
    if url.startswith("plugin://plugin.video.youtube") and not '?video_id' in url:
        deg("updating youtube container")
        xbmc.executebuiltin('Container.Update(%s,return)' %url)
    elif ".mpd" in url:
            import xbmcgui
            item = xbmcgui.ListItem(name)
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')  
            item.setProperty(u'IsPlayable', u'true')
            #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            xbmc.Player().play(url,item)
            xbmc.sleep(1000)
    if  not xbmc.Player().isPlaying():
        
        if not url.startswith("plugin://plugin") or not any(x in url for x in g_ignoreSetResolved):#not url.startswith("plugin://plugin.video.f4mTester") :
            setres=True
            if '$$LSDirect$$' in url:
                url=url.replace('$$LSDirect$$','')
                setres=False
            if url.endswith((".mkv",".m3u8",".ts",".f4m",".flv",".mp4",".avi",".mp3")) or "?wmsAuthSign=" in url or ".m3u8?" in url or url.startswith("rtmp")or url.startswith("plugin://"):            
                url = url
            else:    
                deg("checking urlresolvers database for the url")
                UR = _lspro.urlresolvers(url)
                if UR.resolveable():
                    deg('tRYING TO urlresolvers %s' %url) 
                    url = UR.resolve()
            
            
            import xbmcgui
            item = xbmcgui.ListItem(path=url)
          
            if not setres:
                xbmc.Player().play(url,item)
            else: 
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        


            #xbmc.executebuiltin('playlist.playoffset(video,0)')
        else:
            deg('Not setting setResolvedUrl for %s' %url) 
            xbmc.executebuiltin('XBMC.RunPlugin('+url+')')
        #xbmc.executebuiltin('Container.Update('+url+')')
        #xbmc . executebuiltin ( "PlayMedia(%s)" % url )
		
#"Show a image before you play video. It will activate \"FullScreenVideo\" then play your video."    
   
    #xbmc.executebuiltin('ActivateWindow(12005)') 
    #deg("we are here....")
    #pic = xbmc.executebuiltin('ShowPicture("%s")'%("https://yt3.ggpht.com/-1kCe6rbK_DQ/AAAAAAAAAAI/AAAAAAAAAAA/_jT-RboE2cY/s100-c-k-no-mo-rj-c0xffffff/photo.jpg"))
    #time.sleep(4.5)
    #xbmc.executebuiltin('Action(back)') 
    #time.sleep(1.0)

elif mode==13:
    if not playlist:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        xbmc.Player().play()
        #xbmc.executebuiltin('Playlist.PlayOffset(0)')
    #addon_log("play_playlist")
        #xbmc.Player().play(xbmc.PlayList(xbmc.PLAYLIST_VIDEO))
    else:
        _lspro.play_playlist(name, playlist)

elif mode==14:
    #addon_log("get_xml_database")
    _lspro.get_xml_database(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==15:
    #addon_log("browse_xml_database")
    _lspro.get_xml_database(url, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==16:
    #addon_log("browse_community")
    _lspro.getCommunitySources(url,browse=True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==17 or mode==117:
    addon_log("getRegexParsed")
    from _lspro import RepeatedRegexs
    RepeatedRegexs(regexs,url,name)


elif mode==18:
    #addon_log("youtubedl")
  

    stream_url=_lspro.ytdl(url)
    _lspro.playsetresolved(stream_url,name)
elif mode==19:

    from _lspro import urlsolver
    sol_url = urlsolver(url)
    if sol_url :
        _lspro.playsetresolved (sol_url,name,setresolved=True)
    else:
        xbmc.log("[addon.live.streamspro-%s]: %s" %('Failed attempt', "dddd"),xbmc.LOGNOTICE)                    
elif mode==21:
    #addon_log("download current file using youtube-dl service")
    _lspro.ytdl_download('',name,'video')
elif mode==23:
    #addon_log("get info then download")
    _lspro.ytdl_download(url,name,'video')
elif mode==24:
    #addon_log("Audio only youtube download")
    _lspro.ytdl_download(url,name,'audio')
elif mode==25:
    #addon_log("Searchin Other plugins")
    _lspro._search(url,name)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode==26: # whats on today EPG
    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    
    path = dict(urlparse.parse_qsl(path.split('?',1)[1]))
    xbmc.log(str(path),xbmc.LOGNOTICE)
    from _lspro import epgxml_db
    
    #url,tvgurl,epgfile,offset = path.get('url'),path.get('tvgurl'),path.get('epgfile'),path.get('offset')
    epgxml_db().onedayepg(name,path.get('url'))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
   
elif mode==55:
    #addon_log("enabled lock")
    addon = xbmcaddon.Addon('plugin.video.live.streamspro')
    parentalblockedpin =addon.getSetting('parentalblockedpin')
    keyboard = xbmc.Keyboard('','Enter Pin')
    keyboard.doModal()
    if not (keyboard.isConfirmed() == False):
        newStr = keyboard.getText()
        if newStr==parentalblockedpin:
            addon.setSetting('parentalblocked', "false")
            xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Parental Block Disabled,5000,"+icon+")")
        else:
            xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Wrong Pin??,5000,"+icon+")")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode==56:
    #addon_log("disable lock")
    addon = xbmcaddon.Addon('plugin.video.live.streamspro')
    addon.setSetting('parentalblocked', "true")
    xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Parental block enabled,5000,"+icon+")")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==53:
    #addon_log("Requesting JSON-RPC Items")
    _lspro.pluginquerybyJSON(url)
elif mode==54:

    deg([xbmc.getInfoLabel('ListItem.TVShowTitle'),xbmc.getInfoLabel('ListItem.Season'),xbmc.getInfoLabel('ListItem.Episode'),xbmc.getInfoLabel('ListItem.StartTime'),xbmc.getInfoLabel('ListItem.Label2')])
    tvshowname = xbmc.getInfoLabel('ListItem.TVShowTitle').split(":")[0]
    deg(tvshowname)
    if not tvshowname:
        tvshowname = xbmc.getInfoLabel('ListItem.Title')
    
    #_search(url,name)
    #fill up search by sendInput
    season = xbmc.getInfoLabel('ListItem.Season')
    episode = xbmc.getInfoLabel('ListItem.Episode')
    genre = xbmc.getInfoLabel('ListItem.genre')
    deg(genre)
    if genre:
        all_genre = [i.lower().replace(" ","") for i in genre.split(",") if i]
    if season or episode:
        url = 'http://api.trakt.tv/search/show?limit=20&page=1&query=' + urllib.quote_plus(tvshowname)
        url = '%s?action=tvshowPage&url=%s' % ("plugin://plugin.video.exodus/", urllib.quote_plus(url))
        _lspro.pluginquerybyJSON(url)

    elif genre and any( i in ["movie","film"]  for i in all_genre):
        url = 'http://api.trakt.tv/search/movie?limit=20&page=1&query=' + urllib.quote_plus(tvshowname)
        #going back dont work b/c query is empty
        url = '%s?action=moviePage&url=%s' % ("plugin://plugin.video.exodus/", urllib.quote_plus(url))
        _lspro.pluginquerybyJSON(url)
    else:
       
        _lspro._search(url,tvshowname)
    #_lspro.pluginquerybyJSON(genre,tvshowname)
elif mode==60:
    #addon_log("Requesting JSON-RPC Items")
    xbmc.log(str(url),xbmc.LOGNOTICE)
    if ':' in url:
        _lspro.search_lspro_source(url)
    else:
        _lspro.search_lspro_source()
elif mode==61:
    #addon_log("Requesting JSON-RPC Items")
    _lspro.sdevil()

elif mode==65:
    #addon_log("Requesting JSON-RPC Items")
    _lspro.update_livestreamer()

elif mode==1899:
    #addon_log("Requesting JSON-RPC Items")
    _lspro.pluginquerybyJSON(url, addtoplaylist=True)
elif mode == 1915:
        if url is None or url == "" or url == "NewSearch":
            _lspro.Search_onGoogle(url)
            
        else:
            _lspro.Search_onGoogle_result(url)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    
if xbmc.getCondVisibility("Player.HasMedia") and xbmc.Player().isPlaying()and plot:
    #deg("Spikeeeeeeeeeeeeeeee")
    _lspro.ShowOSDnownext()
 