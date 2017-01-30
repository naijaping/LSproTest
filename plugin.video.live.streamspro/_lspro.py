# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import os
import xbmc,sys
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import traceback
import time
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup, BeautifulSOAP
import urlparse
import datetime
from collections import OrderedDict,Counter
import fnmatch
import cookielib,base64
import xml.etree.ElementTree
try:
    from xml.sax.saxutils import escape
except: traceback.print_exc()
try:
    import json
except:
    import simplejson as json
import SimpleDownloader as downloader
import pyfscache
LS_CACHE_getepgcontent = pyfscache.FSCache(xbmc.translatePath("special://temp/"),hours=10)
LS_CACHE_epginfo = pyfscache.FSCache(xbmc.translatePath("special://temp/"),minutes=25)
LS_CACHE_urlsolver = pyfscache.FSCache(xbmc.translatePath("special://temp/"),hours=1)
LS_CACHE_ytdl_domain = pyfscache.FSCache(xbmc.translatePath("special://temp/"),hours=100)

epgtimeformat2 = "%Y-%m-%d %H:%M:%S"
epgtimeformat = "%Y%m%d%H%M%S"
GUIDE={}
now = datetime.datetime.now().replace(microsecond=0)
resolve_url=["youwatch",'180upload.com', 'letwatch.us','allmyvideos.net', 'bestreams.net', 'clicknupload.com', 'cloudzilla.to', 'movshare.net', 'novamov.com', 'nowvideo.sx', 'videoweed.es', 'daclips.in', 'datemule.com', 'fastvideo.in', 'faststream.in', 'filehoot.com', 'filenuke.com', 'sharesix.com',  'plus.google.com', 'picasaweb.google.com', 'gorillavid.com', 'gorillavid.in', 'grifthost.com', 'hugefiles.net', 'ipithos.to', 'ishared.eu', 'kingfiles.net', 'mail.ru', 'my.mail.ru', 'videoapi.my.mail.ru', 'mightyupload.com', 'mooshare.biz', 'movdivx.com', 'movpod.net', 'movpod.in', 'movreel.com', 'mrfile.me', 'nosvideo.com', 'openload.io', 'played.to', 'bitshare.com', 'filefactory.com', 'k2s.cc', 'oboom.com', 'rapidgator.net', 'primeshare.tv', 'bitshare.com', 'filefactory.com', 'k2s.cc', 'oboom.com', 'rapidgator.net', 'sharerepo.com', 'stagevu.com', 'streamcloud.eu', 'streamin.to', 'thefile.me', 'thevideo.me', 'tusfiles.net', 'uploadc.com', 'zalaa.com', 'uploadrocket.net', 'uptobox.com', 'v-vids.com', 'veehd.com', 'vidbull.com', 'videomega.tv', 'vidplay.net', 'vidspot.net', 'vidto.me', 'vidzi.tv', 'vimeo.com', 'vk.com', 'vodlocker.com', 'xfileload.com', 'xvidstage.com', 'zettahost.tv']
g_ignoreSetResolved=['plugin.video.dramasonline','plugin.video.f4mTester','plugin.video.shahidmbcnet','plugin.video.SportsDevil','plugin.stream.vaughnlive.tv','plugin.video.ZemTV-shani']
art_tags = ['thumbnail', 'fanart', 'poster','clearlogo','banner','clearart']
info_tags = ['director' ,'season','episode', 'writer','date', 'info', 'rating', 'studio', 'source','genre','plotoutline','credits','dateadded','tagline']

addon = xbmcaddon.Addon('plugin.video.live.streamspro')
addon_version = addon.getAddonInfo('version')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
home = xbmc.translatePath(addon.getAddonInfo('path').decode('utf-8'))
favorites = os.path.join(profile, 'favorites')
history = os.path.join(profile, 'history')
REV = os.path.join(profile, 'list_revision')
icon = os.path.join(home, 'icon.png')
FANART = os.path.join(home, 'fanart.jpg')
source_file = os.path.join(profile, 'source_file')

m3uthumb = os.path.join(home,'m3ulist.jpg')
communityfiles = os.path.join(profile, 'LivewebTV')
libpyCode = os.path.join(profile,'libpyCode')
downloader = downloader.SimpleDownloader()
debug = addon.getSetting('debug')
disableepg =addon.getSetting('disableepg')
logo_folder = addon.getSetting('logo_folderPath')
groupm3ulinks = addon.getSetting('groupm3ulinks')

LivewebTVepg = os.path.join(profile, 'LivewebTVepg')

add_playlist = addon.getSetting('add_playlist')
ask_playlist_items =addon.getSetting('ask_playlist_items')
use_thumb = addon.getSetting('use_thumb')

global itemart,item_info,PLAYHEADERS
global viewmode,tsdownloader, hlsretry
tsdownloader=False
hlsretry=False
viewmode=None
if addon.getSetting('tsdownloader') == 'true' :
    tsdownloader = True
if addon.getSetting('hlsretry') == 'true' :
    hlsretry = True      
item_info = {}
itemart={}
PLAYHEADERS=None
itemart["icon"] = icon
itemart["thumb"] = icon
itemart["fanart"] = FANART
class NoRedirection(urllib2.HTTPErrorProcessor):
   def http_response(self, request, response):
       return response
   https_response = http_response

REMOTE_DBG=False;
if REMOTE_DBG:
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)
def addon_log(string,level=xbmc.LOGNOTICE):
    if debug == 'true':
        try:
            xbmc.log("[addon.live.streamspro-%s]: %s" %('addon_version', string),level)
        except:
            pass
def date_strto_localtime(date_str,epgtimeformat = "%Y%m%d%H%M%S",my_timezone=150):
    import pytz
#try:datetime.datetime(*(time.strptime(input, epgtimeformat)[0:6]))
    notimezone=datetime.datetime(*(time.strptime(now.strftime("%Y%m%d") + date_str.split(":")[0]+date_str.split(":")[1],epgtimeformat)[0:6]))
    db_time = pytz.timezone(str(pytz.timezone("Etc/UTC"))).localize(notimezone)
    if isinstance(my_timezone, int):
        my_location=pytz.timezone(pytz.all_timezones[int(my_timezone)])
    else:
        my_location=pytz.timezone(my_timezone)
    print my_location
    converted_time=db_time.astimezone(my_location)
    print converted_time
    starttime=converted_time.strftime("%H:%M")
    print starttime
    return starttime
    #item.setProperty('starttime',starttime)
#except Exception, e:
    #xbmc.log(msg="[Match Center] Exception: %s" % (str(e)), level=xbmc.LOGDEBUG)
    
if os.path.exists(favorites)==True:
    FAV = open(favorites).read()
else: FAV = []
if os.path.exists(source_file)==True:
    SOURCES = open(source_file).read()
else: SOURCES = []

def GetLivestreamerLink(url):
    addon_log('GetLivestreamerLink' + url)
    import streamlink
    s=streamlink.Streamlink()
    try:
        get_streams = s.streams(url)
        stream = get_streams["best"]
        if not get_streams:
            addon_log("No streams found on URL '{0}'".format(url))
            return
    except Exception:
        return
    final_url = ''
    if isinstance(stream, streamlink.stream.hls.HLSStream):
        return stream.url
    elif isinstance(stream, streamlink.stream.RTMPStream):
        xbmc.log('RTMP Trouble ahead for kodi 17' + url)
        final_url = "{0} swfVfy=1 live=true timeout=15".format(stream.params["rtmp"])
        try:
            if stream.params["playpath"]:
                final_url = final_url + " playpath={0}".format(stream.params["playpath"])
        except Exception:
            pass
        try:
            if stream.params["swfVfy"]:
                final_url = final_url + " swfUrl={0}".format(stream.params["swfVfy"])
        except Exception:
            pass
        try:

            if stream.params["pageUrl"]:
                final_url = final_url + " pageUrl={0}".format(stream.params["pageUrl"])
        except Exception:
            pass
        try:

            if stream.params["app"]:
                final_url = final_url + " app={0}".format(stream.params["app"])
        except Exception:
            pass

        return final_url


def makeRequest(url, headers=None):
        try:
            if headers is None:
                headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
                
            if '|' in url:
                url,header_in_page=url.split('|')
                header_in_page=header_in_page.split('&')
                
                for h in header_in_page:
                    if len(h.split('='))==2:
                        n,v=h.split('=')
                    else:
                        vals=h.split('=')
                        n=vals[0]
                        v='='.join(vals[1:])
                        
                    headers[n]=v
                    
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log('URL: '+url)
            if hasattr(e, 'code'):
                
                addon_log('We failed with error code - %s.' % e.code)
                xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,We failed with error code - "+str(e.code)+",10000,"+icon+")")
                
                    
            elif hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
                xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,We failed to reach a server. - "+str(e.reason)+",10000,"+icon+")")

def getSources():
        try:
            if os.path.exists(favorites) == True:
                addDir('Favorites','url',4, itemart , item_info)
            if addon.getSetting("searchotherplugins") == "true":
                addDir('Search Other Plugins','Search Plugins',25, itemart , item_info)

            if os.path.exists(source_file)==True:
                sources = json.loads(open(source_file,"r").read())
                
                if len(sources) > 1:
                    for i in sources:
                        try:
                            
                            if isinstance(i, list):
                                item_info['showcontext'] = 'source'
                                addDir(i[0].encode('utf-8'),i[1].encode('utf-8'),1,itemart , item_info)    
                            else:
                                if i.has_key('thumbnail'):
                                    itemart['thumb'] = i['thumbnail']
                                if i.has_key('fanart'):
                                    itemart['fanart'] = i['fanart']
                                if i.has_key('description'):
                                    item_info['plot'] = i['description']
                                if i.has_key('date'):
                                    item_info['date'] = i['date']
        
                                if i.has_key('genre'):
                                    item_info['genre'] = i['genre']
                                else:
                                  item_info['genre'] = 'Live TV'  
                                if i.has_key('credits'):
                                    item_info['credits'] = i['credits']
                                else:
                                    item_info['credits'] = 'Originally by divingmules.Now maintain by Shani @ forums.tvaddons.ag'
                                item_info['showcontext'] ='source'
                                addDir(i['title'].encode('utf-8'), i['url'].encode('utf-8'), 1, itemart , item_info)
                        except: traceback.print_exc()
                else:
                    if len(sources) == 1:
                        if isinstance(sources[0], list):
                            getData(sources[0][1].encode('utf-8'),FANART)
                        else:
                            getData(sources[0]['url'], sources[0]['fanart'])
        except: traceback.print_exc()

def addSource(url=None):
        DBfolder = False
        media_info = None
        if url is None:
            if not addon.getSetting("new_file_source") == "":
               source_url = addon.getSetting('new_file_source').decode('utf-8')
            elif not addon.getSetting("new_url_source") == "":
               source_url = addon.getSetting('new_url_source').decode('utf-8')
            elif not addon.getSetting("dropboxfolder") == "":
               source_url = "%s%s" %("zip://",addon.getSetting('dropboxfolder').decode('utf-8'))
               
               DBfolder = True
        else:
            source_url = url
        if source_url == '' or source_url is None:
            return
        addon_log('Adding New Source: '+source_url.encode('utf-8'))

        
        
        if not DBfolder:
            
            
            data = getSoup(source_url)
                
            if isinstance(data,BeautifulSOAP):
                if data.find('channels_info'):
                    media_info = data.channels_info
                elif data.find('items_info'):
                    media_info = data.items_info
        if media_info:
            source_media = {}
            source_media['url'] = source_url
            try: source_media['title'] = media_info.title.string
            except: pass
            try: source_media['thumbnail'] = media_info.thumbnail.string or icon
            except: pass
            try: source_media['fanart'] = media_info.fanart.string or FANART
            except: pass
            try: source_media['genre'] = media_info.genre.string
            except: pass
            try: source_media['description'] = media_info.description.string
            except: pass
            try: source_media['date'] = media_info.date.string
            except: pass
            try: source_media['credits'] = media_info.credits.string
            except: pass
        else:
            if '/' in source_url:
                nameStr = source_url.split('/')[-1].split('.')[0]
            if '\\' in source_url:
                nameStr = source_url.split('\\')[-1].split('.')[0]
            if '%' in nameStr:
                nameStr = urllib.unquote_plus(nameStr)
            keyboard = xbmc.Keyboard(nameStr,'Displayed Name, Rename?')
            keyboard.doModal()
            if (keyboard.isConfirmed() == False):
                return
            newStr = keyboard.getText()
            if len(newStr) == 0:
                return
            source_media = {}
            thumbnail= addon.getSetting('source_thumb')
            if not thumbnail== "":
                source_media['thumbnail']= thumbnail.decode('utf-8')
            source_media['title'] = newStr
            source_media['url'] = source_url
            source_media['fanart'] = FANART

        if os.path.exists(source_file)==False:
            source_list = []
            source_list.append(source_media)
            b = open(source_file,"w")
            b.write(json.dumps(source_list))
            b.close()
        else:
            sources = json.loads(open(source_file,"r").read())
            sources.append(source_media)
            b = open(source_file,"w")
            b.write(json.dumps(sources))
            b.close()
        addon.setSetting('new_url_source', "")
        addon.setSetting('source_thumb', "")
        
        addon.setSetting('new_file_source', "")
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,New source added.,5000,"+icon+")")
        xbmc.executebuiltin("XBMC.Container.Refresh")
        addon.setSetting('dropboxfolder', "")


def rmSource(name):
        sources = json.loads(open(source_file,"r").read())
        for index in range(len(sources)):
            if isinstance(sources[index], list):
                if sources[index][0] == name:
                    del sources[index]
                    b = open(source_file,"w")
                    b.write(json.dumps(sources))
                    b.close()
                    break
            else:
                if sources[index]['title'] == name:
                    del sources[index]
                    b = open(source_file,"w")
                    b.write(json.dumps(sources))
                    b.close()
                    break
        xbmc.executebuiltin("XBMC.Container.Refresh")

def find_files(directory, pattern="*"):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename

def getSoup(url,data=None):
        if url.startswith('zip://'):
            dir_url = down_url(url.split("zip://",1)[1])
            
            if os.path.isdir(dir_url):
                for source_url in find_files(dir_url):
                    if '/' in source_url:
                        nameStr = source_url.split('/')[-1].split('.')[0]
                    if '\\' in source_url:
                        nameStr = source_url.split('\\')[-1].split('.')[0]
                    if '%' in nameStr:
                        nameStr = urllib.unquote_plus(nameStr)
                
                    addDir(nameStr,source_url,1,itemart,item_info)
                return 
        if url.startswith('http://') or url.startswith('https://'):
            enckey=False
            if '$$PLAYHEADERS=' in url:
                global PLAYHEADERS
                PLAYHEADERS=url.split('$$PLAYHEADERS=')[1].split('$$')[0]
                rp='$$PLAYHEADERS=%s$$'%PLAYHEADERS
                url=url.replace(rp,"")
            if '$$TSDOWNLOADER$$' in url:
                tsdownloader=True
                url=url.replace("$$TSDOWNLOADER$$","")
            if '$$HLSRETRY$$' in url:
                hlsretry=True
                url=url.replace("$$HLSRETRY$$","")
            if '$$LSProEncKey=' in url:
                enckey=url.split('$$LSProEncKey=')[1].split('$$')[0]
                rp='$$LSProEncKey=%s$$'%enckey
                url=url.replace(rp,"")
                
            data =makeRequest(url)
            if not data:
                return
            if enckey:
                    import pyaes
                    enckey=enckey.encode("ascii")
                    print enckey
                    missingbytes=16-len(enckey)
                    enckey=enckey+(chr(0)*(missingbytes))
                    print repr(enckey)
                    data=base64.b64decode(data)
                    decryptor = pyaes.new(enckey , pyaes.MODE_ECB, IV=None)
                    data=decryptor.decrypt(data).split('\0')[0]
                    
            if re.search("#EXTM3U",data) or '.m3u' in url or re.search(r"^\s*#EXTINF",data):

                return data
        elif data == None:
            if not '/'  in url or not '\\' in url:

                url = os.path.join(communityfiles,url)
            if xbmcvfs.exists(url):
                if url.startswith("smb://") or url.startswith("nfs://"):
                    copy = xbmcvfs.copy(url, os.path.join(profile, 'temp', 'sorce_temp.txt'))
                    if copy:
                        data = open(os.path.join(profile, 'temp', 'sorce_temp.txt'), "r").read()
                        xbmcvfs.delete(os.path.join(profile, 'temp', 'sorce_temp.txt'))
                    else:
                        addon_log("failed to copy from smb:")
                else:
                    data = open(url, 'r').read()
                    if re.match("#EXTM3U",data)or 'm3u' in url:

                        return data
            else:
                addon_log("Soup Data not found!")
                return
        if data and '<SetViewMode>' in data:
            try:
                viewmode=re.findall('<SetViewMode>(.*?)<',data)[0]
                xbmc.executebuiltin("Container.SetViewMode(%s)"%viewmode)
                print 'done setview',viewmode
            except: pass
        return BeautifulSOAP(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)

def processPyFunction(data):
    try:
        if data and len(data)>0 and data.startswith('$pyFunction:'):
            data=doEval(data.split('$pyFunction:')[1],'',None,None )
    except: pass
    deg("ddddddddddddddddddddddddddddddddd")
    deg(data)
    return data

  
def checkfile(epgfilewithreg,timeforfileinsec):
        _time_limit = time.time() - int(timeforfileinsec)
        if os.path.isfile(epgfilewithreg):
            
            

            if os.stat(epgfilewithreg).st_mtime < _time_limit:
                xbmcvfs.delete(epgfilewithreg)        
        if os.path.isfile(epgfilewithreg):
            
            return True
        else:
            return False
              
def getData(url,fanart, data=None,searchterm=None):

        
    import checkbad
    checkbad.do_block_check(False)
    #if url.endswith('.py') and not url.startswith('http') :
    ##elif re.search('[A-Za-z_].*?\.[A-Za-z_].*?')
    #    #xbmc.log(str("###pyfffffffffffffilllle: from link###"),xbmc.LOGNOTICE)
    #    if '\\'  in url:
    #        url, = url.split('$pyFunction:')
    #    py_file = url.split('.py')[0]
    #    #doEval(py_file,'','','')
    #    Func_in_externallink(url,libpyCode)
    if  url.endswith(".plx") or 'navixtreme' in url :
        getnaviplx(url)    
    elif "###LSPRODYNAMIC###" in url:
        Func_in_externallink(url,libpyCode)        
    elif "$pyFunction:" in url and not url.startswith('http'):
        if '\\'  in url:
            tmp = url.split("$pyFunction:")
            Func_in_externallink("$pyFunction:"+tmp[1],libpyCode=tmp[0])
        else:
            Func_in_externallink(url,libpyCode)
    else:
        soup = getSoup(url,data)

         
        if isinstance(soup,BeautifulSOAP):
            if searchterm:
                allitem = soup('item')

                items = [getItems(allitem[index], fanart) for index,i in enumerate(allitem) if i.get('title') and searchterm in i.get('title').lower().strip()]
                return       

            if len(soup('channels')) > 0 and addon.getSetting('donotshowbychannels') == 'false':
                channels = soup('channel')
                for channel in channels:


                    linkedUrl=''
                    lcount=0
                    try:
                        linkedUrl =  channel('externallink')[0].string
                        lcount=len(channel('externallink'))
                    except: pass
                    
                    if lcount>1: linkedUrl=''

                    name = channel('name')[0].string
                    try:
                        name=processPyFunction(name)
                    except: pass                
                    itemart =  dict((art_tag.replace('thumbnail','thumb'),channel(art_tag)[0].string) for art_tag in art_tags if channel.find(art_tag)and channel(art_tag)[0].string is not None)
                    item_info =  dict((art_tag.replace('info','Plot'),channel(art_tag)[0].string) for art_tag in info_tags if channel.find(art_tag)and channel(art_tag)[0].string is not None)                 
                    thumbnail = itemart.get("thumb")
                    if thumbnail and len(thumbnail)>0 and thumbnail.startswith('$pyFunction:'):                
                        itemart["thumb"]=processPyFunction(thumbnail)
                    try:
                        if not itemart.get('fanart'):
                            if use_thumb == "true":
                                itemart["fanart"] = thumbnail

                    except:
                        itemart["fanart"] = fanart
                    try:
                        if linkedUrl=='':
                            item_info['showcontext'] = 'True'
                            addDir(name.encode('utf-8', 'ignore'),url.encode('utf-8'),2,itemart,item_info)
                        else:
                            
                            item_info['showcontext'] = 'source'
                            addDir(name.encode('utf-8'),linkedUrl.encode('utf-8'),1,itemart,item_info)
                    except:
                        
                        addon_log('There was a problem adding directory from getData(): '+name.encode('utf-8', 'ignore'))
            else:
                    if disableepg == 'true' :
                        map(getItems,soup('epgitem'),[fanart])                    
                        map(getItems,soup('item'),[fanart])
                    else:                    
                        if len(soup('epg')) > 0 or len(soup('itemepg')) > 0  :

                                lspro_Epg(soup)
                        total = len(soup("item"))
                        if total:
                            [getItems(i, fanart, total=total) for index,i in enumerate(soup("item")) if not i("itemepg")]                    
        elif soup:
            if searchterm:
                m3upat = re.compile(r"\s?#EXTINF:.+?,%s.*?[\n\r]+[^\r\n]+" %searchterm,  re.IGNORECASE )
                match = m3upat.findall(soup)
                map(parse_m3u,match)
                xbmc.log('m3333uuuuus 0000match: %s' %str(len(match)),xbmc.LOGNOTICE)
                return
            parse_m3u(soup,url)
def down_url(url,filename=None,_out=None):
    ZIP = False
    get_file_name = url.split('/')[-1]
    pDialog = xbmcgui.DialogProgressBG()
    
    pDialog.create('Downloading ......', 'File to download: %s ...' %get_file_name)
    message ='[COLOR yellow]{0}%[/COLOR]  Done...\n{1}'
    size = 0
    block_sz = 8192
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0'}
    req = urllib2.Request(url,None,headers)
    song = urllib2.urlopen(req)
    meta = song.info()
    try:
        file_size = int(meta.getheaders("Content-Length")[0])
    except Exception:
        file_size= 20
        message = '[COLOR yellow]!!File Size Not Found{0}%[/COLOR]  Done...\n{1}'
    if not filename:
        try:
            attachment = meta.getheaders("content-disposition")
            if attachment:
                filename= re_me (attachment[0],r'filename\W*([^\'";]+)')
                if filename == "":
                    raise
                else:
                    if ".zip" in filename:
                        ZIP= True
            else:
                raise
        except:
            filename = cacheKey(url)
            pass
        if _out:
            filename = os.path.join(_out,filename)
        else:
            filename=os.path.join(profile,filename)
    with open(filename, 'wb') as f:

        
        while True:
            buffer = song.read(block_sz)
            if not buffer:
                break

            size += len(buffer) 
            f.write(buffer)
            
            pDialog.update(int(size * 100. / file_size),message.format(str(int(size * 100. / file_size)),filename.rsplit('\\',1)[0]))
    pDialog.close()
    xbmc.sleep(1) #change from 10 to 0.5
    if open(filename).read(1024).startswith('\x50\x4b\x03\x04') or ZIP:
        #try:
            if not _out:
                _out = os.path.join(profile,cacheKey(url))
            import zipfile
        
            zfile = zipfile.ZipFile(filename, 'r')
            zfile.extractall(path=_out)
            
        #except Exception:
            #return
            zfile.close()
            os.remove(filename)
            return _out        
    elif open(filename).read(1024).startswith('\x1f\x8b\x08'):
            import gzip
        #try:
            zfile = gzip.open(filename, 'rb')
            content= zfile.read()
            zfile.close()
            with open(filename,"wb") as f:
                f.write(content)
    
                
    return filename
            
        
        
    #magic_dict = {
    #"\x1f\x8b\x08": "gz",
    #"\x42\x5a\x68": "bz2",
    #"\x50\x4b\x03\x04": "zip"
    #}
    #data = zlib.decompress(data, zlib.MAX_WBITS + 16)
    #f.write(data)
    #f.close()    
    
            
# borrow from https://github.com/enen92/P2P-Streams-XBMC/blob/master/plugin.video.p2p-streams/resources/core/livestreams.py
def deg(string,level=xbmc.LOGNOTICE):

        try:
            if isinstance(string,list):
                string= "\n".join(string)
            elif isinstance(string,tuple):
                string= "\n".join(map(str,string))
            xbmc.log("[LSPRO::]: %s" %str(string),level)
        except:
            traceback.print_exc()
            pass
def parse_m3u(data, url=None, g_name=None):
    content = data.strip()
    global itemart,item_info
    if  groupm3ulinks == 'true' and not url == None:
        if 'group-title' in content and g_name is None :
    
            groups = re.compile('group-title=[\'"](.*?)[\'"]').findall(content)
            if set(groups) > 2:
                for group in set(groups):
                    group_name = group
                    addDir(group_name,url,2,itemart,item_info)
                if re.search(r"^[\s]*#((?!title=).)*$", content, re.IGNORECASE | re.MULTILINE):
                    addDir("No Group-title",url,2,itemart,item_info)
                return    
        elif  g_name is None:
            groups = re.compile(r"^[\s]*#EXTINF.*?,[\s]*([\w\s]+)[\s]*:[^/]", re.IGNORECASE | re.MULTILINE).findall(content)
            #
            if groups and len(set(groups)) > 2 :
                for group in set(groups):
                    group_name = group
                    addDir(group_name,url,2,itemart,item_info)
                if re.search(r"^[\s]*#((?!title=).)*$", content, re.IGNORECASE | re.MULTILINE):
                    addDir("No category",url,2,itemart,item_info)
                return     
    if g_name:
        if g_name == 'No Group-title':
            match = re.compile(r"^[\s]*#EXTINF(((?!group-title=).)*),(.*?)[\n\r]+([^\r\n]+)",re.IGNORECASE|re.MULTILINE).findall(content)
            match =  [(other,channel_name,stream_url) for other,o,channel_name,stream_url in match]
        elif 'group-title' in content:
            
            gr_match= r'#EXTINF:(.*?group-title="%s".*?),(.*?)[\n\r]+([^\r\n]+)'
            match = re.compile(gr_match %re.escape(g_name)).findall(content)
        elif g_name == 'No category':
            
            match = re.compile(r'#EXTINF:(.+?),([^:]+)[\n\r]+([^\r\n]+)',re.I).findall(content)
        else:
            addon_log('No group-title found in m3u list re the country name %s' %g_name, xbmc.LOGNOTICE) 
            gr_match= r'#EXTINF:(.*?),[\s]*%s[\s]*:(.*?)[\n\r]+([^\r\n]+)'
            match = re.compile(gr_match %re.escape(g_name)).findall(content)            
    else:
        match = re.compile(r'#EXTINF:(.+?),(.*?)[\n\r]+([^\r\n]+)',re.IGNORECASE).findall(content)
    m3uepgfileorurl=addon.getSetting("m3uepgfileorurl")
    total = len(match)
    addon_log('tsdownloader %s' %tsdownloader, xbmc.LOGNOTICE) 
    getepg= False 
    #xbmc.log('total match %s' % str(match), xbmc.LOGNOTICE) 
    tvgurls = re.compile(r'#EXTM3U\s*tvgurl=[\'"](.*?)[\'"]',re.IGNORECASE).findall(content)
        
    if addon.getSetting("alwaysfindepg") == 'true'and len(m3uepgfileorurl) > 0:
        tvgurls.append(m3uepgfileorurl)
        tvgurls= set(tvgurls)
    itemsname=[]
    if tvgurls:
            names = [(index,cleanname(i[1])) for index,i in enumerate(match)]
            getepg=True
            for i in tvgurls:
                itemsname,epgnames = CheckEPGtimeValidaty(i,names)
                m3uitems= [(m3ustream_url(match[matchindex][2],match[matchindex][0],name), m3u_iteminfo(match[matchindex][0],match[matchindex][1],name))for matchindex,name in epgnames]
                
                [addLink(stream_url,stream_info[0],stream_info[1],stream_info[2]) for stream_url,stream_info in m3uitems if stream_url]
    if len(itemsname) > 0:

        m3uitems=  [(m3ustream_url(match[matchindex][2],match[matchindex][0],name), m3u_iteminfo(match[matchindex][0],match[matchindex][1]))for matchindex,name in itemsname]
    elif not itemsname and not getepg:
        
    
        m3uitems= [(m3ustream_url(stream_url,other,channel_name), m3u_iteminfo(other,channel_name))for other,channel_name,stream_url in match]
    [addLink(stream_url,stream_info[0],stream_info[1],stream_info[2]) for stream_url,stream_info in m3uitems if stream_url]
 

             
    
def m3ustream_url(stream_url,other,channel_name):
        if stream_url.endswith('.txt') or stream_url.endswith('.m3u') or stream_url.endswith('.xml'):
            item_info['showcontext'] = 'true'
            addDir(channel_name, stream_url, 1, itemart,item_info)
            return
          
        if 'type' in other:
            mode_type = re_me(other,'type=[\'"](.*?)[\'"]')
            if mode_type == 'yt-dl':
                stream_url = stream_url +"&mode=18"
               
            elif mode_type == 'ftv':
                stream_url = 'plugin://plugin.video.F.T.V/?name='+urllib.quote(channel_name) +'&url=' +stream_url +'&mode=125&ch_fanart=na'
        elif (tsdownloader and '.ts' in stream_url) and not 'f4mTester' in stream_url:
            stream_url = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(stream_url)+'&amp;streamtype=TSDOWNLOADER&name='+urllib.quote(channel_name)
        elif hlsretry and '.m3u8' in stream_url and not 'f4mTester' in stream_url:
            stream_url = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(stream_url)+'&amp;streamtype=HLSRETRY&name='+urllib.quote(channel_name)
        return stream_url
def cleanname(title,nocolor=False):
    if title == None: return "UNKNOWN"
    title = re.sub('&#(\d+);', '', title)
    title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '\"').replace('&amp;', '&')
    title = re.sub('\s', '', title.strip()).lower()
    if nocolor:
        re.sub("\[/?COLOR.*?\]","",title)

    
    
    return title    
       
def m3u_iteminfo(other,channel_name,getepg=None):
        item_info = {}
        itemart={}
        itemart['thumb'] = m3uthumb 
        itemart['fanart'] = ''
        if ':' in channel_name:
            co,_name = channel_name.split(':',1)
            channel_name = '%s [COLOR yellow][%s][/COLOR]' %(_name,co)
        else:
            _name = channel_name
        if getepg :
            #Na= cleanname(_name)
            #if Na in GUIDE.keys():
            itemart,item_info = epginfo(getepg)
        else:
            plot = re_me(other,'plot=[\'"](.*?)[\'"]')
            if plot:
                item_info['plot'] = plot
        #if 'tvg-logo' in other:
        thumbnail = re_me(other,'tvg-logo=[\'"](.*?)[\'"]')
        if thumbnail and thumbnail.startswith('http'):
                #if thumbnail.startswith('http'):
                    itemart['thumb'] = thumbnail
        elif not logo_folder == "":
            thumbnail = os.path.join(logo_folder , _name.lower().replace(' ','')+'.png')
            if xbmcvfs.exists(thumbnail):
                #
            
                itemart['thumb'] = thumbnail
        if use_thumb == 'true':
            itemart["fanart"] = itemart.get("thumb")
        return channel_name,itemart,item_info
def getChannelItems(name,url,fanart):
        soup = getSoup(url)
        if isinstance(soup, BeautifulSOAP):
            channel_list = [(i.items,i('subchannel'),i.fanart) for i in soup('channel') if  i.find('name').string == name]
            fanArt=fanart
            if channel_list[0][2]:
                fanArt = channel_list[0][2].string
            if channel_list[0][1]:
                for channel in channel_list[0][1]:

                    name = channel('name')[0].string
                    itemart =  dict((art_tag.replace('thumbnail','thumb'),channel(art_tag)[0].string) for art_tag in art_tags if channel.find(art_tag)and channel(art_tag)[0].string is not None)
                    item_info =  dict((art_tag.replace('info','plot'),channel(art_tag)[0].string) for art_tag in info_tags if channel.find(art_tag)and channel(art_tag)[0].string is not None)            
                try:
                    addDir(name.encode('utf-8', 'ignore'),url.encode('utf-8'),3,itemart,item_info)
                except:

                    addon_log('There was a problem adding directory - '+name.encode('utf-8', 'ignore'))
            if channel_list[0][0]:
                addon_log(' Look at MEeeeee::\n'+str(channel_list[0][0]) )
                map(getItems,channel_list[0][0],[fanArt])
        else:

            parse_m3u(data=soup, g_name=name)            


def getSubChannelItems(name,url,fanart):
        soup = getSoup(url)
        #channel_list = soup.find('subchannel', attrs={'name' : name.decode('utf-8')})
        channel_list = [i.subitems for i in soup('subchannel') if  i.find('name').string == name]
        #items = channel_list('subitem')
        map(getItems,channel_list[0],[fanart])
def getItems(item,fanart,itemart={},item_info={},total=1,dontLink=False):


            parentalblock =addon.getSetting('parentalblocked')
            parentalblock= parentalblock=="true"

            isXMLSource=False
            isJsonrpc = False
            
            applyblock='false'
            try:
                applyblock = item('parentalblock')[0].string
            except:
                addon_log('parentalblock Error')
                applyblock = ''
            if applyblock=='true' and parentalblock: return
            try:
                name = item('title')[0].string
                if name is None:
                    name = 'unknown?'
                elif '[COLOR #' in name:
                    name= ''.join([brace.replace(']','00]',1) for brace in name.split('#')])
                try:
                    
                    if '$pyFunction:' in name:
                        deg("processPyFunciton")
                        name=processPyFunction(name)
                except: pass                
            except:
                addon_log('Name Error')
                name = 'NameError'


 
            try:
                url = []
                if len(item('link')) >0:
                    #print 'item link', item('link')

                    for i in item('link'):
                        if not i.string == None:
                            url.append(i.string.strip())

                elif len(item('sportsdevil')) >0:
                    for i in item('sportsdevil'):
                        if not i.string == None:
                            sportsdevil = 'plugin://plugin.video.SportsDevil/?mode=1&amp;item=catcher%3dstreams%26url=' +i.string
                            referer = item('referer')[0].string
                            if referer:
                                #print 'referer found'
                                sportsdevil = sportsdevil + '%26referer=' +referer
                            url.append(sportsdevil)
                elif len(item('p2p')) >0:
                    for i in item('p2p'):
                        if not i.string == None:
                            if 'sop://' in i.string:
                                sop = 'plugin://plugin.video.p2p-streams/?mode=2url='+i.string +'&' + 'name='+name
                                url.append(sop)
                            else:
                                p2p='plugin://plugin.video.p2p-streams/?mode=1&url='+i.string +'&' + 'name='+name
                                url.append(p2p)
                elif len(item('yt-dl')) >0:
                    for i in item('yt-dl'):
                        if not i.string == None:
                            ytdl = i.string + '&mode=18'
                            url.append(ytdl)
                elif len(item('dm')) >0:
                    for i in item('dm'):
                        if not i.string == None:
                            dm = "plugin://plugin.video.dailymotion_com/?mode=playVideo&url=" + i.string
                            url.append(dm)
                elif len(item('dmlive')) >0:
                    for i in item('dmlive'):
                        if not i.string == None:
                            dm = "plugin://plugin.video.dailymotion_com/?mode=playLiveVideo&url=" + i.string
                            url.append(dm)
                elif len(item('utube')) >0:
                    for i in item('utube'):
                        if not i.string == None:
                            if ' ' in i.string :
                                utube = 'plugin://plugin.video.youtube/search/?q='+ urllib.quote_plus(i.string)
                                isJsonrpc=utube
                            elif len(i.string) == 11:
                                utube = 'plugin://plugin.video.youtube/play/?video_id='+ i.string
                            elif (i.string.startswith('PL') and not '&order=' in i.string) or i.string.startswith('UU'):
                                utube = 'plugin://plugin.video.youtube/play/?&order=default&playlist_id=' + i.string
                            elif i.string.startswith('PL') or i.string.startswith('UU'):
                                utube = 'plugin://plugin.video.youtube/play/?playlist_id=' + i.string
                            elif i.string.startswith('UC') and len(i.string) > 12:
                                utube = 'plugin://plugin.video.youtube/channel/' + i.string + '/'
                                isJsonrpc=utube
                            elif not i.string.startswith('UC') and not (i.string.startswith('PL'))  :
                                utube = 'plugin://plugin.video.youtube/user/' + i.string + '/'
                                isJsonrpc=utube
                        url.append(utube)
                elif len(item('imdb')) >0:
                    for i in item('imdb'):
                        if not i.string == None:
                            if addon.getSetting('genesisorpulsar') == '0':
                                imdb = 'plugin://plugin.video.exodus/?action=play&imdb='+i.string
                            else:
                                imdb = 'plugin://plugin.video.pulsar/movie/tt'+i.string+'/play'
                            url.append(imdb)
                elif len(item('f4m')) >0:
                        for i in item('f4m'):
                            if not i.string == None:
                                if '.f4m' in i.string:
                                    f4m = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(i.string)+'&amp;name='+urllib.quote_plus(name)
                                elif '.m3u8' in i.string and not '.ts' in i.string:
                                    f4m = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(i.string)+'&amp;streamtype=HLS&name='+urllib.quote_plus(name)

                                elif ".ts" in i.string:
                                    f4m = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(i.string)+'&amp;streamtype=TSDOWNLOADER&name='+urllib.quote_plus(name)
                                else:
                                    f4m = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(i.string)+'&amp;streamtype=SIMPLE&amp;name='+name
                            url.append(f4m)
                elif len(item('ftv')) >0:
                    for i in item('ftv'):
                        if not i.string == None:
                            ftv = 'plugin://plugin.video.F.T.V/?name='+urllib.quote(name) +'&url=' +i.string +'&mode=125&ch_fanart=na'
                        url.append(ftv)
                elif len(item('urlsolve')) >0:
                    
                    for i in item('urlsolve'):
                        if not i.string == None:
                            resolver = i.string +'&mode=19'
                            url.append(resolver)
                if len(url) < 1:
                    raise
            except:
                addon_log('Error <link> element, Passing:'+name.encode('utf-8', 'ignore'))
                return
            try:
                isXMLSource = item('externallink')[0].string
            except: pass

            if isXMLSource:
                ext_url=[isXMLSource]
                isXMLSource=True
            else:
                isXMLSource=False
            try:
                isJsonrpc = item('jsonrpc')[0].string
            except: pass
            if isJsonrpc:

                ext_url=[isJsonrpc]
                #print 'JSON-RPC ext_url',ext_url
                isJsonrpc=True
            else:
                isJsonrpc=False
            if not itemart :
                itemart =  dict((art_tag.replace('thumbnail','thumb'),item(art_tag)[0].string) for art_tag in art_tags if item(art_tag) and item(art_tag)[0].string is not None)            
            if not item_info:

                item_info =  dict((art_tag.replace('info','plot'),item(art_tag)[0].string) for art_tag in info_tags if item(art_tag)and item(art_tag)[0].string is not None)
          
            thumbnail = itemart.get("thumb")

            if not thumbnail and  len(item("thumbnail")) >0: #overwrite epg thumb if <thumbnail>
                try:
                    thumbnail=item('thumbnail')[0].string
                    if  thumbnail.startswith('$pyFunction:'):                
                        thumbnail=processPyFunction(thumbnail)
                    itemart['thumb'] = thumbnail 
                except:
                    pass
            elif not logo_folder == "":
                thumb = os.path.join(logo_folder , name.lower().replace(' ','')+'.png') 
                if xbmcvfs.exists(thumb):
            
                    itemart['thumb'] = thumb 
           
            if not itemart.get("fanart") :
                
                try:
                    fanart = item('fanart')[0].string
                    if not fanart:
                        raise
                    itemart['fanart'] = fanart
                except:
                    if use_thumb == 'true' and thumbnail:
                        itemart["fanart"] = thumbnail #thumbAsFanart                                
            if not item_info.get("plot"):
                item_info["plot"] = name
            item_info['showcontext'] = 'true'
            regexs = None
            if item('regex'):
                try:
                    reg_item = item('regex')
                    regexs = parse_regex(reg_item)
                except:
                    pass
            try:
                
                if len(url) > 1:
                    alt = 0
                    playlist = []
                    ignorelistsetting=True if '$$LSPlayOnlyOne$$' in url[0] else False
                    
                    for i in url:
                            if  add_playlist == "false" and not ignorelistsetting:
                                alt += 1
                                addLink(i,'%s) %s' %(alt, name.encode('utf-8', 'ignore')),itemart,item_info,regexs,total)
                            elif  (add_playlist == "true" and  ask_playlist_items == 'true') or ignorelistsetting:
                                if regexs:
                                    playlist.append(i+'&regexs='+regexs)
                                elif  any(x in i for x in resolve_url) and  i.startswith('http'):
                                    playlist.append(i+'&mode=19')
                                else:
                                    playlist.append(i)
                            elif ask_playlist_items == 'false' and "$$lsname=" in i:
                                playlist.append(i.split("$$lsname=")[0])
                            else:
                                playlist.append(i)
                    
                    if len(playlist) > 1:
                        item_info['playlist'] = playlist
                        addLink('', name.encode('utf-8'),itemart,item_info,regexs,total)
                else:
                    if dontLink:
                        return name,url[0],regexs
                    if isXMLSource:
                            if not regexs == None: #<externallink> and <regex>
                                item_info['showcontext'] = '!!update'
                                addDir(name.encode('utf-8'),ext_url[0].encode('utf-8'),1,itemart,item_info,regexs,url[0].encode('utf-8'))
                            #addLink(url[0],name.encode('utf-8', 'ignore')+  '[COLOR yellow]build XML[/COLOR]',thumbnail,fanArt,desc,genre,date,True,None,regexs,total)
                            else:
                                item_info['showcontext'] = 'source'
                                addDir(name.encode('utf-8'),ext_url[0].encode('utf-8'),1,itemart,item_info)
                            #addDir(name.encode('utf-8'),url[0].encode('utf-8'),1,thumbnail,fanart,desc,genre,date,None,'source')
                    elif isJsonrpc:
                        item_info['showcontext'] = 'source'
                        addDir(name.encode('utf-8'),ext_url[0],53,itemart,item_info)
                        #xbmc.executebuiltin("Container.SetViewMode(500)")
                    else:
                        
                        addLink(url[0],name.encode('utf-8', 'ignore'),itemart,item_info,regexs,total)
                    #print 'success'
            except:
                addon_log('There was a problem adding item - '+name.encode('utf-8', 'ignore'))

def parse_regex(reg_item):
                try:
                    regexs = {}
                    for i in reg_item:
                        regexs[i('name')[0].string] = {}
                        regexs[i('name')[0].string]['name']=i('name')[0].string
                        #regexs[i('name')[0].string]['expres'] = i('expres')[0].string
                        try:
                            regexs[i('name')[0].string]['expres'] = i('expres')[0].string
                            if not regexs[i('name')[0].string]['expres']:
                                regexs[i('name')[0].string]['expres']=''
                        except:
                            addon_log("Regex: -- No Referer --")
                        regexs[i('name')[0].string]['page'] = i('page')[0].string
                        try:
                            regexs[i('name')[0].string]['referer'] = i('referer')[0].string
                        except:
                            addon_log("Regex: -- No Referer --")
                        try:
                            regexs[i('name')[0].string]['connection'] = i('connection')[0].string
                        except:
                            addon_log("Regex: -- No connection --")

                        try:
                            regexs[i('name')[0].string]['notplayable'] = i('notplayable')[0].string
                        except:
                            addon_log("Regex: -- No notplayable --")

                        try:
                            regexs[i('name')[0].string]['noredirect'] = i('noredirect')[0].string
                        except:
                            addon_log("Regex: -- No noredirect --")
                        try:
                            regexs[i('name')[0].string]['origin'] = i('origin')[0].string
                        except:
                            addon_log("Regex: -- No origin --")
                        try:
                            regexs[i('name')[0].string]['accept'] = i('accept')[0].string
                        except:
                            addon_log("Regex: -- No accept --")
                        try:
                            regexs[i('name')[0].string]['includeheaders'] = i('includeheaders')[0].string
                        except:
                            addon_log("Regex: -- No includeheaders --")

                            
                        try:
                            regexs[i('name')[0].string]['listrepeat'] = i('listrepeat')[0].string
#                            print 'listrepeat',regexs[i('name')[0].string]['listrepeat'],i('listrepeat')[0].string, i
                        except:
                            addon_log("Regex: -- No listrepeat --")
                    
                            

                        try:
                            regexs[i('name')[0].string]['proxy'] = i('proxy')[0].string
                        except:
                            addon_log("Regex: -- No proxy --")
                            
                        try:
                            regexs[i('name')[0].string]['x-req'] = i('x-req')[0].string
                        except:
                            addon_log("Regex: -- No x-req --")

                        try:
                            regexs[i('name')[0].string]['x-addr'] = i('x-addr')[0].string
                        except:
                            addon_log("Regex: -- No x-addr --")                            
                            
                        try:
                            regexs[i('name')[0].string]['x-forward'] = i('x-forward')[0].string
                        except:
                            addon_log("Regex: -- No x-forward --")

                        try:
                            regexs[i('name')[0].string]['agent'] = i('agent')[0].string
                        except:
                            addon_log("Regex: -- No User Agent --")
                        try:
                            regexs[i('name')[0].string]['post'] = i('post')[0].string
                        except:
                            addon_log("Regex: -- Not a post")
                        try:
                            regexs[i('name')[0].string]['rawpost'] = i('rawpost')[0].string
                        except:
                            addon_log("Regex: -- Not a rawpost")
                        try:
                            regexs[i('name')[0].string]['htmlunescape'] = i('htmlunescape')[0].string
                        except:
                            addon_log("Regex: -- Not a htmlunescape")


                        try:
                            regexs[i('name')[0].string]['readcookieonly'] = i('readcookieonly')[0].string
                        except:
                            addon_log("Regex: -- Not a readCookieOnly")
                        #print i
                        try:
                            regexs[i('name')[0].string]['cookiejar'] = i('cookiejar')[0].string
                            if not regexs[i('name')[0].string]['cookiejar']:
                                regexs[i('name')[0].string]['cookiejar']=''
                        except:
                            addon_log("Regex: -- Not a cookieJar")
                        try:
                            regexs[i('name')[0].string]['setcookie'] = i('setcookie')[0].string
                        except:
                            addon_log("Regex: -- Not a setcookie")
                        try:
                            regexs[i('name')[0].string]['appendcookie'] = i('appendcookie')[0].string
                        except:
                            addon_log("Regex: -- Not a appendcookie")

                        try:
                            regexs[i('name')[0].string]['ignorecache'] = i('ignorecache')[0].string
                        except:
                            addon_log("Regex: -- no ignorecache")
                        #try:
                        #    regexs[i('name')[0].string]['ignorecache'] = i('ignorecache')[0].string
                        #except:
                        #    addon_log("Regex: -- no ignorecache")

                    regexs = urllib.quote(repr(regexs))
                    return regexs
                    #print regexs
                except:
                    regexs = None
                    addon_log('regex Error: '+name.encode('utf-8', 'ignore'))
#copies from lamda's implementation
def get_ustream(url):
    try:
        for i in range(1, 51):
            result = getUrl(url)
            if "EXT-X-STREAM-INF" in result: return url
            if not "EXTM3U" in result: return
            xbmc.sleep(2000)
        return
    except:
        return
def cacheKey(url):
    try:
        from hashlib import md5
        return md5(url).hexdigest()
    except:
        import md5
        return md5.new(url).hexdigest()
def RepeatedRegexs(regexs,url,name):
    data=None
    #deg((regexs,url,name))
    if regexs and 'listrepeat' in urllib.unquote_plus(regexs):
        listrepeat,ret,m,regexs, cookieJar =getRegexParsed(regexs, url)
        #print listrepeat,ret,m,regexs
        d=''
#        print 'm is' , m
#        print 'regexs',regexs
        regexname=m['name']
        existing_list=regexs.pop(regexname)
 #       print 'final regexs',regexs,regexname
        url=''
        import copy
        ln=''
        rnumber=0
        for obj in ret:
            #print 'obj',obj
            try:
                rnumber+=1

                newcopy=copy.deepcopy(regexs)
    #            print 'newcopy',newcopy, len(newcopy)
                listrepeatT=listrepeat
                i=0
                for i in range(len(obj)):
    #                print 'i is ',i, len(obj), len(newcopy)
                    if len(newcopy)>0:
                        for the_keyO, the_valueO in newcopy.iteritems():
                            if the_valueO is not None:
                                for the_key, the_value in the_valueO.iteritems():
                                    if the_value is not None:                                
        #                                print  'key and val',the_key, the_value
        #                                print 'aa'
        #                                print '[' + regexname+'.param'+str(i+1) + ']'
        #                                print repr(obj[i])
                                        if type(the_value) is dict:
                                            for the_keyl, the_valuel in the_value.iteritems():
                                                if the_valuel is not None:
                                                    val=None
                                                    if isinstance(obj,tuple):                                                    
                                                        try:
                                                           val= obj[i].decode('utf-8') 
                                                        except: 
                                                            val= obj[i] 
                                                    else:
                                                        try:
                                                            val= obj.decode('utf-8') 
                                                        except:
                                                            val= obj
                                                    
                                                    if '[' + regexname+'.param'+str(i+1) + '][DE]' in the_valuel:
                                                        the_valuel=the_valuel.replace('[' + regexname+'.param'+str(i+1) + '][DE]', unescape(val))
                                                    the_value[the_keyl]=the_valuel.replace('[' + regexname+'.param'+str(i+1) + ']', val)
                                                    
                                        else:
                                            val=None
                                            if isinstance(obj,tuple):
                                                try:
                                                     val=obj[i].decode('utf-8') 
                                                except:
                                                    val=obj[i] 
                                            else:
                                                try:
                                                    val= obj.decode('utf-8') 
                                                except:
                                                    val= obj
                                            if '[' + regexname+'.param'+str(i+1) + '][DE]' in the_value:
                                                #print 'found DE',the_value.replace('[' + regexname+'.param'+str(i+1) + '][DE]', unescape(val))
                                                the_value=the_value.replace('[' + regexname+'.param'+str(i+1) + '][DE]', unescape(val))

                                            the_valueO[the_key]=the_value.replace('[' + regexname+'.param'+str(i+1) + ']', val)
                                            #print 'second sec val',the_valueO[the_key]

                    val=None
                    if isinstance(obj,tuple):
                        try:
                            val=obj[i].decode('utf-8')
                        except:
                            val=obj[i]
                    else:
                        try:
                            val=obj.decode('utf-8')
                        except: 
                            val=obj
                    if '[' + regexname+'.param'+str(i+1) + '][DE]' in listrepeatT:
                        listrepeatT=listrepeatT.replace('[' + regexname+'.param'+str(i+1) + '][DE]',val)
                    listrepeatT=listrepeatT.replace('[' + regexname+'.param'+str(i+1) + ']',escape(val))
                listrepeatT=listrepeatT.replace('[' + regexname+'.param'+str(0) + ']',str(rnumber)) 
                
                try:
                    if cookieJar and '[' + regexname+'.cookies]' in listrepeatT:
                        listrepeatT=listrepeatT.replace('[' + regexname+'.cookies]',getCookiesString(cookieJar)) 
                except: pass
                
                #newcopy = urllib.quote(repr(newcopy))
    #            print 'new regex list', repr(newcopy), repr(listrepeatT)
    #            addLink(listlinkT,listtitleT.encode('utf-8', 'ignore'),listthumbnailT,'','','','',True,None,newcopy, len(ret))
                regex_xml=''
#                print 'newcopy',newcopy
                if len(newcopy)>0:
                    regex_xml=d2x(newcopy,'lsproroot')
                    regex_xml=regex_xml.split('<lsproroot>')[1].split('</lsproroot')[0]
              
                #ln+='\n<item>%s\n%s</item>'%(listrepeatT.encode("utf-8"),regex_xml)   
                try:
                    ln+='\n<item>%s\n%s</item>'%(listrepeatT,regex_xml)
                except: ln+='\n<item>%s\n%s</item>'%(listrepeatT.encode("utf-8"),regex_xml)
            except: traceback.print_exc(file=sys.stdout)
            #print repr(ln) #repr(ln)
#            print newcopy
                
#            ln+='</item>'

        getData('','',ln)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    else:
        url,setresolved = getRegexParsed(regexs, url)
        #deg((repr(url),setresolved,'imhere')) 
        if url:
            if '$PLAYERPROXY$=' in url:
                url,proxy=url.split('$PLAYERPROXY$=')
                print 'proxy',proxy
                #Jairox mod for proxy auth
                proxyuser = None
                proxypass = None
                if len(proxy) > 0 and '@' in proxy:
                    proxy = proxy.split(':')
                    proxyuser = proxy[0]
                    proxypass = proxy[1].split('@')[0]
                    proxyip = proxy[1].split('@')[1]
                    port = proxy[2]
                else:
                    proxyip,port=proxy.split(':')

                playmediawithproxy(url,name,iconimage,proxyip,port, proxyuser,proxypass) #jairox
            else:
                playsetresolved(url,name,setresolved,regexs)
        else:
            xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Failed to extract regex. - "+"this"+",4000,"+icon+")")
def getRegexParsed(regexs, url,cookieJar=None,forCookieJarOnly=False,recursiveCall=False,cachedPages={}, rawPost=False, cookie_jar_file=None):#0,1,2 = URL, regexOnly, CookieJarOnly
        if not recursiveCall:
            regexs = eval(urllib.unquote(regexs))
        #cachedPages = {}
        #print 'url',url
        doRegexs = re.compile('\$doregex\[([^\]]*)\]').findall(url)
#        print 'doRegexs',doRegexs,regexs
        setresolved=True
        for k in doRegexs:
            if k in regexs:
                #print 'processing ' ,k
                m = regexs[k]
                #print m
                cookieJarParam=False
                if  'cookiejar' in m: # so either create or reuse existing jar
                    #print 'cookiejar exists',m['cookiejar']
                    cookieJarParam=m['cookiejar']
                    if  '$doregex' in cookieJarParam:
                        cookieJar=getRegexParsed(regexs, m['cookiejar'],cookieJar,True, True,cachedPages)
                        
                        cookieJarParam=True
                    else:
                        cookieJarParam=True
                #print 'm[cookiejar]',m['cookiejar'],cookieJar
                if cookieJarParam:
                    if cookieJar==None:
                        #print 'create cookie jar'
                        cookie_jar_file=None
                        if 'open[' in m['cookiejar']:
                            cookie_jar_file=m['cookiejar'].split('open[')[1].split(']')[0]
#                            print 'cookieJar from file name',cookie_jar_file

                        cookieJar=getCookieJar(cookie_jar_file)
#                        print 'cookieJar from file',cookieJar
                        if cookie_jar_file:
                            saveCookieJar(cookieJar,cookie_jar_file)
                        #import cookielib
                        #cookieJar = cookielib.LWPCookieJar()
                        #print 'cookieJar new',cookieJar
                    elif 'save[' in m['cookiejar']:
                        cookie_jar_file=m['cookiejar'].split('save[')[1].split(']')[0]
                        complete_path=os.path.join(profile,cookie_jar_file)
#                        print 'complete_path',complete_path
                        saveCookieJar(cookieJar,cookie_jar_file)
                if  m['page'] and '$doregex' in m['page']:
                    pg=getRegexParsed(regexs, m['page'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
                    if len(pg)==0:
                        pg='http://regexfailed'
                    m['page']=pg

                if 'setcookie' in m and m['setcookie'] and '$doregex' in m['setcookie']:
                    m['setcookie']=getRegexParsed(regexs, m['setcookie'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
                if 'appendcookie' in m and m['appendcookie'] and '$doregex' in m['appendcookie']:
                    m['appendcookie']=getRegexParsed(regexs, m['appendcookie'],cookieJar,recursiveCall=True,cachedPages=cachedPages)


                if  'post' in m and '$doregex' in m['post']:
                    m['post']=getRegexParsed(regexs, m['post'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
#                    print 'post is now',m['post']

                if  'rawpost' in m and '$doregex' in m['rawpost']:
                    m['rawpost']=getRegexParsed(regexs, m['rawpost'],cookieJar,recursiveCall=True,cachedPages=cachedPages,rawPost=True)
                    #print 'rawpost is now',m['rawpost']

                if 'rawpost' in m and '$epoctime$' in m['rawpost']:
                    m['rawpost']=m['rawpost'].replace('$epoctime$',getEpocTime())

                if 'rawpost' in m and '$epoctime2$' in m['rawpost']:
                    m['rawpost']=m['rawpost'].replace('$epoctime2$',getEpocTime2())


                link=''
                if m['page'] and m['page'] in cachedPages and not 'ignorecache' in m and forCookieJarOnly==False :
                    #print 'using cache page',m['page']
                    link = cachedPages[m['page']]
                else:
                    if m['page'] and  not m['page']=='' and  m['page'].startswith('http'):
                        if '$epoctime$' in m['page']:
                            m['page']=m['page'].replace('$epoctime$',getEpocTime())
                        if '$epoctime2$' in m['page']:
                            m['page']=m['page'].replace('$epoctime2$',getEpocTime2())

                        #print 'Ingoring Cache',m['page']
                        page_split=m['page'].split('|')
                        pageUrl=page_split[0]
                        header_in_page=None
                        if len(page_split)>1:
                            header_in_page=page_split[1]

#                            if 
#                            proxy = urllib2.ProxyHandler({ ('https' ? proxytouse[:5]=="https":"http") : proxytouse})
#                            opener = urllib2.build_opener(proxy)
#                            urllib2.install_opener(opener)

                            
                        
#                        import urllib2
#                        print 'urllib2.getproxies',urllib2.getproxies()
                        current_proxies=urllib2.ProxyHandler(urllib2.getproxies())
        
        
                        #print 'getting pageUrl',pageUrl
                        req = urllib2.Request(pageUrl)
                        if 'proxy' in m:
                            proxytouse= m['proxy']
#                            print 'proxytouse',proxytouse
#                            urllib2.getproxies= lambda: {}
                            if pageUrl[:5]=="https":
                                proxy = urllib2.ProxyHandler({ 'https' : proxytouse})
                                #req.set_proxy(proxytouse, 'https')
                            else:
                                proxy = urllib2.ProxyHandler({ 'http'  : proxytouse})
                                #req.set_proxy(proxytouse, 'http')
                            opener = urllib2.build_opener(proxy)
                            urllib2.install_opener(opener)
                            
                        
                        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
                        proxytouse=None

                        if 'referer' in m:
                            req.add_header('Referer', m['referer'])
                        if 'accept' in m:
                            req.add_header('Accept', m['accept'])
                        if 'agent' in m:
                            req.add_header('User-agent', m['agent'])
                        if 'x-req' in m:
                            req.add_header('X-Requested-With', m['x-req'])
                        if 'x-addr' in m:
                            req.add_header('x-addr', m['x-addr'])
                        if 'x-forward' in m:
                            req.add_header('X-Forwarded-For', m['x-forward'])
                        if 'setcookie' in m:
#                            print 'adding cookie',m['setcookie']
                            req.add_header('Cookie', m['setcookie'])
                        if 'appendcookie' in m:
#                            print 'appending cookie to cookiejar',m['appendcookie']
                            cookiestoApend=m['appendcookie']
                            cookiestoApend=cookiestoApend.split(';')
                            for h in cookiestoApend:
                                n,v=h.split('=')
                                w,n= n.split(':')
                                ck = cookielib.Cookie(version=0, name=n, value=v, port=None, port_specified=False, domain=w, domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
                                cookieJar.set_cookie(ck)
                        if 'origin' in m:
                            req.add_header('Origin', m['origin'])
                        if header_in_page:
                            header_in_page=header_in_page.split('&')
                            for h in header_in_page:
                                if h.split('=')==2:
                                    n,v=h.split('=')
                                else:
                                    vals=h.split('=')
                                    n=vals[0]
                                    v='='.join(vals[1:])
                                #n,v=h.split('=')
                                req.add_header(n,v)
                        
                        if not cookieJar==None:
#                            print 'cookieJarVal',cookieJar
                            cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
                            opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
                            opener = urllib2.install_opener(opener)
#                            print 'noredirect','noredirect' in m
                            
                            if 'noredirect' in m:
                                opener = urllib2.build_opener(cookie_handler,NoRedirection, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
                                opener = urllib2.install_opener(opener)
                        elif 'noredirect' in m:
                            opener = urllib2.build_opener(NoRedirection, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
                            opener = urllib2.install_opener(opener)
                            

                        if 'connection' in m:
#                            print '..........................connection//////.',m['connection']
                            from keepalive import HTTPHandler
                            keepalive_handler = HTTPHandler()
                            opener = urllib2.build_opener(keepalive_handler)
                            urllib2.install_opener(opener)


                        #print 'after cookie jar'
                        post=None

                        if 'post' in m:
                            postData=m['post']
                            #if '$LiveStreamRecaptcha' in postData:
                            #    (captcha_challenge,catpcha_word,idfield)=processRecaptcha(m['page'],cookieJar)
                            #    if captcha_challenge:
                            #        postData=postData.replace('$LiveStreamRecaptcha','manual_recaptcha_challenge_field:'+captcha_challenge+',recaptcha_response_field:'+catpcha_word+',id:'+idfield)
                            splitpost=postData.split(',');
                            post={}
                            for p in splitpost:
                                n=p.split(':')[0];
                                v=p.split(':')[1];
                                post[n]=v
                            post = urllib.urlencode(post)

                        if 'rawpost' in m:
                            post=m['rawpost']
                            #if '$LiveStreamRecaptcha' in post:
                            #    (captcha_challenge,catpcha_word,idfield)=processRecaptcha(m['page'],cookieJar)
                            #    if captcha_challenge:
                            #       post=post.replace('$LiveStreamRecaptcha','&manual_recaptcha_challenge_field='+captcha_challenge+'&recaptcha_response_field='+catpcha_word+'&id='+idfield)
                        link=''
                        try:
                            
                            if post:
                                response = urllib2.urlopen(req,post)
                            else:
                                response = urllib2.urlopen(req)
                            if response.info().get('Content-Encoding') == 'gzip':
                                from StringIO import StringIO
                                import gzip
                                buf = StringIO( response.read())
                                f = gzip.GzipFile(fileobj=buf)
                                link = f.read()
                            else:
                                link=response.read()
                            
                        
                        
                            if 'proxy' in m and not current_proxies is None:
                                urllib2.install_opener(urllib2.build_opener(current_proxies))
                            
                            link=javascriptUnEscape(link)
                            #print repr(link)
                            #print link This just print whole webpage in LOG
                            if 'includeheaders' in m:
                                #link+=str(response.headers.get('Set-Cookie'))
                                link+='$$HEADERS_START$$:'
                                for b in response.headers:
                                    link+= b+':'+response.headers.get(b)+'\n'
                                link+='$$HEADERS_END$$:'
    #                        print link
                            addon_log(link)
                            addon_log(cookieJar )

                            response.close()
                        except: 
                            pass
                        cachedPages[m['page']] = link
                        #print link
                        #print 'store link for',m['page'],forCookieJarOnly

                        if forCookieJarOnly:
                            return cookieJar# do nothing
                    elif m['page'] and  not m['page'].startswith('http'):
                        if m['page'].startswith('$pyFunction:'):
                            val=doEval(m['page'].split('$pyFunction:')[1],'',cookieJar,m )
                            if forCookieJarOnly:
                                return cookieJar# do nothing
                            link=val
                            link=javascriptUnEscape(link)
                        else:
                            link=m['page']
                if '$pyFunction:playmedia(' in m['expres'] or 'ActivateWindow'  in m['expres'] or 'RunPlugin'  in m['expres']  or '$PLAYERPROXY$=' in url  or  any(x in url for x in g_ignoreSetResolved):
                    setresolved=False
                if  '$doregex' in m['expres']:
                    m['expres']=getRegexParsed(regexs, m['expres'],cookieJar,recursiveCall=True,cachedPages=cachedPages)
                  
                if not m['expres']=='':
                    #print 'doing it ',m['expres']
                    if '$LiveStreamCaptcha' in m['expres']:
                        val=askCaptcha(m,link,cookieJar)
                        #print 'url and val',url,val
                        url = url.replace("$doregex[" + k + "]", val)

                    elif m['expres'].startswith('$pyFunction:') or '#$pyFunction' in m['expres']:
                        #print 'expeeeeeeeeeeeeeeeeeee',m['expres']
                        val=''
                        if m['expres'].startswith('$pyFunction:'):
                            val=doEval(m['expres'].split('$pyFunction:')[1],link,cookieJar,m)
                        else:
                            val=doEvalFunction(m['expres'],link,cookieJar,m)
                        if 'ActivateWindow' in m['expres'] or 'RunPlugin' in m['expres']  : return '',False
                        if forCookieJarOnly:
                            return cookieJar# do nothing
                        if 'listrepeat' in m:
                            listrepeat=m['listrepeat']                            
                            #ret=re.findall(m['expres'],link)
                            #print 'ret',val
                            return listrepeat,eval(val), m,regexs,cookieJar
#                        print 'url k val',url,k,val
                        #print 'repr',repr(val)
                        
                        try:
                            url = url.replace(u"$doregex[" + k + "]", val)
                        except: url = url.replace("$doregex[" + k + "]", val.decode("utf-8"))
                    else:
                        if 'listrepeat' in m:
                            listrepeat=m['listrepeat']
                            #print 'listrepeat',m['expres']
                            #print m['expres']
                            #print 'aaaa'
                            #print link
                            ret=re.findall(m['expres'],link)
                            #print 'ret',ret
                            return listrepeat,ret, m,regexs,cookieJar
                             
                        val=''
                        if not link=='':
                            #print 'link',link
                            reg = re.compile(m['expres']).search(link)                            
                            try:
                                val=reg.group(1).strip()
                            except: traceback.print_exc()
                        elif m['page']=='' or m['page']==None:
                            val=m['expres']
                            
                        if rawPost:
#                            print 'rawpost'
                            val=urllib.quote_plus(val)
                        if 'htmlunescape' in m:
                            #val=urllib.unquote_plus(val)
                            import HTMLParser
                            val=HTMLParser.HTMLParser().unescape(val)
                        try:
                            url = url.replace("$doregex[" + k + "]", val)
                        except: url = url.replace("$doregex[" + k + "]", val.decode("utf-8"))
                        #print 'ur',url
                        #return val
                else:
                    url = url.replace("$doregex[" + k + "]",'')
        if '$epoctime$' in url:
            url=url.replace('$epoctime$',getEpocTime())
        if '$epoctime2$' in url:
            url=url.replace('$epoctime2$',getEpocTime2())

        if '$GUID$' in url:
            import uuid
            url=url.replace('$GUID$',str(uuid.uuid1()).upper())
        if '$get_cookies$' in url:
            url=url.replace('$get_cookies$',getCookiesString(cookieJar))

        if recursiveCall: return url
        #print 'final url',repr(url)
        if url=="":
            return
        else:
            return url,setresolved

 
def getmd5(t):
    import hashlib
    h=hashlib.md5()
    h.update(t)
    return h.hexdigest()

def decrypt_vaughnlive(encrypted):
    retVal=""
#    print 'enc',encrypted
    #for val in encrypted.split(':'):
    #    retVal+=chr(int(val.replace("0m0","")))
    #return retVal

def playmedia(media_url):
    try:
        import  CustomPlayer
        player = CustomPlayer.MyXBMCPlayer()
        listitem = xbmcgui.ListItem( label = str(name), iconImage = "DefaultVideo.png", thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=media_url )
        player.play( media_url,listitem)
        xbmc.sleep(1000)
        while player.is_active:
            xbmc.sleep(200)
    except:
        traceback.print_exc()
    return ''

def kodiJsonRequest(params):
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return None
    except KeyError:
        logger.warn("[%s] %s" % (params['method'], response['error']['message']))
        return None


def setKodiProxy(proxysettings=None):

    if proxysettings==None:
#        print 'proxy set to nothing'
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.usehttpproxy", "value":false}, "id":1}')
    else:
        
        ps=proxysettings.split(':')
        proxyURL=ps[0]
        proxyPort=ps[1]
        proxyType=ps[2]
        proxyUsername=None
        proxyPassword=None
        
        if len(ps)>3 and '@' in ps[3]: #jairox ###proxysettings
            proxyUsername=ps[3].split('@')[0] #jairox ###ps[3]
            proxyPassword=ps[3].split('@')[1] #jairox ###proxysettings.split('@')[-1]

#        print 'proxy set to', proxyType, proxyURL,proxyPort
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.usehttpproxy", "value":true}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.httpproxytype", "value":' + str(proxyType) +'}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.httpproxyserver", "value":"' + str(proxyURL) +'"}, "id":1}')
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.httpproxyport", "value":' + str(proxyPort) +'}, "id":1}')
        
        
        if not proxyUsername==None:
            xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.httpproxyusername", "value":"' + str(proxyUsername) +'"}, "id":1}')
            xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"network.httpproxypassword", "value":"' + str(proxyPassword) +'"}, "id":1}')

        
def getConfiguredProxy():
    proxyActive = kodiJsonRequest({'jsonrpc': '2.0', "method":"Settings.GetSettingValue", "params":{"setting":"network.usehttpproxy"}, 'id': 1})['value']
#    print 'proxyActive',proxyActive
    proxyType = kodiJsonRequest({'jsonrpc': '2.0', "method":"Settings.GetSettingValue", "params":{"setting":"network.httpproxytype"}, 'id': 1})['value']

    if proxyActive: # PROXY_HTTP
        proxyURL = kodiJsonRequest({'jsonrpc': '2.0', "method":"Settings.GetSettingValue", "params":{"setting":"network.httpproxyserver"}, 'id': 1})['value']
        proxyPort = unicode(kodiJsonRequest({'jsonrpc': '2.0', "method":"Settings.GetSettingValue", "params":{"setting":"network.httpproxyport"}, 'id': 1})['value'])
        proxyUsername = kodiJsonRequest({'jsonrpc': '2.0', "method":"Settings.GetSettingValue", "params":{"setting":"network.httpproxyusername"}, 'id': 1})['value']
        proxyPassword = kodiJsonRequest({'jsonrpc': '2.0', "method":"Settings.GetSettingValue", "params":{"setting":"network.httpproxypassword"}, 'id': 1})['value']

        if proxyUsername and proxyPassword and proxyURL and proxyPort:
            return proxyURL + ':' + str(proxyPort)+':'+str(proxyType) + ':' + proxyUsername + '@' + proxyPassword
        elif proxyURL and proxyPort:
            return proxyURL + ':' + str(proxyPort)+':'+str(proxyType)
    else:
        return None
        
def playmediawithproxy(media_url, name, iconImage,proxyip,port, proxyuser=None, proxypass=None): #jairox

    if media_url==None or media_url=='':
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Unable to play empty Url,5000,"+icon+")")
        return
    progress = xbmcgui.DialogProgress()
    progress.create('Progress', 'Playing with custom proxy')
    progress.update( 10, "", "setting proxy..", "" )
    proxyset=False
    existing_proxy=''
    #print 'playmediawithproxy'
    try:
        
        existing_proxy=getConfiguredProxy()
        print 'existing_proxy',existing_proxy
        #read and set here
        #jairox
        if not proxyuser == None:
            setKodiProxy( proxyip + ':' + port + ':0:' + proxyuser + '@' + proxypass)
        else:
            setKodiProxy( proxyip + ':' + port + ':0')

        print 'proxy setting complete playing',media_url
        proxyset=True
        progress.update( 80, "", "setting proxy complete, now playing", "" )
        
        import  CustomPlayer
        player = CustomPlayer.MyXBMCPlayer()
        player.pdialogue==progress
        listitem = xbmcgui.ListItem( label = str(name), iconImage = iconImage, thumbnailImage = xbmc.getInfoImage( "ListItem.Thumb" ), path=media_url )
        player.play( media_url,listitem)
        xbmc.sleep(1000)
        #while player.is_active:
        #    xbmc.sleep(200)
        import time
        beforestart=time.time()
        try:
            while player.is_active:
                xbmc.sleep(1000)       
                if player.urlplayed==False and time.time()-beforestart>12:
                    print 'failed!!!'
                    xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Unable to play check proxy,5000,"+icon+")")
                    break
                #xbmc.sleep(1000)
        except: pass

        progress.close()
        progress=None
    except:
        traceback.print_exc()
    if progress:
        progress.close()
    if proxyset:
#        print 'now resetting the proxy back'
        setKodiProxy(existing_proxy)
#        print 'reset here'
    return ''


def get_saw_rtmp(page_value, referer=None):
    if referer:
        referer=[('Referer',referer)]
    if page_value.startswith("http"):
        page_url=page_value
        page_value= getUrl(page_value,headers=referer)

    str_pattern="(eval\(function\(p,a,c,k,e,(?:r|d).*)"

    reg_res=re.compile(str_pattern).findall(page_value)
    r=""
    if reg_res and len(reg_res)>0:
        for v in reg_res:
            r1=get_unpacked(v)
            r2=re_me(r1,'\'(.*?)\'')
            if 'unescape' in r1:
                r1=urllib.unquote(r2)
            r+=r1+'\n'
#        print 'final value is ',r

        page_url=re_me(r,'src="(.*?)"')

        page_value= getUrl(page_url,headers=referer)

    #print page_value

    rtmp=re_me(page_value,'streamer\'.*?\'(.*?)\'\)')
    playpath=re_me(page_value,'file\',\s\'(.*?)\'')


    return rtmp+' playpath='+playpath +' pageUrl='+page_url

def get_leton_rtmp(page_value, referer=None):
    if referer:
        referer=[('Referer',referer)]
    if page_value.startswith("http"):
        page_value= getUrl(page_value,headers=referer)
    str_pattern="var a = (.*?);\s*var b = (.*?);\s*var c = (.*?);\s*var d = (.*?);\s*var f = (.*?);\s*var v_part = '(.*?)';"
    reg_res=re.compile(str_pattern).findall(page_value)[0]

    a,b,c,d,f,v=(reg_res)
    f=int(f)
    a=int(a)/f
    b=int(b)/f
    c=int(c)/f
    d=int(d)/f

    ret= 'rtmp://' + str(a) + '.' + str(b) + '.' + str(c) + '.' + str(d) + v;
    return ret

def createM3uForDash(url,useragent=None):
    str='#EXTM3U'
    str+='\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=361816'
    str+='\n'+url+'&bytes=0-200000'#+'|User-Agent='+useragent
    source_file = os.path.join(profile, 'testfile.m3u')
    str+='\n'
    SaveToFile(source_file,str)
    #return 'C:/Users/shani/Downloads/test.m3u8'
    return source_file

def SaveToFile(file_name,page_data,append=False):
    if append:
        f = open(file_name, 'a')
        f.write(page_data)
        f.close()
    else:
        f=open(file_name,'wb')
        f.write(page_data)
        f.close()
        return ''

def LoadFile(file_name):
    f=open(file_name,'rb')
    d=f.read()
    f.close()
    return d

def get_packed_iphonetv_url(page_data):
    import re,base64,urllib;
    s=page_data
    while 'geh(' in s:
        if s.startswith('lol('): s=s[5:-1]
#       print 's is ',s
        s=re.compile('"(.*?)"').findall(s)[0];
        s=  base64.b64decode(s);
        s=urllib.unquote(s);
    print s
    return s

def get_ferrari_url(page_data):
#    print 'get_dag_url2',page_data
    page_data2=getUrl(page_data);
    patt='(http.*)'
    import uuid
    playback=str(uuid.uuid1()).upper()
    links=re.compile(patt).findall(page_data2)
    headers=[('X-Playback-Session-Id',playback)]
    for l in links:
        try:
                page_datatemp=getUrl(l,headers=headers);

        except: pass

    return page_data+'|&X-Playback-Session-Id='+playback


def get_dag_url(page_data):
#    print 'get_dag_url',page_data
    if page_data.startswith('http://dag.total-stream.net'):
        headers=[('User-Agent','Verismo-BlackUI_(2.4.7.5.8.0.34)')]
        page_data=getUrl(page_data,headers=headers);

    if '127.0.0.1' in page_data:
        return revist_dag(page_data)
    elif re_me(page_data, 'wmsAuthSign%3D([^%&]+)') != '':
        final_url = re_me(page_data, '&ver_t=([^&]+)&') + '?wmsAuthSign=' + re_me(page_data, 'wmsAuthSign%3D([^%&]+)') + '==/mp4:' + re_me(page_data, '\\?y=([^&]+)&')
    else:
        final_url = re_me(page_data, 'href="([^"]+)"[^"]+$')
        if len(final_url)==0:
            final_url=page_data
    final_url = final_url.replace(' ', '%20')
    return final_url

def re_me(data, re_patten):
    match = ''
    m = re.search(re_patten, data)
    if m != None:
        match = m.group(1)
    else:
        match = ''
    return match

def revist_dag(page_data):
    final_url = ''
    if '127.0.0.1' in page_data:
        final_url = re_me(page_data, '&ver_t=([^&]+)&') + ' live=true timeout=15 playpath=' + re_me(page_data, '\\?y=([a-zA-Z0-9-_\\.@]+)')

    if re_me(page_data, 'token=([^&]+)&') != '':
        final_url = final_url + '?token=' + re_me(page_data, 'token=([^&]+)&')
    elif re_me(page_data, 'wmsAuthSign%3D([^%&]+)') != '':
        final_url = re_me(page_data, '&ver_t=([^&]+)&') + '?wmsAuthSign=' + re_me(page_data, 'wmsAuthSign%3D([^%&]+)') + '==/mp4:' + re_me(page_data, '\\?y=([^&]+)&')
    else:
        final_url = re_me(page_data, 'HREF="([^"]+)"')

    if 'dag1.asx' in final_url:
        return get_dag_url(final_url)

    if 'devinlivefs.fplive.net' not in final_url:
        final_url = final_url.replace('devinlive', 'flive')
    if 'permlivefs.fplive.net' not in final_url:
        final_url = final_url.replace('permlive', 'flive')
    return final_url


def get_unwise( str_eval):
    page_value=""
    try:
        ss="w,i,s,e=("+str_eval+')'
        exec (ss)
        page_value=unwise_func(w,i,s,e)
    except: traceback.print_exc(file=sys.stdout)
    #print 'unpacked',page_value
    return page_value

def unwise_func( w, i, s, e):
    lIll = 0;
    ll1I = 0;
    Il1l = 0;
    ll1l = [];
    l1lI = [];
    while True:
        if (lIll < 5):
            l1lI.append(w[lIll])
        elif (lIll < len(w)):
            ll1l.append(w[lIll]);
        lIll+=1;
        if (ll1I < 5):
            l1lI.append(i[ll1I])
        elif (ll1I < len(i)):
            ll1l.append(i[ll1I])
        ll1I+=1;
        if (Il1l < 5):
            l1lI.append(s[Il1l])
        elif (Il1l < len(s)):
            ll1l.append(s[Il1l]);
        Il1l+=1;
        if (len(w) + len(i) + len(s) + len(e) == len(ll1l) + len(l1lI) + len(e)):
            break;

    lI1l = ''.join(ll1l)#.join('');
    I1lI = ''.join(l1lI)#.join('');
    ll1I = 0;
    l1ll = [];
    for lIll in range(0,len(ll1l),2):
        #print 'array i',lIll,len(ll1l)
        ll11 = -1;
        if ( ord(I1lI[ll1I]) % 2):
            ll11 = 1;
        #print 'val is ', lI1l[lIll: lIll+2]
        l1ll.append(chr(    int(lI1l[lIll: lIll+2], 36) - ll11));
        ll1I+=1;
        if (ll1I >= len(l1lI)):
            ll1I = 0;
    ret=''.join(l1ll)
    if 'eval(function(w,i,s,e)' in ret:
#        print 'STILL GOing'
        ret=re.compile('eval\(function\(w,i,s,e\).*}\((.*?)\)').findall(ret)[0]
        return get_unwise(ret)
    else:
#        print 'FINISHED'
        return ret

def get_unpacked( page_value, regex_for_text='', iterations=1, total_iteration=1):
    try:
        reg_data=None
        if page_value.startswith("http"):
            page_value= getUrl(page_value)
#        print 'page_value',page_value
        if regex_for_text and len(regex_for_text)>0:
            try:
                page_value=re.compile(regex_for_text).findall(page_value)[0] #get the js variable
            except: return 'NOTPACKED'

        page_value=unpack(page_value,iterations,total_iteration)
    except:
        page_value='UNPACKEDFAILED'
        traceback.print_exc(file=sys.stdout)
#    print 'unpacked',page_value
    if 'sav1live.tv' in page_value:
        page_value=page_value.replace('sav1live.tv','sawlive.tv') #quick fix some bug somewhere
#        print 'sav1 unpacked',page_value
    return page_value

def unpack(sJavascript,iteration=1, totaliterations=2  ):
#    print 'iteration',iteration
    if sJavascript.startswith('var _0xcb8a='):
        aSplit=sJavascript.split('var _0xcb8a=')
        ss="myarray="+aSplit[1].split("eval(")[0]
        exec(ss)
        a1=62
        c1=int(aSplit[1].split(",62,")[1].split(',')[0])
        p1=myarray[0]
        k1=myarray[3]
        with open('temp file'+str(iteration)+'.js', "wb") as filewriter:
            filewriter.write(str(k1))
        #aa=1/0
    else:

        if "rn p}('" in sJavascript:
            aSplit = sJavascript.split("rn p}('")
        else:
            aSplit = sJavascript.split("rn A}('")
#        print aSplit

        p1,a1,c1,k1=('','0','0','')

        ss="p1,a1,c1,k1=('"+aSplit[1].split(".spli")[0]+')'
        exec(ss)
    k1=k1.split('|')
    aSplit = aSplit[1].split("))'")
#    print ' p array is ',len(aSplit)
#   print len(aSplit )

    #p=str(aSplit[0]+'))')#.replace("\\","")#.replace('\\\\','\\')

    #print aSplit[1]
    #aSplit = aSplit[1].split(",")
    #print aSplit[0]
    #a = int(aSplit[1])
    #c = int(aSplit[2])
    #k = aSplit[3].split(".")[0].replace("'", '').split('|')
    #a=int(a)
    #c=int(c)

    #p=p.replace('\\', '')
#    print 'p val is ',p[0:100],'............',p[-100:],len(p)
#    print 'p1 val is ',p1[0:100],'............',p1[-100:],len(p1)

    #print a,a1
    #print c,a1
    #print 'k val is ',k[-10:],len(k)
#    print 'k1 val is ',k1[-10:],len(k1)
    e = ''
    d = ''#32823

    #sUnpacked = str(__unpack(p, a, c, k, e, d))
    sUnpacked1 = str(__unpack(p1, a1, c1, k1, e, d,iteration))

    #print sUnpacked[:200]+'....'+sUnpacked[-100:], len(sUnpacked)
#    print sUnpacked1[:200]+'....'+sUnpacked1[-100:], len(sUnpacked1)

    #exec('sUnpacked1="'+sUnpacked1+'"')
    if iteration>=totaliterations:
#        print 'final res',sUnpacked1[:200]+'....'+sUnpacked1[-100:], len(sUnpacked1)
        return sUnpacked1#.replace('\\\\', '\\')
    else:
#        print 'final res for this iteration is',iteration
        return unpack(sUnpacked1,iteration+1)#.replace('\\', ''),iteration)#.replace('\\', '');#unpack(sUnpacked.replace('\\', ''))

def __unpack(p, a, c, k, e, d, iteration,v=1):

    #with open('before file'+str(iteration)+'.js', "wb") as filewriter:
    #    filewriter.write(str(p))
    while (c >= 1):
        c = c -1
        if (k[c]):
            aa=str(__itoaNew(c, a))
            if v==1:
                p=re.sub('\\b' + aa +'\\b', k[c], p)# THIS IS Bloody slow!
            else:
                p=findAndReplaceWord(p,aa,k[c])

            #p=findAndReplaceWord(p,aa,k[c])


    #with open('after file'+str(iteration)+'.js', "wb") as filewriter:
    #    filewriter.write(str(p))
    return p

#
#function equalavent to re.sub('\\b' + aa +'\\b', k[c], p)
def findAndReplaceWord(source_str, word_to_find,replace_with):
    splits=None
    splits=source_str.split(word_to_find)
    if len(splits)>1:
        new_string=[]
        current_index=0
        for current_split in splits:
            #print 'here',i
            new_string.append(current_split)
            val=word_to_find#by default assume it was wrong to split

            #if its first one and item is blank then check next item is valid or not
            if current_index==len(splits)-1:
                val='' # last one nothing to append normally
            else:
                if len(current_split)==0: #if blank check next one with current split value
                    if ( len(splits[current_index+1])==0 and word_to_find[0].lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_') or (len(splits[current_index+1])>0  and splits[current_index+1][0].lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_'):# first just just check next
                        val=replace_with
                #not blank, then check current endvalue and next first value
                else:
                    if (splits[current_index][-1].lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_') and (( len(splits[current_index+1])==0 and word_to_find[0].lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_') or (len(splits[current_index+1])>0  and splits[current_index+1][0].lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890_')):# first just just check next
                        val=replace_with

            new_string.append(val)
            current_index+=1
        #aaaa=1/0
        source_str=''.join(new_string)
    return source_str

def __itoa(num, radix):
#    print 'num red',num, radix
    result = ""
    if num==0: return '0'
    while num > 0:
        result = "0123456789abcdefghijklmnopqrstuvwxyz"[num % radix] + result
        num /= radix
    return result

def __itoaNew(cc, a):
    aa="" if cc < a else __itoaNew(int(cc / a),a)
    cc = (cc % a)
    bb=chr(cc + 29) if cc> 35 else str(__itoa(cc,36))
    return aa+bb


def getCookiesString(cookieJar):
    try:
        cookieString=""
        for index, cookie in enumerate(cookieJar):
            cookieString+=cookie.name + "=" + cookie.value +";"
    except: pass
    #print 'cookieString',cookieString
    return cookieString


def saveCookieJar(cookieJar,COOKIEFILE):
    try:
        complete_path=os.path.join(profile,COOKIEFILE)
        cookieJar.save(complete_path,ignore_discard=True)
    except: pass

def getCookieJar(COOKIEFILE):

    cookieJar=None
    if COOKIEFILE:
        try:
            complete_path=os.path.join(profile,COOKIEFILE)
            cookieJar = cookielib.LWPCookieJar()
            cookieJar.load(complete_path,ignore_discard=True)
        except:
            cookieJar=None

    if not cookieJar:
        cookieJar = cookielib.LWPCookieJar()

    return cookieJar

def doEval(fun_call,page_data,Cookie_Jar,m,functions_dir=None):
    ret_val=''
    #print fun_call
    #xbmc.log('functiondir doEval %s' %str(functions_dir), xbmc.LOGNOTICE)
    if functions_dir == None:
        functions_dir = profile
    else:
        functions_dir = functions_dir
    if functions_dir not in sys.path:
        sys.path.insert(0,functions_dir)
    #xbmc.log('functiondir doEval %s' %str(sys.path), xbmc.LOGNOTICE)
#    print fun_call
    try:
        py_file='import '+fun_call.split('.')[0]
#        print py_file,sys.path
        exec( py_file)
#        print 'done'
    except:
        #print 'error in import'
        traceback.print_exc(file=sys.stdout)
#    print 'ret_val='+fun_call
    exec ('ret_val='+fun_call)
#    print ret_val
    #exec('ret_val=1+1')
    try:
        return str(ret_val)
    except: return ret_val
#def doEvalFunction2

def Func_in_externallink (fun_call,libpyCode=libpyCode,searchterm=''):
#    print 'doEvalFunction'
    if fun_call.startswith('$pyFunction'):
        fun_call =fun_call.split('$pyFunction:')[1]
        s=doEval(fun_call, '', '', '', libpyCode)
        return s
        
    if not os.path.exists(libpyCode):
        xbmcvfs.mkdir(libpyCode)
    
        
    ret_val=''

    sys.path.insert(0,libpyCode)
    getfilekey = 'py'+cacheKey(fun_call)
    fun_call = fun_call.replace('LSProdynamicCode',getfilekey)
    wrifile =    os.path.join(libpyCode,getfilekey+'.py')
    if not os.path.isfile(wrifile):
        f=open(wrifile,"wb")
        f.write("# -*- coding: utf-8 -*-\n")
        if not (libpyCode == home or libpyCode == profile):
            f.write('import sys\nsys.path.insert(0,r",'+home+'")\n')
        f.write(fun_call.encode("utf-8"));
        
        f.close()
    LSProdynamicCode = __import__(getfilekey)
    ret_val=LSProdynamicCode.GetLSProData('','',searchterm)
    try:
        return str(ret_val)
    except: return ret_val

def doEvalFunction(fun_call,page_data,Cookie_Jar,m,functions_dir=None):
#    print 'doEvalFunction'
    ret_val=''
    if not functions_dir:
        functions_dir = profile    

        filename = 'LSProdynamicCode.py'
        sys.path.insert(0,functions_dir)
    else:
        filename = 'LSProdynamicCode.py'
    #if functions_dir not in sys.path :
        sys.path.insert(0,functions_dir)        
    code_path = os.path.join(functions_dir,filename)
    xbmc.log("functions_dir",xbmc.LOGNOTICE)    
    xbmc.log(str(functions_dir),xbmc.LOGNOTICE)    
    xbmc.log(str(code_path),xbmc.LOGNOTICE)    
    f=open(code_path,"wb")
    f.write("# -*- coding: utf-8 -*-\n")
    f.write(fun_call.encode("utf-8"));
    
    f.close()
    if '/' in code_path:
        LSProdynamicCode = __import__(code_path.rsplit('/',1)[1].split('.')[0])
    else:
        LSProdynamicCode = __import__(code_path.rsplit('\\',1)[1].split('.')[0])
    #import LSProdynamicCode
    ret_val=LSProdynamicCode.GetLSProData(page_data,Cookie_Jar,m)
    try:
        return str(ret_val)
    except: return ret_val


def getGoogleRecaptchaResponse(captchakey, cj,type=1): #1 for get, 2 for post, 3 for rawpost
#    #headers=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')]
#    html_text=getUrl(url,noredir=True, cookieJar=cj,headers=headers)
 #   print 'html_text',html_text
    recapChallenge=""
    solution=""
#    cap_reg="recap.*?\?k=(.*?)\""    
#    match =re.findall(cap_reg, html_text)
    
        
#    print 'match',match
    captcha=False
    captcha_reload_response_chall=None
    solution=None
    if len(captchakey)>0: #new shiny captcha!
        captcha_url=captchakey
        if not captcha_url.startswith('http'):
            captcha_url='http://www.google.com/recaptcha/api/challenge?k='+captcha_url+'&ajax=1'
#        print 'captcha_url',captcha_url
        captcha=True

        cap_chall_reg='challenge.*?\'(.*?)\''
        cap_image_reg='\'(.*?)\''
        captcha_script=getUrl(captcha_url,cookieJar=cj)
        recapChallenge=re.findall(cap_chall_reg, captcha_script)[0]
        captcha_reload='http://www.google.com/recaptcha/api/reload?c=';
        captcha_k=captcha_url.split('k=')[1]
        captcha_reload+=recapChallenge+'&k='+captcha_k+'&reason=i&type=image&lang=en'
        captcha_reload_js=getUrl(captcha_reload,cookieJar=cj)
        captcha_reload_response_chall=re.findall(cap_image_reg, captcha_reload_js)[0]
        captcha_image_url='http://www.google.com/recaptcha/api/image?c='+captcha_reload_response_chall
        if not captcha_image_url.startswith("http"):
            captcha_image_url='http://www.google.com/recaptcha/api/'+captcha_image_url
        import random
        n=random.randrange(100,1000,5)
        local_captcha = os.path.join(profile,str(n) +"captcha.img" )
        localFile = open(local_captcha, "wb")
        localFile.write(getUrl(captcha_image_url,cookieJar=cj))
        localFile.close()
        solver = InputWindow(captcha=local_captcha)
        solution = solver.get()
        os.remove(local_captcha)

    if captcha_reload_response_chall:
        if type==1:
            return 'recaptcha_challenge_field='+urllib.quote_plus(captcha_reload_response_chall)+'&recaptcha_response_field='+urllib.quote_plus(solution)
        elif type==2:
            return 'recaptcha_challenge_field:'+captcha_reload_response_chall+',recaptcha_response_field:'+solution
        else:
            return 'recaptcha_challenge_field='+urllib.quote_plus(captcha_reload_response_chall)+'&recaptcha_response_field='+urllib.quote_plus(solution)
    else:
        return ''
        

def getUrl(url, cookieJar=None,post=None, timeout=20, headers=None, noredir=False):


    cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)

    if noredir:
        opener = urllib2.build_opener(NoRedirection,cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
    else:
        opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
    #opener = urllib2.install_opener(opener)
    req = urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36')
    if headers:
        for h,hv in headers:
            req.add_header(h,hv)

    response = opener.open(req,post,timeout=timeout)
    link=response.read()
    response.close()
    return link;

def get_decode(str,reg=None):
    if reg:
        str=re.findall(reg, str)[0]
    s1 = urllib.unquote(str[0: len(str)-1]);
    t = '';
    for i in range( len(s1)):
        t += chr(ord(s1[i]) - s1[len(s1)-1]);
    t=urllib.unquote(t)
#    print t
    return t

def javascriptUnEscape(str):
    js=re.findall('unescape\(\'(.*?)\'',str)
#    print 'js',js
    if (not js==None) and len(js)>0:
        for j in js:
            #print urllib.unquote(j)
            str=str.replace(j ,urllib.unquote(j))
    return str

iid=0
def askCaptcha(m,html_page, cookieJar):
    global iid
    iid+=1
    expre= m['expres']
    page_url = m['page']
    captcha_regex=re.compile('\$LiveStreamCaptcha\[([^\]]*)\]').findall(expre)[0]

    captcha_url=re.compile(captcha_regex).findall(html_page)[0]
#    print expre,captcha_regex,captcha_url
    if not captcha_url.startswith("http"):
        page_='http://'+"".join(page_url.split('/')[2:3])
        if captcha_url.startswith("/"):
            captcha_url=page_+captcha_url
        else:
            captcha_url=page_+'/'+captcha_url

    local_captcha = os.path.join(profile, str(iid)+"captcha.jpg" )
    localFile = open(local_captcha, "wb")
#    print ' c capurl',captcha_url
    req = urllib2.Request(captcha_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
    if 'referer' in m:
        req.add_header('Referer', m['referer'])
    if 'agent' in m:
        req.add_header('User-agent', m['agent'])
    if 'setcookie' in m:
#        print 'adding cookie',m['setcookie']
        req.add_header('Cookie', m['setcookie'])

    #cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
    #opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
    #opener = urllib2.install_opener(opener)
    urllib2.urlopen(req)
    response = urllib2.urlopen(req)

    localFile.write(response.read())
    response.close()
    localFile.close()
    solver = InputWindow(captcha=local_captcha)
    solution = solver.get()
    return solution

def askCaptchaNew(imageregex,html_page,cookieJar,m):
    global iid
    iid+=1


    if not imageregex=='':
        if html_page.startswith("http"):
            page_=getUrl(html_page,cookieJar=cookieJar)
        else:
            page_=html_page
        captcha_url=re.compile(imageregex).findall(html_page)[0]
    else:
        captcha_url=html_page
        if 'oneplay.tv/embed' in html_page:
            import oneplay
            page_=getUrl(html_page,cookieJar=cookieJar)
            captcha_url=oneplay.getCaptchaUrl(page_)

    local_captcha = os.path.join(profile, str(iid)+"captcha.jpg" )
    localFile = open(local_captcha, "wb")
#    print ' c capurl',captcha_url
    req = urllib2.Request(captcha_url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
    if 'referer' in m:
        req.add_header('Referer', m['referer'])
    if 'agent' in m:
        req.add_header('User-agent', m['agent'])
    if 'accept' in m:
        req.add_header('Accept', m['accept'])
    if 'setcookie' in m:
#        print 'adding cookie',m['setcookie']
        req.add_header('Cookie', m['setcookie'])

    #cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
    #opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
    #opener = urllib2.install_opener(opener)
    #urllib2.urlopen(req)
    response = urllib2.urlopen(req)

    localFile.write(response.read())
    response.close()
    localFile.close()
    solver = InputWindow(captcha=local_captcha)
    solution = solver.get()
    return solution

#########################################################
# Function  : GUIEditExportName                         #
#########################################################
# Parameter :                                           #
#                                                       #
# name        sugested name for export                  #
#                                                       # 
# Returns   :                                           #
#                                                       #
# name        name of export excluding any extension    #
#                                                       #
#########################################################
def TakeInput(name, headname):


    kb = xbmc.Keyboard('default', 'heading', True)
    kb.setDefault(name)
    kb.setHeading(headname)
    kb.setHiddenInput(False)
    return kb.getText()

   
#########################################################

class InputWindow(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        self.cptloc = kwargs.get('captcha')
        self.img = xbmcgui.ControlImage(335,30,624,60,self.cptloc)
        self.addControl(self.img)
        self.kbd = xbmc.Keyboard()

    def get(self):
        self.show()
        time.sleep(2)
        self.kbd.doModal()
        if (self.kbd.isConfirmed()):
            text = self.kbd.getText()
            self.close()
            return text
        self.close()
        return False

def getEpocTime():
    import time
    return str(int(time.time()*1000))

def getEpocTime2():
    import time
    return str(int(time.time()))

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


def getFavorites():
        items = json.loads(open(favorites).read())
        total = len(items)
        for i in items:
            name = i[0]
            url = i[1]
            itemart['thumb']  = i[2]
            try:
                itemart['fanart']  = i[3]
                if i[3] == None:
                    raise
            except:
                if addon.getSetting('use_thumb') == "true":
                    itemart['fanart'] = iconimage
                else:
                    itemart['fanart'] = fanart
            try: item_info["playlist"] = i[5]
            except: item_info["playlist"] = None
            try: regexs = i[6]
            except: regexs = None

            if i[4] == 0:
                addLink(url,name,itemart,item_info,regexs,total)
            else:
                addDir(name,url,i[4],itemart,item_info)


def addFavorite(name,url,iconimage,fanart,mode,playlist=None,regexs=None):
        favList = []
        try:
            # seems that after
            name = name.encode('utf-8', 'ignore')
        except:
            pass
        if os.path.exists(favorites)==False:
            addon_log('Making Favorites File')
            favList.append((name,url,iconimage,fanart,mode,playlist,regexs))
            a = open(favorites, "w")
            a.write(json.dumps(favList))
            a.close()
        else:
            addon_log('Appending Favorites')
            a = open(favorites).read()
            data = json.loads(a)
            data.append((name,url,iconimage,fanart,mode))
            b = open(favorites, "w")
            b.write(json.dumps(data))
            b.close()


def rmFavorite(name):
        data = json.loads(open(favorites).read())
        for index in range(len(data)):
            if data[index][0]==name:
                del data[index]
                b = open(favorites, "w")
                b.write(json.dumps(data))
                b.close()
                break
        xbmc.executebuiltin("XBMC.Container.Refresh")
@LS_CACHE_ytdl_domain
def YTDL_domain_check(hostname):
    try:
        YTdl = True
        from YDStreamExtractor import getVideoInfo # import this first. it will add profile youtube-dl to sys 
        import youtube_dl
        from youtube_dl import extractor as _EX
        extractors= _EX.list_extractors('18') # cache that
        names=list(set([extractor.IE_NAME.lower() \
                        for extractor in extractors if not extractor.IE_NAME == 'generic']))
        if not any(((name in hostname) or (hostname in name)) for name in names):
            xbmc.log("This hostname nof found in Youtube-dl module: %s" %hostname, xbmc.LOGNOTICE)
            raise        
        
    except Exception:
        YTdl = False
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Please [COLOR yellow]install Youtube-dl[/COLOR] module ,5000,"")")
    return YTdl
@LS_CACHE_urlsolver    
def urlsolver(url):
    import urlresolver
    host = urlresolver.HostedMediaFile(url)
    stream_url = None
    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create("Trying","Using Urlresolver")
    hostname = urlparse.urlparse(url).hostname.lower()
    if host:
        try:
            stream_url = host.resolve()
            if not (stream_url and isinstance(stream_url, basestring)):
                raise
            #if stream_url and isinstance(stream_url, basestring):
            return stream_url
                #xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Urlresolver donot support this domain. - ,5000)")
                #raise Exception()
            #elif stream_url and isinstance(stream_url,list):
            #    for k in stream_url:
            #        quality = addon.getSetting('quality')
            #        if k['quality'] == 'HD'  :
            #            return k['url']
            #        elif k['quality'] == 'SD' :
            #            return k['url']
            #        elif k['quality'] == '1080p' and addon.getSetting('1080pquality') == 'true' :
            #            return k['url']
        except Exception:
            pass

 
    
    if not stream_url and YTDL_domain_check(hostname):
        pDialog.update(50,'[COLOR yellow]{0}[/COLOR]\nTrying Next:\n{1}{2}'.format('Urlresolver Failed','YoutubeDL Module...',hostname))
        from YDStreamExtractor import getVideoInfo
        info=getVideoInfo(url)
        if info:
            for s in info.streams():
                    #try:
                        stream_url = s['xbmc_url'].encode('utf-8','ignore')
                        itemart['thumb'] = s.get('thumbnail')
                        itemart['info'] = s['ytdl_format'].get('description').encode('utf-8','ignore')
                        addon_log("[STREAMURL FOUND FROM YTDL-%s]: %s" %('YOUTUBEDL', str(stream_url)))
                        if '.f4m' in stream_url:
                            if re.search('''foodnetwork''',stream_url):
                                stream_url=stream_url.replace('|User-Agent','&hdcore=2.11.3&g=OCVKSKWGMWCF|User-Agent')
                            stream_url= 'plugin://plugin.video.f4mTester/?url=' + urllib.quote_plus(stream_url)
                        elif re.search('''watch\?v=''',stream_url) :
                            uid = re.compile(utubeid,re.DOTALL).findall(stream_url)[0]
                            stream_url= 'plugin://plugin.video.youtube/play/?video_id=' + uid
                        elif stream_url:
                            stream_url= stream_url
        #else:                #return stream_url
        #    return
    if stream_url:
        pDialog.close()
        return stream_url
    pDialog.update(65,'[COLOR yellow]{0}[/COLOR]\nTrying Next:\n{1}'.format('Youtube-dl Failed','Chirppa Livestreamer Module...'))                
    final_url = GetLivestreamerLink(url)
    if not final_url:
        pDialog.close()
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro, [COLOR yellow]Couldnot resolve this url:[/COLOR] ,5000,"")")
        return
    pDialog.close()
    return final_url

def tryplay(url,listitem,pdialogue=None):    
    if url.lower().startswith('plugin') and 'youtube' not in  url.lower():
        addon_log("[addon.live.streamspro_tryplay.RunPlugin-%s]: " %( url),xbmc.LOGNOTICE)
        xbmc.executebuiltin('XBMC.RunPlugin('+url+')') 
        for i in range(8):
            xbmc.sleep(500) ##sleep for 10 seconds, half each time
            try:
                #print 'condi'
                if xbmc.getCondVisibility("Player.HasMedia") and xbmc.Player().isPlaying():
                    return True
            except: pass
        print 'returning now'
        return False
    import  CustomPlayer,time

    player = CustomPlayer.MyXBMCPlayer()
    player.pdialogue=pdialogue
    start = time.time() 
    #xbmc.Player().play( liveLink,listitem)
    print 'going to play'
    import time
    beforestart=time.time()
    player.play( url, listitem)
    xbmc.sleep(1000)
    
    try:
        while player.is_active:
            xbmc.sleep(400)
           
            if player.urlplayed:
                print 'yes played'
                return True
            if time.time()-beforestart>4: return False
            #xbmc.sleep(1000)
    except: pass
    print 'not played',url
    return False
def play_playlist(name, mu_playlist,queueVideo=None,itemart={},item_info={}):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        #print 'mu_playlist',mu_playlist
        if '$$LSPlayOnlyOne$$' in mu_playlist[0]:
            mu_playlist[0]=mu_playlist[0].replace('$$LSPlayOnlyOne$$','')
            import urlparse
            names = []
            iloop=0
            progress = xbmcgui.DialogProgress()
            progress.create('Progress', 'Trying Multiple Links')
            for i in mu_playlist:
                

                if '$$lsname=' in i:
                    d_name=i.split('$$lsname=')[1].split('&regexs')[0]
                    names.append(d_name)                                       
                    mu_playlist[iloop]=i.split('$$lsname=')[0]+('&regexs'+i.split('&regexs')[1] if '&regexs' in i else '')                    
                else:
                    d_name=urlparse.urlparse(i).netloc
                    if d_name == '':
                        names.append(name)
                    else:
                        names.append(d_name)
                index=iloop
                iloop+=1
                
                playname=names[index]
                if progress.iscanceled(): return 
                progress.update( iloop/len(mu_playlist)*100,"", "Link#%d"%(iloop),playname  )
                print 'auto playnamexx',playname
                if "&mode=19" in mu_playlist[index]:
                        #playsetresolved (urlsolver(mu_playlist[index].replace('&mode=19','')),name,iconimage,True)
                    liz = xbmcgui.ListItem(playname, iconImage=iconimage, thumbnailImage=iconimage)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    urltoplay=urlsolver(mu_playlist[index].replace('&mode=19','').replace(';',''))
                    liz.setPath(urltoplay)
                    #xbmc.Player().play(urltoplay,liz)
                    played=tryplay(urltoplay,liz)
                elif "$doregex" in mu_playlist[index] :
#                    print mu_playlist[index]
                    sepate = mu_playlist[index].split('&regexs=')
#                    print sepate
                    url,setresolved = getRegexParsed(sepate[1], sepate[0])
                    url2 = url.replace(';','')
                    liz = xbmcgui.ListItem(playname, iconImage=iconimage, thumbnailImage=iconimage)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    liz.setPath(url2)
                    #xbmc.Player().play(url2,liz)
                    played=tryplay(url2,liz)

                else:
                    url = mu_playlist[index]
                    url=url.split('&regexs=')[0]
                    liz = xbmcgui.ListItem(playname, iconImage=iconimage, thumbnailImage=iconimage)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    liz.setPath(url)
                    #xbmc.Player().play(url,liz)
                    played=tryplay(url,liz)
                    print 'played',played
                print 'played',played
                if played: return
            return     
        if addon.getSetting('ask_playlist_items') == 'true' and not queueVideo :

            names = []
            iloop=0
            for i in mu_playlist:
                if '$$lsname=' in i:
                    d_name=i.split('$$lsname=')[1].split('&regexs')[0]
                    names.append(d_name)                                       
                    mu_playlist[iloop]=i.split('$$lsname=')[0]+('&regexs'+i.split('&regexs')[1] if '&regexs' in i else '')                    
                else:
                    d_name=urlparse.urlparse(i).netloc
                    if d_name == '':
                        names.append(name)
                    else:
                        names.append(d_name)
                    
                iloop+=1
            dialog = xbmcgui.Dialog()
            index = dialog.select('Choose a video source', names)
            if index >= 0:
                playname=names[index]
                print 'playnamexx',playname
                if "&mode=19" in mu_playlist[index]:
                        #playsetresolved (urlsolver(mu_playlist[index].replace('&mode=19','')),name,iconimage,True)
                    liz = xbmcgui.ListItem(playname)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    urltoplay=urlsolver(mu_playlist[index].replace('&mode=19','').replace(';',''))
                    liz.setPath(urltoplay)
                    xbmc.Player().play(urltoplay,liz)
                elif "$doregex" in mu_playlist[index] :
#                    print mu_playlist[index]
                    sepate = mu_playlist[index].split('&regexs=')
#                    print sepate
                    url,setresolved = getRegexParsed(sepate[1], sepate[0])
                    url2 = url.replace(';','')
                    liz = xbmcgui.ListItem(playname)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    liz.setPath(url2)
                    xbmc.Player().play(url2,liz)

                else:
                    url = mu_playlist[index]
                    url=url.split('&regexs=')[0]
                    liz = xbmcgui.ListItem(playname)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    liz.setPath(url)
                    xbmc.Player().play(url,liz)
        elif not queueVideo:
            #playlist = xbmc.PlayList(1) # 1 means video
            playlist.clear()
            item = 0
            for i in mu_playlist:
                item += 1
                info = xbmcgui.ListItem('%s) %s' %(str(item),name))
                # Don't do this as regex parsed might take longer
                try:
                    if "$doregex" in i:
                        sepate = i.split('&regexs=')
#                        print sepate
                        url,setresolved = getRegexParsed(sepate[1], sepate[0])
                    elif "&mode=19" in i:
                        url = urlsolver(i.replace('&mode=19','').replace(';',''))                        
                    if url:
                        playlist.add(url, info)
                    else:
                        raise
                except Exception:
                    playlist.add(i, info)
                    pass #xbmc.Player().play(url)

            xbmc.executebuiltin('playlist.playoffset(video,0)')
        else:

                listitem = xbmcgui.ListItem(name)
                playlist.add(mu_playlist, listitem)


def download_file(name, url):
        if addon.getSetting('save_location') == "":
            xbmc.executebuiltin("XBMC.Notification('LiveStreamsPro','Choose a location to save files.',15000,"+icon+")")
            addon.openSettings()
        params = {'url': url, 'download_path': addon.getSetting('save_location')}
        downloader.download(name, params)
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno('LiveStreamsPro', 'Do you want to add this file as a source?')
        if ret:
            addSource(os.path.join(addon.getSetting('save_location'), name))

def _search(url,name):
   # print url,name
    pluginsearchurls = ['plugin://plugin.video.exodus/?action=tvSearch',\
             'plugin://plugin.video.exodus/?action=movieSearch',\
             'plugin://plugin.video.salts/?mode=search&amp;section=Movies',\
             'plugin://plugin.video.salts/?mode=search&amp;section=TV',\

             'plugin://plugin.video.youtube/kodion/search/list/',\
             'plugin://plugin.video.dailymotion_com/?mode=search&amp;url',\
             'plugin://plugin.video.vimeo/kodion/search/list/'\
             ]
    names = ['Exodus TV','Exodus Movie','Salt movie','salt TV',\
             'Youtube','DailyMotion','Vimeo']
    dialog = xbmcgui.Dialog()
    index = dialog.select('Choose a video source', names)

    if index >= 0:
        url = pluginsearchurls[index]
#        print 'url',url
        pluginquerybyJSON(url)

def addDir(name,url,mode,itemart,item_info,regexs=None,reg_url=None):
        fanart = itemart.get('fanart') or FANART

        #xbmc.log("PLAYHEADERS: "+str(PLAYHEADERS),xbmc.LOGNOTICE)
        if PLAYHEADERS and not "$$PLAYHEADERS="  in url:
        
            url = '{0}|{1}'.format(url,PLAYHEADERS)
            #xbmc.log("url with PLAYHEADERS: "+str(url),xbmc.LOGNOTICE)
        if regexs and len(regexs)>0:
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&regexs="+regexs
        else:
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        try:
        
            u += "&name="+urllib.quote_plus(name)
        except:
            pass
        try:
        
            u += "&fanart="+urllib.quote_plus(fanart)
        except:
            pass
   
        ok=True

        liz=xbmcgui.ListItem(name)
        item_info["Title"] = name
        iconimage = itemart.get('thumb')
        if not iconimage:
            itemart['thumb'] =iconimage = icon
        liz.setInfo(type="Video", infoLabels= item_info)
        liz.setArt(itemart)
        showcontext = item_info.get('showcontext',None)

        if showcontext:
            contextMenu = []
            parentalblock =addon.getSetting('parentalblocked')
            parentalblock= parentalblock=="true"
            parentalblockedpin =addon.getSetting('parentalblockedpin')
#            print 'parentalblockedpin',parentalblockedpin
            #Container.Update
            contextMenu.append(('Search this source for','Container.Update(%s?url=%s&mode=60&name=%s,return)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))            
            if len(parentalblockedpin)>0:
                if parentalblock:
                    contextMenu.append(('Disable Parental Block','XBMC.RunPlugin(%s?mode=55&name=%s)' %(sys.argv[0], urllib.quote_plus(name))))
                else:
                    contextMenu.append(('Enable Parental Block','XBMC.RunPlugin(%s?mode=56&name=%s)' %(sys.argv[0], urllib.quote_plus(name))))
                    
            if showcontext == 'source':
            
                if name in str(SOURCES):
                    contextMenu.append(('Remove from Sources','XBMC.RunPlugin(%s?mode=8&name=%s)' %(sys.argv[0], urllib.quote_plus(name))))
                    
                    
            elif showcontext == 'download':
                contextMenu.append(('Download','XBMC.RunPlugin(%s?url=%s&mode=9&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
            elif showcontext == 'fav':
                contextMenu.append(('Remove from LiveStreamsPro Favorites','XBMC.RunPlugin(%s?mode=6&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(name))))
            if showcontext == '!!update':
                fav_params2 = (
                    '%s?url=%s&mode=17&regexs=%s'
                    %(sys.argv[0], urllib.quote_plus(reg_url), regexs)
                    )
                contextMenu.append(('[COLOR yellow]!!update[/COLOR]','XBMC.RunPlugin(%s)' %fav_params2))
            if showcontext == 'YTsearch':
                    YT_search_name = re.sub(r"\[/?\w{4}.*?\]" ,r'',name.split('(')[0],re.I) #remove [/color]
                    
                    youtube_con = 'plugin://plugin.video.youtube/kodion/search/query/?q=' + urllib.quote_plus(YT_search_name +' album' )
                    addon_log("youtube kodion search %s" %youtube_con,xbmc.LOGNOTICE) 
                    contextMenu.append(('[COLOR white]Play from Youtube[/COLOR]', 'XBMC.RunPlugin(%s?url=%s&mode=1899&name=%s)'% (sys.argv[0], urllib.quote_plus(youtube_con), urllib.quote_plus(name))))            
            if not name in FAV:
                contextMenu.append(('Add to LiveStreamsPro Favorites','XBMC.RunPlugin(%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&fav_mode=%s)'
                         %(sys.argv[0], urllib.quote_plus(name), urllib.quote_plus(url), urllib.quote_plus(iconimage), urllib.quote_plus(fanart), mode)))
            liz.addContextMenuItems(contextMenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

        
def ytdl_download(url,title,media_type='video'):
    # play in xbmc while playing go back to contextMenu(c) to "!!Download!!"
    # Trial yasceen: seperate |User-Agent=
    import youtubedl
    if not url == '':
        if media_type== 'audio':
            youtubedl.single_YD(url,download=True,audio=True)
        else:
            youtubedl.single_YD(url,download=True)
    elif xbmc.Player().isPlaying() == True :
        import YDStreamExtractor
        if YDStreamExtractor.isDownloading() == True:

            YDStreamExtractor.manageDownloads()
        else:
            xbmc_url = xbmc.Player().getPlayingFile()

            xbmc_url = xbmc_url.split('|User-Agent=')[0]
            info = {'url':xbmc_url,'title':title,'media_type':media_type}
            youtubedl.single_YD('',download=True,dl_info=info)
    else:
        xbmc.executebuiltin("XBMC.Notification(DOWNLOAD,First Play [COLOR yellow]WHILE playing download[/COLOR] ,10000)")

## Lunatixz PseudoTV feature
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

def pluginquerybyJSON(queryurl,give_me_result=None,addtoplaylist=False):
    #xbmc.log("playlist: %s" %url)
    if 'audio' in queryurl:
        json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params": {"directory":"%s","media":"video", "properties": ["title", "album", "artist", "duration","thumbnail", "year"]}, "id": 1}') %queryurl
    else:
        json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","media":"video","properties":[ "plot","playcount","director", "genre","votes","duration","trailer","premiered","thumbnail","title","year","dateadded","fanart","rating","season","episode","studio","mpaa"]},"id":1}') %queryurl
    json_folder_detail = json.loads(sendJSON(json_query))
    #print json_folder_detail
    if give_me_result:
        return json_folder_detail
    #xbmc.log("playlist: %s" %url)
    if json_folder_detail.has_key('error'):
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Plugin Json Request failed. - "+"this"+",4000,"+icon+")")
        return
    else:
        total=len(json_folder_detail['result']['files'])
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)  # 1 means video
        playlist.clear()
        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create("PlayList","Adding")     
        for index,i in enumerate(json_folder_detail['result']['files']) :
            meta ={}
            url = i['file']
            try:
                name = i['label'] # support non-english
            except:
                name = removeNonAscii(i['label'])
            itemart['thumb'] = removeNonAscii(i.get('thumbnail',icon))
            itemart['fanart'] = removeNonAscii(i.get('fanart',FANART))
            item_info = dict((k,v) for k, v in i.iteritems() if not v == '0' or not v == -1 or v == '')
            meta.pop("file", None)
            if i['filetype'] == 'file':
                if addtoplaylist:
                    liz = xbmcgui.ListItem(name)
                    liz.setInfo(type="Video", infoLabels=item_info)
                    liz.setArt(itemart)
                    
                    playlist.add(url, liz)

                    if index > 2 and not xbmc.getCondVisibility('Player.HasMedia'):
                        xbmc.Player().play(playlist)                    

                    continue
                else:
                    addLink(url,name,itemart,item_info,None,total)
                    #xbmc.executebuiltin("Container.SetViewMode(500)")
                    tvshow=i.get('type')
                    if  tvshow :
                        if  tvshow in ('tvshows','episodes') :
                            xbmcplugin.setContent(int(sys.argv[1]), tvshow)

            elif url.startswith("plugin://") :
                addDir(name,url,53,itemart,item_info)
            else:
                if not "plugin://" in url:
                    
                    mas = re.compile(r"[&|;]url=([^&\n\r]+)",re.IGNORECASE | re.DOTALL).findall(queryurl)
                    if mas:
                        url = queryurl.replace(mas[0],urllib.quote_plus(url))
                item_info["showcontext"] = 'source'
                addDir(name,url,53,itemart,item_info)
        pDialog.close()
        if not addtoplaylist:
            xbmcplugin.endOfDirectory(int(sys.argv[1]))                

def addLink(url,name,itemart={},item_info={},regexs=None,total=1,setCookie=""):
        #,type(name),type(itemart),type(item_info))))
        if not url:
            return
        contextMenu =[]
        parentalblock =addon.getSetting('parentalblocked')
        parentalblock= parentalblock=="true"
        parentalblockedpin =addon.getSetting('parentalblockedpin')
        if PLAYHEADERS and not '|' in url:
            url = '{0}|{1}'.format(url,PLAYHEADERS)
        if len(parentalblockedpin)>0:
            if parentalblock:
                contextMenu.append(('Disable Parental Block','XBMC.RunPlugin(%s?mode=55&name=%s)' %(sys.argv[0], urllib.quote_plus(name))))
            else:
                contextMenu.append(('Enable Parental Block','XBMC.RunPlugin(%s?mode=56&name=%s)' %(sys.argv[0], urllib.quote_plus(name))))
                    
        try:
            name = name.encode('utf-8')
        except: pass
        ok = True
        isFolder=False
        if regexs:
            mode = '17'
            if 'listrepeat' in regexs:
                isFolder=True
#                print 'setting as folder in link'
            contextMenu.append(('[COLOR white]!!Download Currently Playing!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=21&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
        elif  (any(x in url for x in resolve_url) and  url.startswith('http')) or url.endswith('&mode=19'):
            url=url.replace('&mode=19','')
            mode = '19'
            contextMenu.append(('[COLOR white]!!Download Currently Playing!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=21&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
        elif url.endswith('&mode=18'):
            url=url.replace('&mode=18','')
            mode = '18'
            contextMenu.append(('[COLOR white]!!Download!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=23&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
            if addon.getSetting('dlaudioonly') == 'true':
                contextMenu.append(('!!Download [COLOR seablue]Audio!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=24&name=%s)'
                                        %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
        elif url.startswith('magnet:?xt='):
            if '&' in url and not '&amp;' in url :
                url = url.replace('&','&amp;')
            url = 'plugin://plugin.video.pulsar/play?uri=' + url
            mode = '12'
        elif 'youtube' in url and 'watch?v=' in url:
            url = 'plugin://plugin.video.youtube/play/?video_id=' + re.compile('v(?:=|%3D)([0-9A-Za-z_-]{11})',re.I).findall(url)[0]
            mode = '12'            
        else:
            mode = '12'
            contextMenu.append(('[COLOR white]!!Download Currently Playing!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=21&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
        if 'plugin://plugin.video.youtube/play/?video_id=' in url:
              yt_audio_url = url.replace('plugin://plugin.video.youtube/play/?video_id=','https://www.youtube.com/watch?v=')
              contextMenu.append(('!!Download [COLOR blue]Audio!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=24&name=%s)'
                                      %(sys.argv[0], urllib.quote_plus(yt_audio_url), urllib.quote_plus(name))))
        u=sys.argv[0]+"?"
        play_list = False
        playlist = item_info.get('playlist',None)
        if playlist:
            if addon.getSetting('add_playlist') == "false" and '$$LSPlayOnlyOne$$' not in playlist[0] :
                u += "url="+urllib.quote_plus(url)+"&mode="+mode
            else:
                u += "mode=13&name=%s&playlist=%s" %(urllib.quote_plus(name), urllib.quote_plus(str(playlist).replace(',','||')))
                name = name + '[COLOR magenta] (' + str(len(playlist)) + ' items )[/COLOR]'
                play_list = True
        else:
            u += "url="+urllib.quote_plus(url)+"&mode="+mode
        if regexs:
            u += "&regexs="+regexs
        if not setCookie == '':
            u += "&setCookie="+urllib.quote_plus(setCookie)
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
        if (not play_list) and not any(x in url for x in g_ignoreSetResolved) and not '$PLAYERPROXY$=' in url:#  (not url.startswith('plugin://plugin.video.f4mTester')):
            if regexs:
                #print urllib.unquote_plus(regexs)
                if '$pyFunction:playmedia(' not in urllib.unquote_plus(regexs) and 'notplayable' not in urllib.unquote_plus(regexs) and 'listrepeat' not in  urllib.unquote_plus(regexs) :
                    #print 'setting isplayable',url, urllib.unquote_plus(regexs),url
                    liz.setProperty('IsPlayable', 'true')
            else:
                liz.setProperty('IsPlayable', 'true')
        else:
            addon_log( 'NOT setting isplayable'+url)
        showcontext = item_info.get('showcontext',None)
        fanart = itemart.get('fanart')  or FANART          
        if showcontext:
            #contextMenu = []
            if disableepg == 'false' and item_info.get('tvgurl') and not item_info.get('tvgurl') == '0':
                u += "&tvgurl=%s&epgfile=%s&offset=%s" %(item_info.get('tvgurl','0'),
                                              item_info.get('epgfile','0')
                                              ,item_info.get('offset','0'))
                contextMenu.append(
                    ('What\'s on Today','Container.Update(%s?mode=26&url=%s&name=%s,return)'
                     %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name.split('::')[0])))
                     )                
                
                
            if showcontext == 'fav':
                contextMenu.append(
                    ('Remove from LiveStreamsPro Favorites','XBMC.RunPlugin(%s?mode=6&name=%s)'
                     %(sys.argv[0], urllib.quote_plus(name)))
                     )
            elif not name in FAV:
                try:
                    fav_params = (
                        '%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&fav_mode=0'
                        %(sys.argv[0], urllib.quote_plus(name), urllib.quote_plus(url), urllib.quote_plus(iconimage), urllib.quote_plus(fanart))
                        )
                except:
                    fav_params = (
                        '%s?mode=5&name=%s&url=%s&iconimage=%s&fanart=%s&fav_mode=0'
                        %(sys.argv[0], urllib.quote_plus(name), urllib.quote_plus(url), urllib.quote_plus(iconimage.encode("utf-8")), urllib.quote_plus(fanart.encode("utf-8")))
                        )
                if playlist:
                    fav_params += 'playlist='+urllib.quote_plus(str(playlist).replace(',','||'))
                if regexs:
                    fav_params += "&regexs="+regexs
                contextMenu.append(('Add to LiveStreamsPro Favorites','XBMC.RunPlugin(%s)' %fav_params))
            if showcontext == 'YTsearch':  # Did not work
                    YT_search_name = re.sub(r"\[/?\w{4}.*?\]" ,r'',name.split('(')[0],re.I) #remove [/color]
                    
                    youtube_con = 'plugin://plugin.video.youtube/kodion/search/query/?q=' + urllib.quote_plus(YT_search_name +' album' )
                    addon_log("youtube kodion search %s" %youtube_con,xbmc.LOGNOTICE) 
                    contextMenu.append(('[COLOR white]Play from Youtube[/COLOR]', 'XBMC.RunPlugin(%s?url=%s&mode=1899&name=%s)'% (sys.argv[0], urllib.quote_plus(youtube_con), urllib.quote_plus(name))))            

            liz.addContextMenuItems(contextMenu)
        try:
            if not playlist is None:
                if addon.getSetting('add_playlist') == "false":
                    playlist_name = name.split(') ')[1]
                    contextMenu_ = [
                        ('Play '+playlist_name+' PlayList','XBMC.RunPlugin(%s?mode=13&name=%s&playlist=%s)'
                         %(sys.argv[0], urllib.quote_plus(playlist_name), urllib.quote_plus(str(playlist).replace(',','||'))))
                         ]
                    liz.addContextMenuItems(contextMenu_)
        except: pass
        #print 'adding',name
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total,isFolder=isFolder)

        #print 'added',name
        return ok

def getnaviplx(url,data=None):
    if data is None :
        data = makeRequest(url)
    data = re.split(r"^\s+(?!\n)", data, 0, re.IGNORECASE | re.MULTILINE)
    data = [i.split("\n") for i in data ]
    for index,i in enumerate(data):
        d=dict((j.split("=",1)[0],j.split("=",1)[1]) for j in i if "=" in j)
        URL = d.get("URL")
        if not d or not URL:
            continue
        
        itemart["thumb"] = d.get("thumb") or d.get("icon") 
        if index==0:
            itemart["fanart"] = d.get("background")
        
        if d.get("type") == "playlist" or URL.endswith((".xml",".XML",".plx")):
            addDir(d.get('name'), URL, 1,itemart,item_info)
        else:
            addLink(URL, d.get('name'),itemart,item_info,regexs=None,total=1)
 
      
def playsetresolved(url,name,setresolved=True,reg=None):
    print url
    if setresolved:
        setres=True
        if '$$LSDirect$$' in url:
            url=url.replace('$$LSDirect$$','')
            setres=False
        if reg and 'notplayable' in reg:
            setres=False
        try:
            path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
            path = dict(urlparse.parse_qsl(path.split('?',1)[1]))
            item_info["plot"] = path.get("plot")
            itemart["thumb"] = path.get("thumb")
        except:
            pass
        
        liz = xbmcgui.ListItem(name)
        item_info['Title'] = name

        liz.setInfo(type='Video', infoLabels=item_info)
        liz.setArt(itemart)
        liz.setProperty("IsPlayable","true")
        liz.setPath(url)
        if not setres:
            xbmc.Player().play(url)
        else:
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
           
    else:
        xbmc.executebuiltin('XBMC.RunPlugin('+url+')')


## Thanks to daschacka, an epg scraper for http://i.teleboy.ch/programm/station_select.php
##  http://forum.xbmc.org/post.php?p=936228&postcount=1076

    
##not a generic implemenation as it needs to convert            
def d2x(d, root="root",nested=0):

    op = lambda tag: '<' + tag + '>'
    cl = lambda tag: '</' + tag + '>\n'

    ml = lambda v,xml: xml + op(key) + str(v) + cl(key)
    xml = op(root) + '\n' if root else ""

    for key,vl in d.iteritems():
        vtype = type(vl)
        if nested==0: key='regex' #enforcing all top level tags to be named as regex
        if vtype is list: 
            for v in vl:
                v=escape(v)
                xml = ml(v,xml)         
        
        if vtype is dict: 
            xml = ml('\n' + d2x(vl,None,nested+1),xml)         
        if vtype is not list and vtype is not dict: 
            if not vl is None: vl=escape(vl)
            #print repr(vl)
            if vl is None:
                xml = ml(vl,xml)
            else:
                #xml = ml(escape(vl.encode("utf-8")),xml)
                xml = ml(vl.encode("utf-8"),xml)

    xml += cl(root) if root else ""

    return xml
xbmcplugin.setContent(int(sys.argv[1]), 'movies')

try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
except:
    pass
try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_GENRE)
except:
    pass

def search_lspro_source(source=None,searchterm="") :
    if searchterm == "" :
        keyboard = xbmc.Keyboard('','Search[Use one syllable only;no space]')
        keyboard.doModal()
        if not (keyboard.isConfirmed() == False):
                newStr = keyboard.getText()
                if len(newStr) == 0 :
                    return 
        else:
            xbmc.log("No Search term found",xbmc.LOGNOTICE)
            return
        searchterm = newStr.lower().replace(' ', '')
        changesetting = False
        if groupm3ulinks == 'true':
            addon.setSetting('groupm3ulinks', 'false')
            changesetting = True
        if addon.getSetting('donotshowbychannels') == 'false':
            addon.setSetting('donotshowbychannels', 'true')
            changesetting = True
    import workers
    progress = xbmcgui.DialogProgress()
    progress.create('Progress', 'Creating Search')
        
    m3upat = re.compile(r"\s?#EXTINF:.+?,.*?%s.*?[\n\r]+[^\r\n]+" %searchterm,  re.IGNORECASE )
        
    link = ''
    ALLexlink =allitems= []
    threads = []
    if not source:
        s_f = os.path.join(profile,'source_file')
        sources = json.loads(open(s_f,"r").read())
    else:
        sources = [source]
    def processthreads(threads):
        [i.start() for i in threads]
        timeout =10
        for i in range(0, timeout * 2):
            progress.update(30+i,"Please Wait %s Seconds" %str(i))
            is_alive = [x.is_alive() for x in threads]
            if all(x == False for x in is_alive): break
            time.sleep(0.5)
            #[i.join() for i in threads]
        try: progress.close()
        except: pass        
    def getSearchData(url):
            print url
            k=None
            soup = getSoup(url)
            #progress.update(40, "Searching URL")
            allitem = soup("item")
            [getItems(allitem[index], FANART) for index,i in enumerate(allitem) if i.get('title') and searchterm in i.get('title').lower().strip()]
            exlink = soup("externallink")
            if len(exlink) > 0:
                allexlinks= [i.string for index,i in  enumerate(exlink) if not i.string is None and i.string.startswith('http')  ]
                k=find_ex_links(allexlinks)
            if k:
                k=find_ex_links(allexlinks)
            if k:
                k=find_ex_links(allexlinks)
            if k:
                k=find_ex_links(allexlinks)          
    def find_ex_links(links): 
        for link in links:
            progress.update(20, "Finding External Links")
            soup = getSoup(link)
            if not isinstance(soup,BeautifulSOAP):
            
                    matchs = m3upat.findall(soup)
                    for match in matchs : threads.append(workers.Thread(parse_m3u, match))
                    continue
            allitem = soup("item")
            progress.update(25,"Items found %s" %len(allitem))
            [getItems(allitem[index], FANART) for index,i in enumerate(allitem) if i.get('title') and searchterm in i.get('title').lower().strip()]
            exlink =soup('externallink')
            progress.update(25,"processing externallink : %s" %len(exlink))
            if len(exlink)>0:
                return [i.string for index,i in  enumerate(exlink) if not i.string is None and i.string.startswith('http')  ]

    getexitems = find_ex_links(sources)
    if getexitems:
    
            ll= [i.string for index,i in  enumerate(getexitems) if not i.string is None and i.string.startswith('http')  ]
    
            for link in ll :threads.append(workers.Thread(getSearchData, link)) 
            progress.update(30,"processing Threads : %s" %len(threads))
    try: progress.close()
    except: pass
    #Not sure why these change dont take place
    if changesetting:
        addon.setSetting('groupm3ulinks', 'true')
        addon.setSetting('donotshowbychannels', 'false')    
    processthreads(threads)

    #xbmc.log("[addon.live.streamsproSearchURL-%s]:Items found %s" %(str(url), str(len(allitems))),xbmc.LOGNOTICE)         
    #items = [getItems(allitem[index], fanart) for index,i in enumerate(allitems[0])]
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def starttimeofchannel(n):
    if  (startorstoptodatetime(sorted(GUIDE[n].keys(),reverse=True)[0])- datetime.timedelta(seconds=60*30))< now :
        return "1"
    return "0"

def checkfile(epgfilewithreg,timeforfileinsec):
        _time_limit = time.time() - int(timeforfileinsec)
        if os.path.isfile(epgfilewithreg):
            #xbmcvfs.Stat(filename).st_mtime()
            #xbmcvfs.File(filename).size()

            if os.stat(epgfilewithreg).st_mtime < _time_limit:
                xbmcvfs.delete(epgfilewithreg)        
        if os.path.isfile(epgfilewithreg):
            
            return True
        else:
            return False
#@LS_CACHE_getepgcontent
def getepgcontent(epg,getnew=False):
    if epg and isinstance(epg, basestring):
        url=epglink=epg
        epgfile = "0"
    else:
        epglink= epg.get('tvgurl')
        
        url=epglink
        if epglink:
            epgfile = epg.get('epgfile','0')
            houroffset = epg.get('tvgshift') or 0
            updateafterhour = epg.get('updateafterhour','24')
    if not xbmcvfs.exists(LivewebTVepg):
        xbmcvfs.mkdir(LivewebTVepg)
    if not epgfile == "0":
        filename = os.path.join(LivewebTVepg,cacheKey(url))
        extracted_dir = os.path.join(LivewebTVepg,cacheKey(url)+'_extracted')#dir
          
        epgxml = os.path.join(extracted_dir,epgfile)
        epgfilewithreg = os.path.join(extracted_dir,cacheKey(epgxml)+'.json')
    
                    
    else:
        epgfilewithreg = os.path.join(LivewebTVepg,cacheKey(url)+'.json')
        if "\\" in url:
            epgxml = url
        else:
            epgxml = os.path.join(LivewebTVepg,cacheKey(url))
        
    if getnew:
        os.remove(epgfilewithreg)
    if os.path.isfile(epgfilewithreg):
        return epgfilewithreg
    elif not "\\" in url:
        if not epgfile == "0":
            
            down_url(url,filename,_out=extracted_dir)
        else:
            down_url(url,epgxml)        
    # file is ready check cache 
    return epg_source_toregfile(epgxml,epgtimeformat,epgfilewithreg)

#@LS_CACHE_EPGcontent
'''  <programme start="20170111010000 -0500" stop="20170111020000 -0500" channel="GLOBAL VANCOUVER">
    <title lang="en">Chicago Fire</title>
    <useless-title lang="en">The People We Meet</useless-title>
    <desc lang="en">The People We Meet    Episode: S05E10  2017 TV-14  
Drama | Action.
Severide agrees to a bone marrow donation; Casey and Dawson attempt to find harmony at home; Otis and Mouch plan to create a PSA to encourage people to join the Chicago Fire Department. Severide agrees to a bone marrow donation; Casey and Dawson attempt to find harmony at home; Otis and Mouch plan to create a PSA to encourage people to join the Chicago Fire Department.
</desc>
    <category lang="en">Drama</category>
    <category lang="en">Action</category>
    <episode-num system="common">S05E10</episode-num>
  </programme>'''
def epg_source_toregfile(epgxml,epgtimeformat,epgfilewithreg):
    epgfile = open(epgxml,"rb").read()
    if epgfile != None:
        try:
            root = xml.etree.ElementTree.fromstring(epgfile)
        except:
            root = None
        
        if root is not None:
            pDialog= xbmcgui.DialogProgressBG()
            pDialog.create("Preparing XMLTV File ","Finding programs and writing as dictionary")
            
            ALLROOTS = root.findall("./programme")
            total = len(ALLROOTS)
            for index,programme in  enumerate(ALLROOTS):
                subtitle=desc=""
                channel = cleanname(programme.get('channel')) #clenname in here.(nospace,lower)
                start = programme.get('start')[:14]
                stop = programme.get('stop')[:14]
                title = programme.find('title').text
                if not programme.find('sub-title') is None:
                    subtitle = programme.find('sub-title').text
                if not programme.find('desc') is None:
                    desc = programme.find('desc').text
                try:
                    category = " ".join([i.text for i in epgsoup('category')])
                    #programme.find('category').text
                except:
                    category = "Lspro"
                    pass
                try:
                    episodenum = programme.find('episode-num').text
                except:
                    episodenum = '0'
                    pass
                pDialog.update(int(index*100./total), channel, "Writing %s" %channel)

                item = {"episodenum": episodenum,"genre":category,'start': start, 'stop': stop, 'title': title,"subtitle":subtitle,"plot":desc}
                GUIDE.setdefault(channel, {})[start] = item
            GUIDE["FileKEY"] = epgfilewithreg
            with open(epgfilewithreg,"w") as f:
                f.write(json.dumps(GUIDE))
            try:
                pDialog.close()
                os.remove(epgxml)
                
            except Exception:
                pass
            
            return epgfilewithreg

        else:
            xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,!!Warning Bad Regex::No Epg found!! ,3000,"+icon+")")
    
    return None

           
def startorstoptodatetime(input):
    return datetime.datetime(*(time.strptime(input, epgtimeformat)[0:6]))           

    
                
@LS_CACHE_epginfo                
def epginfo(channel,onedayEPG=False):                            
    summary = ''
    itemart={}
    item_info ={}
    
    hh= [i for i in GUIDE[channel].values() if  startorstoptodatetime(i['start']) <= now + datetime.timedelta(hours = 4) and startorstoptodatetime(i['stop']) > now ]
    #
    items_list = sorted(hh, key= lambda d: int(d["start"]))
    for index,item in enumerate(items_list):
        start = startorstoptodatetime(item['start'])
      
        if index == 0:
            #try:
            #python 2.7 only
            item_info['duration'] = int((startorstoptodatetime(item['stop'])-start).total_seconds())
            summary ='NOW([COLOR yellow]' + start.strftime('%H:%M') + ' [/COLOR])[COLOR cyan][B]' + item['title']+ ":" +item['subtitle'] + '\n' + item['plot'] + "[/B][/COLOR]!!!\n"
            continue
        else:
            nowtonxstart = str((start-now)).split(":")
            if nowtonxstart[0]=='0':
                duration = "[COLOR hotpink][I](In:%sm)[/I][/COLOR]" %nowtonxstart[1]
            else:
                duration = "[COLOR hotpink][I](In:%sh%sm)[/I][/COLOR]" %(nowtonxstart[0],nowtonxstart[1])
                
        summary = summary + '[COLOR skyblue]' + start.strftime('%H:%M') + '%s ' %duration+ item['title']+ "[/COLOR]:" +item['subtitle'] + '\n' + item['plot'] +"!!!\n"
        item_info['genre']  = item.get('genre',"TV")
    item_info['plot'] = re.sub("\n+","\n",summary)
    
    return itemart,item_info
#E_con(soup or url and list of names) to get nameinepgfile(in epgfile) and names(not inclued in epgfile)
def CheckEPGtimeValidaty(E_con,itemsname):
        global GUIDE
        epgdictfile= getepgcontent(E_con)
        
        GUIDE = json.loads(open(epgdictfile).read())
        guidekeys = GUIDE.keys()

        #FF=[]
        nameinepgfile=[]
        #for name in sorted(itemsname,reverse=True):
        #    if  name[1] in guidekeys:
        #        nameinepgfile.append(name)
        #        itemsname.remove(name)
        #        FF.append(starttimeofchannel(name[1]))
                
        FF=[(starttimeofchannel(name[1]),nameinepgfile.append(name),itemsname.remove(name)) for name in sorted(itemsname,reverse=True)  if  name[1] in guidekeys]
        failcount= Counter(elem[0] for elem in FF).get("1") or 0
        if nameinepgfile and int(failcount*100/len(nameinepgfile)) > 45:
            getepgcontent(E_con,getnew=True)
        return itemsname,nameinepgfile
def lspro_Epg(soup):
   
    pDialog = xbmcgui.DialogProgress()
    pDialog.create("Getting EPG","Please Wait" )
    global GUIDE
    if isinstance(soup,basestring):
        #try:
            epgdictfile= getepgcontent(soup)
        #except:
            #epgdictfile=None
            GUIDE = json.loads(open(epgdictfile).read())
            return epgdictfile
    else:
        E=  list(set(soup("epg")+soup("itemepg")))
        F = soup("item") + soup("epgitem") # can be safely remove soup("epgitem") and soup("itemepg")

        total = len(F)    
        names = [(index,cleanname(i.title.text.decode('utf-8'))) for index,i in enumerate(F)]
    pDialog.update(5, "Total names found : %s" %str(len(names)),"Total Epgfiles found:%s" %len(E))
    percent = 95/len(E)
    for index,E_con in enumerate(E):
        names,epgnames=CheckEPGtimeValidaty(E_con,names)
        Ppercent= int(percent)*(index+1)
        pDialog.update(int(Ppercent), "Updateing EPG for %s channels" %len(epgnames) )
        itemsartinfo =  [(epgitemcount,epginfo(name)) for epgitemcount,name in epgnames]
        
        [getItems(F[epgitemcount],FANART,epgiteminfo[0],epgiteminfo[1],total=total) for epgitemcount,epgiteminfo in itemsartinfo]
    
        GUIDE={}
        
    pDialog.update(int(len(E)*100./len(E)), "Finished Listing one epg file" )    
    if len(names) > 0:
        [getItems(F[epgitemcount],FANART) for epgitemcount,i in names ]
    pDialog.close()
def addDirPlayable(name, url, mode,itemart,item_info,playslideshow=None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(
        name) 
    # print 'adddirplayable',u
    contextMenu = []
    ok = True
    showcontext = item_info.get('showcontext')
    liz = xbmcgui.ListItem(name)
    item_info["Title"] = name
#    if not itemart.get('thumb'):
#        itemart['thumb'] = icon
    if use_thumb and not itemart.get('fanart'):
        itemart['fanart']= itemart.get('thumb') or FANART
    if not itemart.get('thumb'):
        itemart['thumb'] = icon
    if playslideshow:
        liz.setInfo( type="image", infoLabels={"Title": name} )
        #xbmcplugin.setContent(int(sys.argv[1]), 'images')
        #liz.setInfo(type="pictures", infoLabels=item_info)
    else:
        liz.setInfo(type="Video", infoLabels=item_info)
        liz.setArt(itemart)    
    
  
    
    if showcontext and showcontext == 'YTsearch':  # Did not work
        youtube_con = 'plugin://plugin.video.youtube/kodion/search/query/?q=' + urllib.quote_plus(
            name.split('[')[0] + ' album')
        contextMenu.append(('[COLOR white]Play from Youtube[/COLOR]', 'XBMC.RunPlugin(%s?url=%s&mode=1899&name=%s)'
                            % (sys.argv[0], urllib.quote_plus(youtube_con), urllib.quote_plus(name))))
        liz.addContextMenuItems(contextMenu)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
    return ok
def addDirectoryItem( url, name, isFolder=False):

    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=xbmcgui.ListItem(name), isFolder=isFolder)
def notification(header="", message="", sleep=3000,icon=icon):
    """ Will display a notification dialog with the specified header and message,
    in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i,%s)" % ( header, message, sleep,icon ))
def ShowOSDnownext():
    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    xbmc.log(str(path),xbmc.LOGNOTICE)
    path = dict(urlparse.parse_qsl(path.split('?',1)[1]))
    plot = path.get('plot')
    progtimes = re.compile(r"\](\d{2}:\d{2})\[",re.DOTALL).findall(plot)
    if not progtimes:
        return
    icon = path.get("thumb","0")
    
    
    plots = plot.split("!!!\n")
    #deg(plots)
    plot = plots.pop(0)
    heading,mesg = plot.rsplit("\n",1)
    heading = (re.sub(r"\[/?[COLOR|B|I].*?\]","",heading).split("\n",1)[0]).replace("\n"," ")
    notification(heading, "Playing", sleep=10000,icon=icon)
    for i,plot in enumerate(plots):
        if plot:
            heading,mesg = plot.rsplit("\n",1)
            heading = (re.sub(r"\[/?[COLOR|B|I].*?\]","",heading).split(")",1)[1]).replace("\n"," ")
            progtime = progtimes[i]
            notimezone=datetime.datetime.strptime(now.strftime("%Y%m%d") + progtime.split(":")[0]+progtime.split(":")[1],"%Y%m%d%H%M")
            waitfornxnoti=int((notimezone-now).total_seconds())

            
            while 1:
                time.sleep(10)
                waitfornxnoti =  waitfornxnoti-10
                if xbmc.abortRequested == True or not xbmc.Player().isPlaying():
                    return sys.exit()
                if int(waitfornxnoti)<60 :
                    break
            notification(heading, "Next In 1 minuts", sleep=10000,icon=icon)
 