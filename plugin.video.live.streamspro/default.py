
import _lspro
import urlparse,sys,urllib,xbmc,xbmcplugin,xbmcaddon,traceback

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
    deg(url)
    _lspro.getData(url,fanart,data)
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
    deg(url)
    if url.startswith("$pyFunction:"):
        #xbmc.log("$pyFunction in mode 12 Test",xbmc.LOGNOTICE)
        url = _lspro.Func_in_externallink(url)
        #if stream_url:
        #    playsetresolved(stream_url,name,itemart,item_info,True)
        #else:
        #    xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Finding stream_url for pyFunction failed ,1000,"")")         
    
    if not url.startswith("plugin://plugin") or not any(x in url for x in g_ignoreSetResolved):#not url.startswith("plugin://plugin.video.f4mTester") :
        setres=True
        if '$$LSDirect$$' in url:
            url=url.replace('$$LSDirect$$','')
            setres=False
        import xbmcgui
        item = xbmcgui.ListItem(path=url)
        if not setres:
            xbmc.Player().play(url)
        else: 
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    
    else:
#        print 'Not setting setResolvedUrl'
        xbmc.executebuiltin('XBMC.RunPlugin('+url+')')


elif mode==13:
    #addon_log("play_playlist")
    _lspro.play_playlist(name, playlist,itemart=itemart,item_info=item_info)

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
    try:
        import youtubedl
    except Exception:
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Please [COLOR yellow]install Youtube-dl[/COLOR] module ,10000,"")")
    stream_url=youtubedl.single_YD(url)
    _lspro.playsetresolved(stream_url,name)
elif mode==19:
    #addon_log("Genesiscommonresolvers")

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
    xbmc.log(str(path),xbmc.LOGNOTICE)
    path = dict(urlparse.parse_qsl(path.split('?',1)[1]))
    deg(path)
    url,tvgurl,epgfile,offset = path.get('url'),path.get('tvgurl'),path.get('epgfile'),path.get('offset')
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
elif mode==60:
    #addon_log("Requesting JSON-RPC Items")
    xbmc.log(str(url),xbmc.LOGNOTICE)
    if ':' in url:
        _lspro.search_lspro_source(url)
    else:
        _lspro.search_lspro_source()
elif mode==1899:
    #addon_log("Requesting JSON-RPC Items")
    _lspro.pluginquerybyJSON(url, addtoplaylist=True)
if xbmc.getCondVisibility("Player.HasMedia") and xbmc.Player().isPlaying():    
    _lspro.ShowOSDnownext()
 