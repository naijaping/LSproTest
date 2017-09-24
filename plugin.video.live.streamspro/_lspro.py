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
import difflib as df    
import binascii
try:
    import pyDes
except Exception:
    pass
import xml.etree.ElementTree as ET

try:
    from xml.sax.saxutils import escape
except: traceback.print_exc()
try:
    import json
except:
    import simplejson as json
import SimpleDownloader as downloader

epgtimeformat2 = "%Y-%m-%d %H:%M:%S"
epgtimeformat = "%Y%m%d%H%M%S"
GUIDE={}
now = datetime.datetime.now().replace(microsecond=0)
from resources.lib import pyfscache
LS_CACHE_urlsolver = pyfscache.FSCache(xbmc.translatePath("special://temp/"),seconds=3600)

LS_CACHE_ALLUrlResolver = pyfscache.FSCache(xbmc.translatePath("special://temp/"),seconds=10*24*3600)
LS_CACHE_ytdl_domain = pyfscache.FSCache(xbmc.translatePath("special://temp/"),seconds=100*3600)
g_ignoreSetResolved=['plugin.video.dramasonline','plugin.video.f4mTester','plugin.video.shahidmbcnet','plugin.video.SportsDevil','plugin.stream.vaughnlive.tv','plugin.video.ZemTV-shani']
art_tags = ['thumbnail', 'fanart', 'poster','clearlogo','banner','clearart']
info_tags = ['director' ,'season','episode', 'writer','date', 'info', 'rating', 'studio', 'source','genre','plotoutline','credits','dateadded','tagline',"tvshowtitle","label"]
global gLSProDynamicCodeNumber
gLSProDynamicCodeNumber=0
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
if not logo_folder and os.path.isdir(os.path.join(profile, "Logo")):
    logo_folder = os.path.join(profile, "Logo")
    
groupm3ulinks = addon.getSetting('groupm3ulinks')

LivewebTVepg = os.path.join(profile, 'LivewebTVepg')

add_playlist = addon.getSetting('add_playlist')
ask_playlist_items =addon.getSetting('ask_playlist_items')
LSPlayOnlyOne =addon.getSetting('LSPlayOnlyOne')
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

if os.path.exists(favorites)==True:
    FAV = open(favorites).read()
else: FAV = []
if os.path.exists(source_file)==True:
    SOURCES = open(source_file).read()
else: SOURCES = []


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
            if response.info().get('Content-Encoding') == 'gzip':
                from StringIO import StringIO
                import gzip
                buf = StringIO( data)
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
            elif response.info().get('Content-Encoding') == 'deflate':
                decompress = zlib.decompressobj(-zlib.MAX_WBITS)
                inflated = decompress.decompress(data)
                inflated += decompress.flush()
                data = inflated                
            return data
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                if e.code == 404:
                    name = xbmc.getInfoLabel('ListItem.Label')
                    rmSource(name)
                addon_log('We failed with error code - %s.' % e.code)
                xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Site Shows Not available - "+str(e.code)+",10000,"+icon+")")
                
                    
            elif hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
                xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,We failed to reach a server. - "+str(e.reason)+",3000,"+icon+")")

def getSources():
        try:
            if os.path.exists(favorites) == True:
                addDir('Favorites','url',4, itemart , item_info)
            if addon.getSetting("searchotherplugins") == "true":
                addDir('Search Other Plugins','Search Plugins',25, itemart , item_info)
            if addon.getSetting("searchgoogle") == "true":
                addDir('Search on Google ','',1915,itemart , item_info)                

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
        addon.setSetting('dropboxfolder', "")
        addon.setSetting('new_file_source', "")
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,New source added.,5000,"+icon+")")
        xbmc.executebuiltin("XBMC.Container.Refresh")
        


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
                yield basename,filename

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
                    missingbytes=16-len(enckey)
                    enckey=enckey+(chr(0)*(missingbytes))
                    data=base64.b64decode(data)
                    decryptor = pyaes.new(enckey , pyaes.MODE_ECB, IV=None)
                    data=decryptor.decrypt(data).split('\0')[0]
            if re.search("(?:\s+)#EXTM3U",data) or '.m3u' in url or re.search(r"(?:\s+)#EXTINF:",data):

                return data
        elif data == None:
            if xbmcvfs.exists(url) or url.startswith("special://") :
                if url.startswith("smb://") or url.startswith("nfs://"):
                    copy = xbmcvfs.copy(url, os.path.join(profile, 'temp', 'sorce_temp.txt'))
                    if copy:
                        data = open(os.path.join(profile, 'temp', 'sorce_temp.txt'), "r").read()
                        xbmcvfs.delete(os.path.join(profile, 'temp', 'sorce_temp.txt'))
                    else:
                        addon_log("failed to copy from smb:")
                
                
                    
                else:
                    if url.startswith("special://"):
                        url = xbmc.translatePath(url).decode('utf-8','ignore')
                    data = open(url, 'r').read()
                    if re.match("#EXTM3U",data)or '.m3u' in url:

                        return data
            else:
                addon_log("Soup Data not found!")
                return
        if data and '<SetViewMode>' in data:
            try:
                viewmode=re.findall('<SetViewMode>(.*?)<',data)[0]
                xbmc.executebuiltin("Container.SetViewMode(%s)"%viewmode)
            except: pass
        return BeautifulSOAP(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)

def processPyFunction(data):
    try:
        if data and len(data)>0 and data.startswith('$pyFunction:'):
            data=doEval(data.split('$pyFunction:')[1],'',None,None )
    except: pass
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

  
    if "###LSPRODYNAMIC###" in url:
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
                        
                        addon_log('There was a problem adding directory from getData(): ')
                
           
            else:
                    if disableepg == 'true' :
                        map(getItems,soup('item'),[fanart])
                    else:
                        total = len(soup("item"))
                        if len(soup('epg')) > 0 :
                            _O_info = epgxml_db()
                            allsources = epgxml_db().getallepgsources()
                            if allsources:
                                allsources = [i[0] for i in allsources if i[0]]
                                for epg in soup("epg"):
                                        epglink= epg.get('tvgurl')
                                        
                                        if epglink and epglink not in allsources:
                                            houroffset = epg.get('tvgshift') or '0'
                                            updateafterhour = epg.get('updateafterhour','24')
                                            _O_info = epgxml_db(epglink,houroffset=houroffset)
                                            _O_info._update_xml()
                            else:
                                for epg in soup("epg"):
                                    if epg.get('tvgurl'):
                                        houroffset = epg.get('tvgshift') or '0'
                                        updateafterhour = epg.get('updateafterhour','24')
                                        _O_info = epgxml_db(epg.get('tvgurl'),houroffset=houroffset)
                                        _O_info._update_xml()
      
                            for index,i in enumerate(soup("item")):
                                name=getxmlname(i("title")) #channelepg
                                itemart,item_info=_O_info.channelepg(name)
                                    
                                getItems(i, fanart,itemart,item_info, total=total)


                        else:
                            [getItems(i, fanart, total=total) for index,i in enumerate(soup("item")) if not i("itemepg")]                    
        elif soup:
            if searchterm:
                m3upat = re.compile(r"\s?#EXTINF:.+?,%s.*?[\n\r]+[^\r\n]+" %searchterm,  re.IGNORECASE )
                match = m3upat.findall(soup)
                map(parse_m3u,match)
                xbmc.log('m3333u 0000match: %s' %str(len(match)),xbmc.LOGNOTICE)
                return
            parse_m3u(soup,url)
        if not soup:
            return "unsuccessful"


def sdevil():
    import shutil
    import zipfile
    dialog = xbmcgui.Dialog()
    import requests
    box_url = 'https://app.box.com/index.php?rm=box_download_shared_file&shared_name=b6tqh5trzcpqb1h16lfpfgyewqm3ur94&file_id=f_{0}'
    c = requests.get('https://app.box.com/s/b6tqh5trzcpqb1h16lfpfgyewqm3ur94', allow_redirects=False)
    cookie= dict(c.cookies)
    res = requests.get('https://app.box.com/s/b6tqh5trzcpqb1h16lfpfgyewqm3ur94',cookies = cookie)
    SDevil = xbmc.translatePath(os.path.join('special://','home/addons/plugin.video.SportsDevil'))

    match = re.search(r'data-resin-file_id\=&quot;([^&]+)',res.content)
    version=os.path.join(SDevil,"version.txt")
    c = requests.get(box_url.format(match.group(1)),cookies=cookie, allow_redirects=False)
    url= c.headers["Location"]
    filename= 'Sdevil.zip'
    if 'download' in url:
        
            # NOTE the stream=True parameter
        try:
            c= requests.head(url,cookies=cookie, allow_redirects=False)
            contentlength = c.headers.get('content-length')
            contentdisposition = c.headers.get('content-disposition')
            filename = re.compile(r"filename\W+([^\";']+)").findall(contentdisposition)[0]
            
        except:
            pass
        UserDataFolder=xbmc.translatePath(os.path.join('special://profile/addon_data/',filename))    
        r = requests.get(url, stream=True)
        with open(UserDataFolder, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        getzip = zipfile.ZipFile(UserDataFolder, 'r')
        if os.path.isdir(SDevil):
            shutil.rmtree(SDevil,ignore_errors=True)
        getzip.extractall(xbmc.translatePath(os.path.join('special://','home/addons/'))) 
        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,ALL DONE - ,4000)")
        with open(version,"w") as f:
            f.write(filename)
        th= urllib.urlretrieve("https://www.dropbox.com/s/ltv3qg842e1lum7/livestreamerXBMCLocalProxy.py?dl=1",os.path.join(SDevil,"service/livestreamerXBMCLocalProxy.py"))
        th= urllib.urlretrieve("https://www.dropbox.com/s/4udsbyfje53hj3n/proxy_service.py?dl=1",os.path.join(SDevil,"service/proxy_service.py"))
def down_url(url,filename=None,_out=None,replacefile=False):
    ZIP = False
    get_file_name = url.split('/')[-1]
    if len(get_file_name) == 0:
        get_file_name = url
    if filename and os.path.isfile(filename) and not replacefile:
        return filename
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
                raise
        except:
            filename = cacheKey(url)
            pass
        filename=os.path.join(profile,filename)
    try:
        with open(filename, 'wb') as f:
            while True:
                buffer = song.read(block_sz)
                if not buffer:
                    break

                size += len(buffer) 
                f.write(buffer)
                if not file_size == 20:
                    pDialog.update(int(size * 100. / file_size),message.format(str(int(size * 100. / file_size)),get_file_name))
            pDialog.close()
    except:
        if os.path.exists(filename):
            os.remove(filname)
        pass    
    
    pDialog.close()
    xbmc.sleep(1) #change from 10 to 0.5
    return filename
def contentfromZip(filename,_out=None,choosefile=None):
        
    if open(filename).read(1024).startswith('\x50\x4b\x03\x04') or filename.endswith(".zip"):
        #try:
            if not _out:
                _out = os.path.join(profile,cacheKey(filename))
            import zipfile
        
            zfile = zipfile.ZipFile(filename, 'r')
            zfile.extractall(path=_out)
            
        #except Exception:
            #return
            zfile.close()
            os.remove(filename)
            allfiles=os.listdir(_out)
            if len(allfiles) == 1:
                _out = os.path.join(_out,allfiles[0])
            elif choosefile:
                choice = index = xbmcgui.Dialog().select('Multiple Files', allfiles)
                if choice:
                    _out = os.path.join(_out,allfiles[choice])
            return _out        
    elif open(filename).read(1024).startswith('\x1f\x8b\x08'):
            import gzip
            zfile = gzip.open(filename, 'rb')
            content= zfile.read()
            zfile.close()
            with open(filename,"wb") as f:
                 f.write(content)
    
                
            return filename
    return
            
        
        
    #magic_dict = {
    #"\x1f\x8b\x08": "gz",
    #"\x42\x5a\x68": "bz2",
    #"\x50\x4b\x03\x04": "zip"
    #}
    #data = zlib.decompress(data, zlib.MAX_WBITS + 16)
    #f.write(data)
    #f.close()    
    
            
# borrow from https://github.com/enen92/P2P-Streams-XBMC/blob/master/plugin.video.p2p-streams/resources/core/livestreams.py
def removeNonAscii(s): return "".join(filter(lambda x: ord(x)<128, s))
def deg(string,level=xbmc.LOGNOTICE):

        try:
            if isinstance(string,list):
                string= "\n".join(string)
            elif isinstance(string,tuple):
                string= "\n".join(map(str,string))
            xbmc.log("[LSPRO::]: %s" %str( removeNonAscii(str(string))),level)
        except:
            traceback.print_exc()
            pass
@LS_CACHE_ALLUrlResolver
def ALLUrlResolver():
    from urlresolver.resolver import UrlResolver
    classes = UrlResolver.__class__.__subclasses__(UrlResolver) 
    allurlsolvedomains = []
    [allurlsolvedomains.append(res_domain.lower()) for resolver in classes for res_domain in resolver.domains]
        
            
    return allurlsolvedomains 
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

        xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Hostname not found in Youtube-dl module,5000,"")")
    return YTdl

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
    getepg= False 
    tvgurls = re.compile(r'#EXTM3U\s*tvgurl=[\'"](.*?)[\'"]',re.IGNORECASE).findall(content)
        
    if addon.getSetting("alwaysfindepg") == 'true'and len(m3uepgfileorurl) > 0:
        tvgurls.append(m3uepgfileorurl)
        tvgurls= set(tvgurls)
    itemsname=[]
    names = [(index,i[1]) for index,i in enumerate(match)]
    if tvgurls:
        try:
           
            getepg=True
            for i in tvgurls:
                _O_info = epgxml_db(i)
                _O_info._update_xml() 
            m3uitems= [(m3ustream_url(match[matchindex][2],match[matchindex][0],name), m3u_iteminfo(match[matchindex][0],match[matchindex][1],name,_O_info))for matchindex,name in names]
                    
            [addLink(stream_url,stream_info[0],stream_info[1],stream_info[2]) for stream_url,stream_info in m3uitems if stream_url]
        except:
            pass
    elif not tvgurls and addon.getSetting("alwaysfindepg") == 'true':
                _O_info = epgxml_db()
                m3uitems= [(name,m3ustream_url(match[matchindex][2],match[matchindex][0],name),_O_info.channelepg(name) )for matchindex,name in names]
                #deg(str(m3uites))    
                [addLink(stream_url,stream_info[1].get('title',name),stream_info[0],stream_info[1]) for name,stream_url,stream_info in m3uitems if stream_url]
       
    
    if len(itemsname) > 0:
        m3uitems=  [(m3ustream_url(match[matchindex][2],match[matchindex][0],name), m3u_iteminfo(match[matchindex][0],match[matchindex][1]))for matchindex,name in itemsname]
    elif not itemsname and not getepg and addon.getSetting("alwaysfindepg") == 'false':
        
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
                stream_url = stream_url +"&in_mode=18"
            elif mode_type == 'addDirfr_gsearch':
                
                try:
                    item_info['showcontext'] = 'true'
                    addDir(channel_name, stream_url, 1915, itemart,item_info)
                    return
                except Exception:
                    return               
            elif mode_type == 'ftv':
                stream_url = 'plugin://plugin.video.F.T.V/?name='+urllib.quote(channel_name) +'&url=' +stream_url +'&mode=125&ch_fanart=na'
        elif (tsdownloader and '.ts' in stream_url) and not 'f4mTester' in stream_url:
            stream_url = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(stream_url)+'&amp;streamtype=TSDOWNLOADER&name='+urllib.quote(channel_name)
        elif hlsretry and '.m3u8' in stream_url and not 'f4mTester' in stream_url:
            stream_url = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(stream_url)+'&amp;streamtype=SIMPLE&name='+urllib.quote(channel_name)
        elif stream_url.strip().startswith("f4m://"):
            stream_url = 'plugin://plugin.video.f4mTester/?url='+urllib.quote_plus(stream_url.strip().replace("f4m://",""))+'&amp;streamtype=HLSRETRY&name='+urllib.quote(channel_name)
        return stream_url

def m3u_iteminfo(other,channel_name,getepg=None,_O_info=None):
        item_info = {}
        itemart={}
        itemart['thumb'] = m3uthumb 
        itemart['fanart'] = ''
        if ':' in channel_name:
            co,_name = channel_name.split(':',1)
            channel_name = '%s [COLOR yellow][%s][/COLOR]' %(_name,co)
        else:
            _name = channel_name
        if _O_info :

            itemart,item_info = _O_info.channelepg(getepg)
        else:
            plot = re_me(other,'plot=[\'"](.*?)[\'"]')
            if plot:
                item_info['plot'] = plot
        thumbnail = re_me(other,'tvg-logo=[\'"](.*?)[\'"]')
        if thumbnail and thumbnail.startswith('http'):
                    itemart['thumb'] = thumbnail
        elif not logo_folder == "":
            thumbnail = os.path.join(logo_folder , _name.lower().replace(' ','')+'.png')
            if xbmcvfs.exists(thumbnail):
                #
            
                itemart['thumb'] = thumbnail
        if use_thumb == 'true':
            itemart["fanart"] = itemart.get("thumb")
        return channel_name,itemart,item_info
def getlogofromfolder(name,genre=None):
        alt_name=None
        name=name.lower()
        ss=name.split(" ")
        #if "hd" in ss:
        _excl = ["hd","usa","india"]
        [ss.remove(x)for x in _excl if x in ss]


        #if len(ss) >1:
        alt_name = "".join(ss).strip()
        name=name.replace(' ','')
        

        if os.path.isdir(logo_folder):
            if genre:
                thumb_folder =  os.path.join(logo_folder , genre)
            else:
                thumb_folder = logo_folder
            thumbnail = os.path.join(thumb_folder , name+".png")
            if not xbmcvfs.exists(thumbnail) and alt_name:
                #
                thumbnail = os.path.join(thumb_folder , alt_name.lower().replace(' ','')+".png")
                
            if not xbmcvfs.exists(thumbnail):
                    thumbnail = icon
            return thumbnail
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

def live_tv_name(title):
    title=re.sub(r"(?is)\[/?COLOR.*?\]","",title)
    title = re.sub('&#(\d+);', '', title)
    title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '\"').replace('&amp;', '&')
    #deg("removed color "+ title)
    title = title.strip()
    title = title.lower()
    title= title.replace("usa","")
    title= title.replace("india","")
    title= title.replace("hd","")
    
    title = re.sub('&TV', 'AND TV', title)        
    return title.lower()
 
def getSubChannelItems(name,url,fanart):
        soup = getSoup(url)
        channel_list = [i.subitems for i in soup('subchannel') if  i.find('name').string == name]
        map(getItems,channel_list[0],[fanart])
def getxmlname(i):        
            try:
                name = i[0].string
                if name is None:
                    name = 'unknown?'
                elif '[COLOR #' in name:
                    name= ''.join([brace.replace(']','00]',1) for brace in name.split('#')])
                try:
                    
                    if '$pyFunction:' in name:
                        name=processPyFunction(name)
                except: pass                
            except:
                addon_log('Name Error')
                name = 'NameError'
            return name
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
            #name=getxmlname(item('title'))
            try:
                name = item('title')[0].string
                if name is None:
                    name = 'unknown?'
                elif '[COLOR #' in name:
                    name= ''.join([brace.replace(']','00]',1) for brace in name.split('#')])
                try:
                    
                    if '$pyFunction:' in name:
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
                elif len(item('yt-dl')) >0:
                    for i in item('yt-dl'):
                        if not i.string == None:
                            ytdl = i.string + '&in_mode=18'
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
                                utube = 'plugin://plugin.video.youtube/play/?&order=default&playlist_id=' + i.string + "&play=1"
                            elif i.string.startswith('PL') or i.string.startswith('UU'):
                                utube = 'plugin://plugin.video.youtube/play/?playlist_id=' + i.string+ "&play=1"
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
                                imdb = 'plugin://plugin.video.covenant/?action=play&imdb='+i.string
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
                            resolver = i.string +'&in_mode=19'
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
                
                    
            if not itemart:
                itemart =  dict((art_tag.replace('thumbnail','thumb'),item(art_tag)[0].string) for art_tag in art_tags if item(art_tag) and item(art_tag)[0].string is not None)            
            if not item_info:

                item_info =  dict((art_tag.replace('info','plot'),item(art_tag)[0].string) for art_tag in info_tags if item(art_tag)and item(art_tag)[0].string is not None)
                item_info['showcontext'] = 'true'
          
            thumbnail = itemart.get("thumb")
             #    
            if not thumbnail and  len(item("thumbnail")) >0: #overwrite epg thumb if <thumbnail>
                try:
                    thumbnail=item('thumbnail')[0].string
                    if  thumbnail.startswith('$pyFunction:'):                
                        thumbnail=processPyFunction(thumbnail)
                    itemart['thumb'] = thumbnail 
                except:
                    pass
            elif not thumbnail and not logo_folder == "":
                thumbnail=itemart['thumb'] = getlogofromfolder(name)

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

            regexs = None
            if item('regex'):
                try:
                    reg_item = item('regex')
                    regexs = parse_regex(reg_item)
                except:
                    pass
            try:
                
                if len(url) > 1:
                    parse_multiple_links(url,name,itemart,item_info,regexs,total,add_playlist,ask_playlist_items)
                else:
                    if dontLink:
                        return name,url[0],regexs
                    if isXMLSource:
                            if not regexs == None: #<externallink> and <regex>
                                item_info['showcontext'] = '!!update'
                                addDir(name.encode('utf-8'),ext_url[0].encode('utf-8'),1,itemart,item_info,regexs,url[0].encode('utf-8'))
                            else:
                                item_info['showcontext'] = 'source'
                                addDir(name.encode('utf-8'),ext_url[0].encode('utf-8'),1,itemart,item_info)
                    elif isJsonrpc:
                        item_info['showcontext'] = 'source'
                        addDir(name.encode('utf-8'),ext_url[0],53,itemart,item_info)
                        #xbmc.executebuiltin("Container.SetViewMode(500)")
                    else:
                        try:
                            if '$doregex' in name and not getRegexParsed==None:
                                
                                tname,setres=getRegexParsed(regexs, name)
                                
                                if not tname==None:
                                    name=tname
                        except: pass
                        try:
                            if '$doregex' in thumbnail and not getRegexParsed==None:
                                tname,setres=getRegexParsed(regexs, thumbnail)
                                if not tname==None:
                                    thumbnail=tname
                        except: pass                        
                        
                        addLink(url[0],name.encode('utf-8', 'ignore'),itemart,item_info,regexs,total)
                    #print 'success'
            except:
                traceback.print_exc()
                addon_log('There was a problem adding item - '+name.encode('utf-8', 'ignore'))

def parse_multiple_links(url,name,itemart,item_info,regexs,total,add_playlist,ask_playlist_items):                    
    alt = 0
    playlist = []
    #if LSPlayOnlyOne == "false":
    ignorelistsetting=True if '$$LSPlayOnlyOne$$' in url[0] or addon.getSetting('LSPlayOnlyOne') == "true"  else False
    for i in url:
            domain = __top_domain(i)
            if  add_playlist == "false" and not ignorelistsetting:
                alt += 1
                addLink(i,'%s) %s' %(alt, name.encode('utf-8', 'ignore')),itemart,item_info,regexs,total)
            elif  (add_playlist == "true" and  ask_playlist_items == 'true') or ignorelistsetting:
                if regexs:
                    playlist.append(i+'&regexs='+regexs)
                elif  domain in ALLUrlResolver():
                    playlist.append(i+'&in_mode=19')
                else:
                    playlist.append(i)
            elif ask_playlist_items == 'false' and "$$lsname=" in i:
                playlist.append(i.split("$$lsname=")[0])
            else:
                playlist.append(i)
    if len(playlist) > 1:
        item_info['playlist'] = playlist
        addLink('playlist', name.encode('utf-8'),itemart,item_info,regexs,total)

                    
regex_tags = ['name', 'expres','listrepeat' , 'proxy','referer', 'page', 'agent', 'post', 'rawpost', 'connection', 'notplayable','noredirect', 'origin', 'accept', 'includeheaders', 'x-req', 'x-forward', 'htmlunescape','readcookieonly', 'cookiejar', 'setcookie', 'appendcookie', 'ignorecache', 'listrepeat', 'x-addr']


def parse_regex(reg_item):
    regexs = {}
    for i in reg_item:
        # print i('name')[0].string
        regexs[i('name')[0].string] = {}
        regexs[i('name')[0].string]['page'] = i('page')[0].string
        for tag in regex_tags:
            if len(i(tag)) > 0:
                if not i(tag)[0].string == None:
                    regexs[i('name')[0].string][tag] = i(tag)[0].string
                # if not regexs[i('name')[0].string][tag]:
                else:
                    regexs[i('name')[0].string][tag] = ''
    regexs = urllib.quote(repr(regexs))
    # print regexs
    return regexs                    
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
            try:
                rnumber+=1

                newcopy=copy.deepcopy(regexs)
                listrepeatT=listrepeat
                i=0
                for i in range(len(obj)):
                    if len(newcopy)>0:
                        for the_keyO, the_valueO in newcopy.iteritems():
                            if the_valueO is not None:
                                for the_key, the_value in the_valueO.iteritems():
                                    if the_value is not None:                                

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
                        current_proxies=urllib2.ProxyHandler(urllib2.getproxies())
        
        
                        #print 'getting pageUrl',pageUrl
                        req = urllib2.Request(pageUrl)
                        if 'proxy' in m:
                            proxytouse= m['proxy']

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
                            splitpost=postData.split(',');
                            post={}
                            for p in splitpost:
                                n=p.split(':')[0];
                                v=p.split(':')[1];
                                post[n]=v
                            post = urllib.urlencode(post)

                        if 'rawpost' in m:
                            post=m['rawpost']

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

                            return listrepeat,eval(val), m,regexs,cookieJar
#                        print 'url k val',url,k,val
                        #print 'repr',repr(val)
                        
                        try:
                            url = url.replace(u"$doregex[" + k + "]", val)
                        except: url = url.replace("$doregex[" + k + "]", val.decode("utf-8"))
                    else:
                        if 'listrepeat' in m:
                            listrepeat=m['listrepeat']

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
    #deg(str(response))
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

    e = ''
    d = ''#32823

    #sUnpacked = str(__unpack(p, a, c, k, e, d))
    sUnpacked1 = str(__unpack(p1, a1, c1, k1, e, d,iteration))


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
    global gLSProDynamicCodeNumber
    gLSProDynamicCodeNumber=gLSProDynamicCodeNumber+1    
    ret_val=''
    if not functions_dir:
        functions_dir = profile    

        filename='LSProdynamicCode%s.py'%str(gLSProDynamicCodeNumber)
        sys.path.insert(0,functions_dir)
    else:
        filename='LSProdynamicCode%s.py'%str(gLSProDynamicCodeNumber)
    #if functions_dir not in sys.path :
        sys.path.insert(0,functions_dir)        
    filenamewithpath = os.path.join(functions_dir,filename)

    f=open(filenamewithpath,"wb")
    f.write("# -*- coding: utf-8 -*-\n")
    f.write(fun_call.encode("utf-8"));
    
    f.close()

    LSProdynamicCode = import_by_string(filename.split('.')[0],filenamewithpath)

    ret_val=LSProdynamicCode.GetLSProData(page_data,Cookie_Jar,m)
    try:
        return str(ret_val)
    except: return ret_val

def import_by_string(full_name,filenamewithpath):
    try:
        
        import importlib
        return importlib.import_module(full_name, package=None)
    except:
        import imp
        return imp.load_source(full_name,filenamewithpath)
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
        

def getUrl(url, cookieJar=None,post=None, timeout=20, headers=None, noredir=False,output='cookie'):


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
    #try:
    #    import livestreamer
    ##except:
        #from resources.lib.streamlink import Streamlink # need to fix module relative path
        #import streamlink
    from resources.lib import streamlink_solver    
    final_url = streamlink_solver.GetLivestreamerLink(url)
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
def play_playlist(name, mu_playlist,queueVideo=None):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        #print 'mu_playlist',mu_playlist
        if ('$$LSPlayOnlyOne$$' in mu_playlist[0] or addon.getSetting('LSPlayOnlyOne') == "true") and not queueVideo:
            mu_playlist[0]=mu_playlist[0].replace('$$LSPlayOnlyOne$$','')
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
                item_info['plot'] = xbmc.getInfoLabel('ListItem.Plot')
                itemart['thumb'] = xbmc.getInfoLabel('ListItem.Art(thumb)')
                itemart["fanart"] = xbmc.getInfoLabel('ListItem.Art(fanart)')                
                if "&in_mode=19" in mu_playlist[index]:
                        #playsetresolved (urlsolver(mu_playlist[index].replace('&mode=19','')),name,iconimage,True)
                    liz = xbmcgui.ListItem(playname)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    urltoplay=urlsolver(mu_playlist[index].replace('&in_mode=19','').replace(';',''))
                    liz.setPath(urltoplay)
                    #xbmc.Player().play(urltoplay,liz)
                    played=tryplay(urltoplay,liz)
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
                    #xbmc.Player().play(url2,liz)
                    played=tryplay(url2,liz)

                else:
                    url = mu_playlist[index]
                    url=url.split('&regexs=')[0]
                    liz = xbmcgui.ListItem(playname)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    liz.setPath(url)
                    #xbmc.Player().play(url,liz)
                    played=tryplay(url,liz)
                    print 'played',played
                print 'played',played
                if played and xbmc.Player().isPlaying(): return
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
                    d_name=__top_domain(i)
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
                if "&in_mode=19" in mu_playlist[index]:
                        #playsetresolved (urlsolver(mu_playlist[index].replace('&mode=19','')),name,iconimage,True)
                    liz = xbmcgui.ListItem(playname)
                    item_info['Title'] = playname
                    liz.setInfo(type='Video', infoLabels=item_info)
                    liz.setArt(itemart)
                    liz.setProperty("IsPlayable","true")
                    urltoplay=urlsolver(mu_playlist[index].replace('&in_mode=19','').replace(';',''))
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

                elif mu_playlist[index].startswith("plugin://"):
                    #Container.Update(%s?url=%s&mode=60&name=%s,return)
                    xbmc.executebuiltin('XBMC.RunPlugin('+mu_playlist[index]+')')
                    
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
            item_info['plot'] = xbmc.getInfoLabel('ListItem.Plot')
            itemart['thumb'] = xbmc.getInfoLabel('ListItem.Art(thumb)')
            itemart["fanart"] = xbmc.getInfoLabel('ListItem.Art(fanart)')
            for i in mu_playlist:
                item += 1
                info = xbmcgui.ListItem('%s) %s' %(str(item),name))
                info.setArt(itemart)
                info.setInfo(type="Video", infoLabels= item_info)
                # Don't do this as regex parsed might take longer
                try:
                    if "$doregex" in i:
                        sepate = i.split('&regexs=')
#                        print sepate
                        url,setresolved = getRegexParsed(sepate[1], sepate[0])
                    elif "&in_mode=19" in i:
                        url = urlsolver(i.replace('&in_mode=19','').replace(';',''))                        
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
    names=[]
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
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.ZemTV-shani)"):
        pluginsearchurls.append("plugin://plugin.video.ZemTV-shani/?mode=13&amp;name=Sports&amp;url=Live")
        names.append("ZemTV Sports")

    dialog = xbmcgui.Dialog()
    index = dialog.select('Choose a video source', names,preselect=2)
 
    if index >= 0:
        url = pluginsearchurls[index]

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
        showcontext = item_info.pop('showcontext',None)
        liz=xbmcgui.ListItem(name)
        item_info["Title"] = name
        iconimage = itemart.get('thumb')
        if not iconimage:
            itemart['thumb'] =iconimage = icon
        liz.setInfo(type="Video", infoLabels= item_info)
        liz.setArt(itemart)
        

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
        json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s","media":"video","properties":[ "plot","director", "genre","votes","duration","trailer","premiered","thumbnail","title","year","dateadded","fanart","rating","season","episode","studio","mpaa"]},"id":1}') %queryurl
    
    
    json_folder_detail = json.loads(sendJSON(json_query))
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
        #deg(str(json_folder_detail['result']['files']))
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
                    #studio = i.get('studio')
                    #if studio:
                    #    item_info["showcontext"] = studio
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

        NoturlResolver=False
        mode = '12'
        if url.endswith((".mkv",".m3u8",".ts",".f4m",".flv",".mp4",".avi",".mp3")) or "?wmsAuthSign=" in url or url.startswith("rtmp"):
            
            NoturlResolver = True
            
        if regexs:
            mode = '17'
            if 'listrepeat' in regexs:
                isFolder=True
#                print 'setting as folder in link'
            if xbmc.getCondVisibility("Player.HasMedia"):
                contextMenu.append(('[COLOR white]!!Download Currently Playing!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=21&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
        elif '&in_mode=' in url:
            
            mode = str(url.rsplit('&in_mode=',1)[1])   
            url = re.sub('&in_mode=\d+', '', url)
                

            if mode == "18" :
                contextMenu.append(('[COLOR white]!!Download!![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=23&name=%s)'
                                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name))))
            else:
                contextMenu.append(('[COLOR white]!!Download !![/COLOR]','XBMC.RunPlugin(%s?url=%s&mode=21&name=%s)'
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
        elif  not NoturlResolver and not isinstance(url,list):
            #deg("check domain in urlresolver")
                
            domain = __top_domain(url)
            alldomains_from_urlresolver = ALLUrlResolver()
            #deg(alldomains_from_urlresolver)
            if domain in alldomains_from_urlresolver:
                deg("domain %s found in ALLUrlResolver" %domain)
                mode = '19'
            #
        if mode == "12" or mode == "19":
            if xbmc.getCondVisibility("Player.HasMedia"):
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

        liz=xbmcgui.ListItem(name,item_info.get("Label"," "))
        iconimage = itemart.get('thumb')
        
                   
        if not iconimage:    
            iconimage=itemart['thumb'] = icon
        try:
            u += "&thumb="+urllib.quote_plus(iconimage)
        except: pass
        try:
            u += "&plot="+ urllib.quote_plus(item_info.get("plot",name))
            #try:
            #    response = json.loads(request)
            #except UnicodeDecodeError:
            #    response = json.loads(request.decode('utf-8', 'ignore'))            
        except UnicodeDecodeError: 
            u += "&plot="+ urllib.quote_plus(normalize(item_info.get("plot",name)))
        except:    
            pass
        #u += "&iconimage="+urllib.quote_plus(iconimage) 
        #deg(str(item_info))
        showcontext = item_info.pop('showcontext',None)
        #item_info.pop("thumb",None)
        liz.setInfo(type="Video", infoLabels=item_info)
        liz.setArt(itemart)        
        #liz.setProperty( "starttime", str(datetime.datetime.utcfromtimestamp(float(item_info.get("starttime",0.0))) ))
        #liz.setProperty( "endtime", str(datetime.datetime.utcfromtimestamp(float(item_info.get("endtime",0.0))) ) )       
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
        
        
        #deg(str(item_info))
        fanart = itemart.get('fanart')  or FANART          
        #deg(str(showcontext))
        if showcontext:
            #contextMenu = []
            if isinstance(showcontext,dict):
                if showcontext.get("epgcontext"):
             
                    contextMenu.append(
                        ('[COLOR yellow]Find Show/Movie in Exodus[/COLOR]','Container.Update(%s?mode=54&url=%s&name=%s,return)'
                         %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name.split('[')[0])))
                         )      
                    contextMenu.append(
                        ('[COLOR cyan]What\'s on Today[/COLOR]','Container.Update(%s?mode=26&url=%s&name=%s,return)'
                         %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name.split('[')[0])))
                         )  
            else:
                
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
                if 'YTsearch' in showcontext :  # Did not work
                        YT_search_name = re.sub(r"\[/?\w{4}.*?\]" ,r'',name.split('(')[0],re.I) #remove [/color]
                        
                        youtube_con = 'plugin://plugin.video.youtube/kodion/search/query/?q=' + urllib.quote_plus(YT_search_name +' album' )
                        addon_log("youtube kodion search %s" %youtube_con,xbmc.LOGNOTICE) 
                        contextMenu.append(('[COLOR white]Play from Youtube[/COLOR]', 'XBMC.RunPlugin(%s?url=%s&mode=1899&name=%s)'% (sys.argv[0], urllib.quote_plus(youtube_con), urllib.quote_plus(name))))
                if 'addDir' in showcontext :
                    contextMenu.append(('[COLOR white]Play from Youtube[/COLOR]', 'XBMC.RunPlugin(%s?url=%s&mode=1&name=%s)'% (sys.argv[0], urllib.quote_plus(youtube_con), urllib.quote_plus(name))))

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
        except: 
            traceback.print_exc()
            pass
        #print 'adding',name
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total,isFolder=isFolder)
        #print 'added',name
        return ok
#Exodus
def normalize(title):
    try:
        try: return title.decode('ascii').encode("utf-8")
        except: pass
        import unicodedata
        return str( ''.join(c for c in unicodedata.normalize('NFKD', unicode( title.decode('utf-8') )) if unicodedata.category(c) != 'Mn') )
    except:
        return title
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
    import xbmcgui
    if ".mpd" in url:

            item = xbmcgui.ListItem(name)
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            item.setProperty('inputstream.adaptive.manifest_type', 'mpd')  
            item.setProperty(u'IsPlayable', u'true')
            xbmc.Player().play(url,item) 
            return
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
xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

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
def getepgcontent(epg,replacefile=False):
    extracted_dir = None
    if epg and isinstance(epg, basestring):
        url=epglink=epg
        epgfile = "0"
    #        
    if not xbmcvfs.exists(LivewebTVepg):
        xbmcvfs.mkdir(LivewebTVepg)
    if not epgfile == "0":
        filename = os.path.join(LivewebTVepg,cacheKey(url))
        
        extracted_dir = os.path.join(LivewebTVepg,cacheKey(url)+'_extracted')#dir

    else:
        if "\\" in url:
            epgxml = url
        else:
            #epgxml = os.path.join(LivewebTVepg,cacheKey(url))
            filename = os.path.join(LivewebTVepg,cacheKey(url))

    if "://" in url :
           
            epgxml = down_url(url,filename,replacefile=replacefile)
            ItsZip = contentfromZip(epgxml,extracted_dir)
            
            if ItsZip:
                if os.path.isdir(ItsZip) and not epgfile == "0":
                    epgxml = os.path.join(ItsZip,epgfile)
                elif os.path.isfile(ItsZip):
                    return ItsZip
                
 
class epgxml_db():
    def __init__(self,epgxml='i',houroffset='0'):
        self.source= houroffset + '_ ' +cacheKey(epgxml)
        self.channel = ''
        self.url = epgxml
        try:
            from sqlite3 import dbapi2 as database
        except:
            from pysqlite2 import dbapi2 as database
           
        self.now = datetime.datetime.now().replace(microsecond=0)
        self.channeldisplayname=""
        self.houroffset = houroffset
        self.databasePath = os.path.join(profile, 'lsproepg.db')
        self.dbcon = database.connect(self.databasePath)
        self.c = self.dbcon.cursor()  
        self.c.execute('CREATE TABLE IF NOT EXISTS up_source(source_id TEXT, title TEXT, url TEXT,expire_date TIMESTAMP,houroffset integer,last_updated TIMESTAMP, PRIMARY KEY (source_id))') #  

        self.c.execute('CREATE TABLE IF NOT EXISTS channels(id TEXT,epgid TEXT, alt_title TEXT, categories TEXT, logo TEXT,thumb TEXT, lang TEXT, source TEXT,channelsources TEXT, PRIMARY KEY (id))')
        self.c.execute('CREATE TABLE IF NOT EXISTS programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, subTitle TEXT, image_large TEXT, source TEXT)') 


        self.expire=[0]
        self.Programfailed = 0
        self.updateurl = []
        
            
        
    
    
    
    def predefinedchannel(self):
        url='https://www.dropbox.com/s/ds9uuve6odvg0zr/ALLCHANNELS2?dl=1' 
        data=makeRequest(url) 
        for id,  alt_title, categories, logo, thumb, lang, source, channelsources in json.loads(data):
            self.c.execute('INSERT OR IGNORE INTO channels(id,epgid,  alt_title, categories, logo, thumb, lang, source, channelsources) VALUES( ?, ?, ?, ?, ?, ?,?,?,?)', [id, id,  alt_title, categories, logo, thumb, lang, source, channelsources]) 
        self.dbcon.commit()
        
        
    def _update_xml(self):
        up_source=self.c.execute('SELECT * FROM up_source WHERE source_id=?',[self.source]) 
        up_source = up_source.fetchone()

        if up_source:
            self.url = up_source[2]
                               
            #if abs(int(time.time()) - int(up_source[5])) < 60*60 or not self.updateurl :
            return 
        if not self.updateurl and up_source:
            #if up_source :
                self.url = up_source[2]
                expire = up_source[3] #2017072014
                last_updated = up_source[5]
                deg(str(last_updated))
                   
                if abs(int(time.time()) - int(last_updated)) < 60*60 or not self.updateurl :
                        deg("Returning from forceupdate")
                        return
        self.pDialog = xbmcgui.DialogProgressBG()
        self.pDialog.create("Updating EPG", " EPG: %s .\nPlease Wait.." %self.url.split("/")[-1] )
        
        self.c.execute('DELETE FROM programs WHERE source=?',[self.source])
        #self.c.execute('DROP TABLE channels')
        self.c.execute("VACUUM")
        self.c.execute('DELETE FROM up_source WHERE source_id=?',[self.source])             
        epgxml=  getepgcontent(self.url,replacefile=True)
        
        self.pDialog.update(5, "EPG updated url %s" %epgxml)
        if not xbmcvfs.exists(self.databasePath):
            self.pDialog.update( 15 ,"Adding Predefined Channel ")
            xbmc.log("should see this statement once",xbmc.LOGNOTICE)
            

            self.predefinedchannel()
        self.get_channels_db(epgxml)

        #self.dbcon.commit()
        if "whatsonindia_data.json" in self.url:
            self.c.execute('INSERT OR IGNORE INTO up_source(source_id,title,url,expire_date,houroffset,last_updated) VALUES(?,?,?,?,?,?) ',[self.source,self.url.split("/")[-1],self.url,max(self.expire),self.houroffset,int(time.time())])         
        
        else:
            self.epg_programes_todb()
            self.c.execute('INSERT OR IGNORE INTO up_source(source_id,title,url,expire_date,houroffset,last_updated) VALUES(?,?,?,?,?,?) ',[self.source,self.url.split("/")[-1],self.url,max(self.expire),self.houroffset,int(time.time())])         
        self.c.execute('DROP INDEX IF EXISTS Idx3 ')
        self.c.execute('CREATE INDEX  Idx3 ON programs(channel,start_date, end_date)')
        self.dbcon.commit()
        self.pDialog.close()
        #up_source=self.c.execute('SELECT * FROM up_source WHERE source_id=?)',[source_id]) 
    
    def get_channels_db(self,epgxml):
            self.pDialog.update( 30 ,"Adding Channels from Epg ")
            #self.predefinedchannel()
            epgfile = open(epgxml,"rb").read()
        #try:
            if epgfile is not None:
                    try:
                        self.root = ET.fromstring(epgfile)
                    except:
                        root = None
                        deg("Warning!! Not Valid XML file format")
                    
                    if self.root is not None:
                        #pDialog= xbmcgui.DialogProgressBG()
                        channels = self.root.findall("./channel")
                        self.pDialog.update( 20 ,"Adding channels ")
                        channelsources=[]
                        lang="English"
                        
                        for i in channels :
                            #print i
                            #channel= cleanname(i.get("id"),removecolorcode=True) 
                            epgid= i.get("id").decode("utf-8","ignore")
                            channeldisplayname = i.find("display-name").text.capitalize()
                            chexist=self.c.execute('SELECT id from channels WHERE id=? ',[channeldisplayname])
                            chexist= chexist.fetchone()
                            
                            if not chexist:
                                self.c.execute('INSERT INTO channels(id,epgid,  alt_title, categories, logo, thumb, lang, source, channelsources) VALUES( ?, ?, ?, ?, ?, ?,?,?,?)', [channeldisplayname,epgid,  live_tv_name(channeldisplayname).replace(" ", ""), "", "", getlogofromfolder(channeldisplayname).split("\\")[-1], lang,self.source,json.dumps(channelsources)])  
                            else:
                                self.c.execute('UPDATE channels SET source = ? AND epgid = ? WHERE id= ?',[self.source,epgid,channeldisplayname]) 
                        self.pDialog.update( 50 ,"Finished adding %s channels" %str(len(channels)) )
                
            
            else:
                deg("No valid epgfile found. Read error")
 
    def epg_programes_todb(self):
                for channel, title, startDate, endDate, item, subTitle, imageLarge in self.process_epgxml():
                    if not title == "":
                        self.c.execute('INSERT INTO programs(channel, title, start_date, end_date, description, subTitle, image_large, source) VALUES(?, ?, ?, ?, ?, ?, ?,?)',
                                    [channel.capitalize(), title, startDate, endDate, json.dumps(item), subTitle, imageLarge,self.source])
                        #self.expire.append(int(item.get("start")))
                        self.expire.append(int(startDate))
                self.dbcon.commit()


    def startorstoptodatetime(self,input):
        return int(time.mktime(time.strptime(input, epgtimeformat)))          #else:
            #    xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,!!Not Valid XML file format!! ,3000,"")")
    def process_epgxml(self):
                                                    
                ALLROOTS = self.root.findall("./programme")
                total = len(ALLROOTS)
                #databasePath = os.path.join(profile, 'lsproepg.db')
                #dbcon = database.connect(databasePath)
                #c = dbcon.cursor()  
                for index,programme in  enumerate(ALLROOTS):
                    item={}
                    subTitle=desc=""
                    
                    channel = programme.get('channel').decode("utf-8","ignore") #clenname in here.(nospace,lower)
                    self.pDialog.update( 30 + int(total*0.8),"Finished adding %s " %str(channel)) 
                    item["start"] = startDate=startorstoptodatetime(programme.get('start')[:14])

                    endDate = startorstoptodatetime(programme.get('stop')[:14])
                    title = programme.find('title').text
                    if not programme.find('sub-title') is None:
                        subTitle=item["tag"] = programme.find('sub-title').text
                    if not programme.find('desc') is None:
                        item["plot"] = programme.find('desc').text
                    icon = programme.find('icon')
                    if not icon is None:
                        imageLarge = icon.attrib.get("src")
                    else:
                        imageLarge = ''
                    try:
                        item["genre"] = ",".join([i.text for i in programme.findall('category')])
                        #programme.find('category').text
                    except:
                        item["genre"] = "Lspro"
                        pass
                    try:
                        episodenum = programme.find('episode-num').text
                        #deg(episodenum)
                        if "." in episodenum:
                            epinum = episodenum.split(".") #0..
                            item["season"] = int(epinum[0])
                            item["episode"] = int(epinum[1].split("/")[0]) if len(epinum[1]) >0 else 0
        
                        elif "S" in episodenum:
                            item["season"] = int(re_me(episodenum,r"S.*?(\d{1,2})"))
                            item["episode"] = int(re_me(episodenum,r"E*?(\d{1,2})"))                         
                    except:
                        
                        pass
                    yield (channel, title, startDate, endDate, item, subTitle, imageLarge)
    def matchChannel(self,xmlname):
        
        xmlname = live_tv_name(xmlname).capitalize().strip()
        self.c.execute('SELECT epgid,source FROM channels WHERE id=? ',[xmlname] )

        _getnow = self.c.fetchone()
        if _getnow:
            self.channel = _getnow[0].capitalize()
            self.source = _getnow[1]
            if self.source:
                self.houroffset = int(self.source[:1])
            return _getnow[0]
                
        else:

            self.c.execute('SELECT epgid,source FROM channels WHERE id LIKE ? ', [xmlname[:3]+'%'] )

            _getnow = self.c.fetchall()
            _getchannels = [(index,str(i[0]),i[1]) for index,i in enumerate(_getnow)]
            k= df.get_close_matches(xmlname.replace(" ","").lower(),[i[1].replace(" ","").lower() for i in _getchannels],cutoff=0.6)
            #deg("kkkk for k:")
            #deg( str(k))
            if k:
                k = [index for index,i in enumerate(_getnow) if str(i[0]).replace(" ","").lower() == k[0]]
                #deg("k has become:")
                #deg(str(k))
                self.channel=_getchannels[k[0]][1].capitalize()
                #overwrite source to channel
                self.source =_getchannels[k[0]][2] 

                deg("EPG Channel match other way:xmlname:" + xmlname  +","  +self.channel)
                if self.source:
                    self.houroffset = int(self.source[:1])
                return self.channel
            else:
                #self.dbcon.close()
                return          

    def _getCurrentProgram(self,houroffset=0):
        self.CurrentProgramstart_date = int(time.time())+int(self.houroffset)*60*60 #forward for 10*60*60
        self.c.execute('SELECT * FROM programs WHERE channel= ? AND source=? AND start_date <= ? AND end_date >= ?', [self.channel, self.source, self.CurrentProgramstart_date, self.CurrentProgramstart_date])
        _getnow = self.c.fetchone()

        if _getnow:
            return _getnow
            #self.Programfailed += 1
            #if self.Programfailed == 9:
        self.updateurl.append(self.source)        
        #else:
        #    self.c.execute('SELECT start_date FROM programs WHERE channel= ? AND source=? ', [channel, self.source])
            
        
        return
    def _getNextProgram(self,end_date):

        self.c.execute('SELECT start_date, end_date,description FROM programs WHERE channel=? AND source=? AND start_date >= ? ORDER BY start_date ASC LIMIT 2', [self.channel, self.source, end_date])
        #deg("_getNextProgram getting" +channel +str( end_date))
        _getNextPrograms = self.c.fetchall()
        
        if len(_getNextPrograms) <= 1 :
            self.updateurl.append(self.source)
        
        #self.dbcon.close()
        #deg(str(_getNextPrograms))

        return _getNextPrograms 
    def getallepgsources(self):
        if not self.url == 'i' :
            self.c.execute('SELECT url FROM up_source WHERE url=? ', [self.url])
            return self.c.fetchone()
            
        self.c.execute('SELECT url FROM up_source ', [])
        return self.c.fetchall()
        
    def checknextprogames(self):
        if self.updateurl :
            #deg("self.updateurl")
            #deg(str(self.updateurl))
            self.updateurl = [ (x, self.updateurl.count(x)) for x in self.updateurl]
            #deg(str(self.updateurl))
            for source,number in set(self.updateurl):
                if number >= 9:
                    self.source = source
                    self.forceupdate = True
                    #deg("self.sourceself.sourceself.source::"+self.source)
                    self._update_xml()        
    def processepg_item_info(self,name,item_info):
        itemart={}
        CurrentProgram=item_info.get("CurrentProgram")
        if CurrentProgram:
            NextProgram =  item_info.get("NextProgram" )
            #divmod(abs(1500325267 -time.time()),(60*60))
            timeletfCurrentProgram = divmod(abs(CurrentProgram[3]  - int(self.CurrentProgramstart_date)),(60*60))
            if int(timeletfCurrentProgram[0]) >0:
                timeletfCurrentProgram = "%sh:%s Remaining:" %(str(int(timeletfCurrentProgram[0])),   str(int(timeletfCurrentProgram[1]/60)))
            else:
                timeletfCurrentProgram = "%smin. Remaining:" %(   str(int(timeletfCurrentProgram[1]/60)))
            #deg(name +str(CurrentProgram))
            item_info=json.loads(CurrentProgram[4])
            item_info["tvshowtitle"] = CurrentProgram[1]
            itemart['poster']=itemart['thumb']=CurrentProgram[6]
            
            thumbnail = getlogofromfolder(name.split('[')[0])
            if not thumbnail == icon:
                itemart['fanart'] = thumbnail
                #itemart['thumb'] = now_thumb        
            if NextProgram:
                NextProgram =[(datetime.datetime.fromtimestamp(float(i[0])).strftime("%H:%M"),json.loads(i[2])) for i in NextProgram]
                #deg(str(NextProgram))
                NextProgram = "\n====================\n".join( [ "[COLOR fuchsia]" +i[0] + " : [/COLOR] [COLOR plum]" +i[1].get("tvshowtitle", " ")+"[/COLOR]\n"+i[1].get("plot", " ") for i in NextProgram])
                #deg(NextProgram) blue_grey_900_ff263238
                item_info['plot'] =   timeletfCurrentProgram + "[COLOR lightcoral] " +item_info.get("plot", " ") +"[/COLOR]\n====================\n" +  NextProgram
                item_info["title"] = name + " [I][COLOR lemonchiffon]" +CurrentProgram[1]+"[/COLOR][/I]"
                item_info.setdefault("showcontext",{})["epgcontext"] = "epgcontext"

                #item_info["starttime"] = CurrentProgram[2]
                #item_info["endtime"] = CurrentProgram[3] 
                 
                #item_info["epgcontext"] = "true" 
            item_info.pop("start",None)
            item_info.pop("thumb",None)
        return itemart,item_info    
    def channelepg(self,name):
        
        item_info={}
        itemart={}
        epgname = self.matchChannel(name)
        if epgname:        
            CurrentProgram=item_info["CurrentProgram"]=self._getCurrentProgram() 
            if CurrentProgram:
                item_info["NextProgram"] = self._getNextProgram(CurrentProgram[3])
    
        if item_info.get("CurrentProgram"):

           itemart,item_info=self.processepg_item_info(name,item_info)  
        return itemart,item_info
    def onedayepg(self,name,url,houroffset=0):
        item_info={}
        itemart={}
        epgname = self.matchChannel(name)
        LOGO = getlogofromfolder(name)
        itemart["fanart"] = LOGO
        self.CurrentProgramstart_date = int(time.time())+ houroffset
        if epgname:        
            self.c.execute('SELECT title, start_date,description,image_large FROM programs WHERE channel=? AND source=? AND start_date >= ? AND end_date <= ? ORDER BY start_date', [self.channel, self.source, self.CurrentProgramstart_date,self.CurrentProgramstart_date + 24*60*60 ])
            #deg("_getNextProgram getting" +channel +str( end_date))
            _getNextPrograms = self.c.fetchall()
            seen= set()
            _getNextPrograms= [i for i in _getNextPrograms if i[0] not in seen and not seen.add(i[0])]
            for title, start_date,description,image_large in _getNextPrograms:
                #if start_date <= 
                HM = datetime.datetime.fromtimestamp(float(start_date)).strftime("%I:%M %p")
                item_info =  json.loads(description)
                title = "[I][COLOR grey]%s [/COLOR][/I] %s"  %(HM,title)
                itemart["thumb"] = image_large or LOGO
                addLink(url,title,itemart,item_info)
            #self.dbcon.close()
            #deg(str(_getNextPrograms))
            #return _getNextPrograms 
#def startorstoptodatetime(input):
#    return datetime.datetime(*(time.strptime(input, epgtimeformat)[0:6]))           
def startorstoptodatetime(input):
        return int(time.mktime(time.strptime(input, epgtimeformat)))
               
  
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


def __top_domain(url):           
        elements = urlparse.urlparse(url)
        domain = elements.netloc or elements.path
        domain = domain.split('@')[-1].split(':')[0]
        regex = "(\w{2,}\.\w{2,3}\.\w{2}|\w{2,}\.\w{2,3})$"
        res = re.search(regex, domain)
        if res:
            domain = res.group(1)
        domain = domain.lower()
        return domain
def notification(header="", message="", sleep=3000,icon=icon):
    """ Will display a notification dialog with the specified header and message,
    in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i,%s)" % ( header, message, sleep,icon ))
def ShowOSDnownext():
    path__ = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    try:
        path = dict(urlparse.parse_qsl(path__.split('?',1)[1]))
    except:
    #    deg("path Error")
    #    deg(str(urlparse.parse_qsl(path__.split('?',1))))
        pass
        return

    #deg([xbmc.getInfoLabel('Player.Duration'),xbmc.getInfoLabel('VideoPlayer.Plot'),xbmc.getInfoLabel('System.Time(format)'),xbmc.getInfoLabel('Player.Filename')]) #nothing works here.
    #deg([xbmc.getInfoLabel('ListItem.TVShowTitle'),xbmc.getInfoLabel('ListItem.Season'),xbmc.getInfoLabel('ListItem.Episode'),xbmc.getInfoLabel('ListItem.StartTime'),xbmc.getInfoLabel('ListItem.Label2')]) 

    plot = xbmc.getInfoLabel('ListItem.Plot')
    dur = xbmc.getInfoLabel('ListItem.Duration')
    progtimes = re.compile(r"\](\d{2}:\d{2})\[",re.DOTALL).findall(plot)
    if not progtimes:
        return
    icon = path.get("thumb","0")
    
    
    plots = plot.split("!!!\n")
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
google_search_res = os.path.join(profile, 'google_search_res')
def Search_onGoogle_result(url):
    #match = re.compile(r'''<a\s*href=['"](.*?)[""]>.*?</a>(.*?)$''',re.DOTALL | re.MULTILINE).findall(makeRequest(url))
    match = re.compile(r'''\s*href=['"]([^\?].*?)["']>.*?</a>(.*?)(?:tr>|\n)''',re.DOTALL | re.MULTILINE).findall(makeRequest(url))
    total = len(match)
    
    prem_pat = r'.*?(\d{2,4})-([A-Za-z]+)-(\d{2,4})'
    search = re.compile(prem_pat,re.DOTALL)
    if match:
        if match[-1][0].endswith(('.png','.jpg','.jpeg','.PNG')):
            link = '%s%s'%(url,match[-1][0])
            itemart['thumb'] = link
            itemart['fanart'] = link
            match.remove(match[-1])
        for count,(href,other) in enumerate(match):
            dir_ = False
            title = ' {0} [COLOR yellow]{1} [/COLOR]'
            if href.endswith('/') :
                if href == '../' or href.startswith('/'):
                    if '?' in href:
                        pep_url = url.split('://')
                        link = '%s%s%s%s' %(pep_url[0],'://',pep_url[1].split('/',1)[0],href)
                    else:
                        link= url.rsplit('/',2)[0] + '/'
                
                else:
                    link = '%s%s'%(url,href)
                dir_ = True                    
                
            elif href.endswith(('.mkv','.mp4','.avi','.flv')):
                if '?' in href:
                    pep_url = url.split('://')
                    link = '%s%s%s%s' %(pep_url[0],'://',pep_url[1].split('/',1)[0],href)
                else:
                    link = '%s%s'%(url,href)

            elif href.endswith(('.png','.jpg','.jpeg','.PNG')) :
                link = '%s%s'%(url,href)
                tle = urllib.unquote(href).replace('/',' ')
                itemart['thumb'] = link
                itemart['fanart'] = link
                addDirPlayable(tle, link, '1916',{},{},playslideshow='1')
            elif href.endswith(('.mp3','.m4a')):
                if '?' in href:
                    pep_url = url.split('://')
                    link = '%s%s%s%s' %(pep_url[0],'://',pep_url[1].split('/',1)[0],href)
                else:
                    link = '%s%s'%(url,href)
            
            else:
                continue
            try:
                if '</' in other:
                    item_info['plot'] = re.sub(r'<.*?>','\n',other)

                    #print re.compile(r'>(.*?)</').findall(other)
                else:
                    item_info['plot'] = other.replace(' ', '\n',1)
                premiered =search.findall(other)
                #xbmc.log("[addon.live.streamspro-%s]: %s" %('premiered', str(premiered)),xbmc.LOGNOTICE)
                #https://github.com/vonH/plugin.video.iplayerwww/blob/3c5e08e845cd756a9b17a66e45882fd82b90472e/resources/lib/ipwww_video.py#L181
                if premiered:
                    month = premiered[0][1]
                    monthDict={
                        'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
                        'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
                    if month in monthDict:
                        month = monthDict[month]
                    else:
                        month = '01'
                    if len(premiered[0][0]) == 4:
                        year = premiered[0][0]
                        item_info['premiered'] =  '%s-%s-%s' %(str(premiered[0][0]),month,str(premiered[0][2])) 
                    else:
                        item_info['premiered'] =  '%s-%s-%s' %(str(premiered[0][2]),month,str(premiered[0][0])) 
                else:
                    item_info['premiered'] = '1969-01-01'                    
            except:
                pass
            d_k = urlparse.urlsplit(link)
            try:

                if dir_:
                    tle = link.rsplit('/', 2)
                    xbmc.log('tle : %s ' %str(tle),xbmc.LOGNOTICE)
                    if tle[-1] == '':
                        title = title.format(urllib.unquote(tle[-2]).replace('/',' '),d_k.hostname)
                    else:
                        title = title.format(urllib.unquote(tle[-1]).replace('/',' '),d_k.hostname)
                
                #tle = urllib.unquote(href).replace('/',' ')
                else:
                    tle = urllib.unquote(link.rsplit('/', 1)[-1]).replace('/',' ')
                    tle=re.sub(r"(S\d{,2}\W?E\d{,2})",r'[COLOR cyan] \1 [/COLOR]',tle,1, re.IGNORECASE)
                        
                    if '720p' in tle:
                        title = title.format('[720] ',tle.replace('.720p.',''))
                    elif '1080p' in href:
                        title = title.format('[1080] ',tle.replace('.1080p.',''))
                    elif '480p' in href:
                        title = title.format('[480] ',tle.replace('.480p.',''))
                    else:
                        title = title.format('',tle)
            except Exception: 
                
                title = title.format('',d_k.hostname)
            
            #clean UP
            link = link.replace('&amp;','&')
            if '=' in title:
                title = '%s%s' %('[COLOR cyan] ',title.split('=')[-1])
            #clean UP
            if dir_:
                addDir(title,link,1915,itemart,item_info)
            else:
                addLink(link,title,itemart,item_info,None,total)
            
def update_livestreamer():
    import shutil
        
    addon2 = xbmcaddon.Addon('script.module.livestreamer')
    profile2 = xbmc.translatePath(addon2.getAddonInfo('profile').decode('utf-8'))
    if not os.path.isdir(profile2) :
        xbmcvfs.mkdir(profile2)
    version_file = os.path.join(profile2,'version.txt')

    url = 'https://codeload.github.com/streamlink/streamlink/zip/master'
    No_pycountry = 'https://www.dropbox.com/s/dih7kbaw5qsp1h3/l10n.py?dl=1'    
    filename=xbmc.translatePath('special://home/addons/packages/script.module.livestreamer.zip')
    get_version="https://pypi.python.org/pypi/streamlink/json"
    src = xbmc.translatePath('special://home/addons/packages/script.module.livestreamer/streamlink-master/src/streamlink/')
    dst = xbmc.translatePath('special://home/addons/script.module.livestreamer/lib/streamlink')
    new_=""
    if xbmcvfs.exists(version_file):
        old_ = open(version_file).read()
        new_ = json.loads(makeRequest(get_version))["info"].get("version")
        if old_ == new_:
            try:
                import streamlink
                return
            except:
                pass
           
            
        
    if not xbmcvfs.exists(filename):
        down_url(url,filename)
    contentfromZip(filename,_out=xbmc.translatePath('special://home/addons/packages/script.module.livestreamer/'))
    need_this_not_in_streamlink = xbmc.translatePath('special://home/addons/packages/backports_shutil.zip')
    down_url('https://codeload.github.com/minrk/backports.shutil_which/zip/master',need_this_not_in_streamlink)
    contentfromZip(need_this_not_in_streamlink,_out=xbmc.translatePath('special://home/addons/packages/script.module.livestreamer/'))

    if xbmc.getCondVisibility("System.HasAddon(script.module.livestreamer)"):
        if not os.path.isdir(dst) and os.path.isdir(xbmc.translatePath('special://home/addons/script.module.livestreamer/lib/livestreamer')):
           shutil.rmtree(xbmc.translatePath('special://home/addons/script.module.livestreamer/lib/livestreamer'),ignore_errors=True)
        else:
            shutil.rmtree(dst)    
    if os.path.isdir(src) :
        shutil.move(src,dst)
        shutil.move(xbmc.translatePath('special://home/addons/packages/script.module.livestreamer/backports.shutil_which-master/backports/'),dst)
    down_url(No_pycountry,xbmc.translatePath('special://home/addons/script.module.livestreamer/lib/streamlink/utils/l10n.py'),replacefile=True)
    if new_ == "":
        new_ = json.loads(makeRequest(get_version))["info"].get("version")
    with open(version_file,"w") as f:
        f.write(new_)
    shutil.rmtree(xbmc.translatePath('special://home/addons/packages/script.module.livestreamer/'),ignore_errors=True)      

def Search_onGoogle(search=None):
    #http://www.google.com/search?hl=en&q=preacher
    if not os.path.isdir(google_search_res):
        xbmcvfs.mkdir(google_search_res) 
      
    if search and search =="NewSearch":
        keyboard = xbmc.Keyboard('','Search the TV Show in google.com Index')
        keyboard.setDefault("+(mkv|avi|mpeg)")
        keyboard.doModal()
        if (keyboard.isConfirmed() == False):

            for item in os.listdir(google_search_res):
                addDir(item,os.path.join(google_search_res,item),1,itemart,item_info)
            return
        newStr = keyboard.getText()
        if len(newStr) == 0:
            return
        else:
            search = newStr
    else:
        addDir('[B]New Search[/B]',"NewSearch",1915,itemart,item_info)
        for item in os.listdir(google_search_res):
            addDir(item,os.path.join(google_search_res,item),1,itemart,item_info)
        return
    # import Google Search
    search = search.replace(' ', '.')
    #senitize_search = re.sub('\W+','_',search)
    nameoffile = os.path.join(google_search_res, re.sub('\W+','_',search))
    token_time_limit = time.time() - int(24*24*60*60) #19min
    if os.path.isfile(nameoffile):
        if os.stat(nameoffile).st_mtime < token_time_limit:
            xbmcvfs.delete(nameoffile)
    if os.path.isfile(nameoffile):
        parse_m3u(open(nameoffile).read())
    else:
        from xgoogle.search import GoogleSearch
        # search on google
        gs = GoogleSearch('?intitle:index.of? ' + search)
        gs.results_per_page = 50
        gs.page = 0
        # return result or None
        try:
            results = gs.get_results()
            #return results
        except Exception, e:
            xbmc.log("[addon.live.streamspro-%s]: %s" %('Search Unsuccessful', e),xbmc.LOGNOTICE)
        if results :
            makem3u = '''#EXTINF:-1 plot="%s"  type="addDirfr_gsearch" , %s  [COLOR yellow] %s [/COLOR]\n%s'''
            with open(nameoffile,'w') as f:
                f.write('#EXTM3U\n')
                #for res in results:
                kkk=    [makem3u %(title,urllib.unquote(d_k.path.split('/',2)[-1]).replace('/',' '),d_k.hostname,url) if d_k.path.split('/',2)[-1] != '' else makem3u %(title,d_k.hostname,d_k.hostname,url) for d_k,url,title in [(urlparse.urlsplit(res.url.encode('utf8','ignore')),res.url.encode('utf8','ignore'),res.title.encode('utf8','ignore')) for res in results if 'Index of' in res.title.encode('utf8','ignore')]]
                f.write('\n'.join(map(str,kkk)))                     

        else:
            print "No Results found"
            return
        parse_m3u(open(nameoffile).read())  

def movedown_zip(url,zipname,_out=xbmc.translatePath('special://home/addons/')):
    filename=xbmc.translatePath('special://home/addons/packages/%s.zip' %zipname)
    
    down_url(url,filename,replacefile=True)
    return contentfromZip(filename,_out) 
