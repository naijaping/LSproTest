from collections import OrderedDict,Counter
import datetime
#from datetime import datetime, timedelta

from _lspro import *
def deg(string,level=xbmc.LOGNOTICE):
        try:
            xbmc.log("[LSPRO::]: %s" %str(string),level)
        except:
            traceback.print_exc()
            pass
epgtimeformat2 = "%Y-%m-%d %H:%M:%S"
epgtimeformat = "%Y%m%d%H%M%S"

GUIDE={}
now = datetime.datetime.now().replace(microsecond=0)
import xml.etree.ElementTree
import pyfscache
LS_CACHE_getepgcontent = pyfscache.FSCache(xbmc.translatePath("special://temp/"),hours=10)
LS_CACHE_epginfo = pyfscache.FSCache(xbmc.translatePath("special://temp/"),minutes=25)


def starttimeofchannel(n):
    if  (startorstoptodatetime(sorted(GUIDE[n].keys(),reverse=True)[0])- datetime.timedelta(seconds=60*30))< now :
        return "1"
    return "0"
def cleanname(title):
    if title == None: return "UNKNOWN"
    title = re.sub('&#(\d+);', '', title)
    title = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
    title = title.replace('&quot;', '\"').replace('&amp;', '&')
    title = re.sub('\s', '', title.strip()).lower()

    
    
    return title

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
    epglink= epg.get('tvgurl')
    deg(epglink)
    url=epglink
    if epglink:
        epgfile = epg.get('epgfile','0')
        houroffset = epg.get('tvgshift') or 0
        updateafterhour = epg.get('updateafterhour','24')
        deg(epgfile) 
        nowstr = now.strftime(epgtimeformat)
        #nowstrplus14h =  now + datetime.timedelta(hours=14)
        #regvalidfor = nowstrplus14h.strftime(format)
        
        filedata = ''
        if not xbmcvfs.exists(LivewebTVepg):
            xbmcvfs.mkdir(LivewebTVepg)
        # check whether zip or xml file        
        if not epgfile == "0":
            filename = os.path.join(LivewebTVepg,cacheKey(url))
            extracted_dir = os.path.join(LivewebTVepg,cacheKey(url)+'_extracted')#dir
            #addon_log("[addon.live.streamspro-%s]: %s" %('No extracted_dir found ', str(extracted_dir)),xbmc.LOGNOTICE)            
       
            epgxml = os.path.join(extracted_dir,epgfile)
            epgfilewithreg = os.path.join(extracted_dir,cacheKey(epgxml)+'.json')
      
                        
        else:
            #xbmc.log("[addon.live.streamspro-%s]: %s" %(' Nofilefromzip ', str(filefromzip)),xbmc.LOGNOTICE)
            epgfilewithreg = os.path.join(LivewebTVepg,cacheKey(url)+'.json')
            if "\\" in url:
                epgxml = url
            else:
                epgxml = os.path.join(LivewebTVepg,cacheKey(url))
            
        deg("making regfile "+ str(epgfilewithreg))
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
        return epg_source_toregfile(epgxml,epgtimeformat,nowstr,epgfilewithreg)

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
def epg_source_toregfile(epgxml,epgtimeformat,nowstr,epgfilewithreg):
    epgfile = open(epgxml,"rb").read()
    if epgfile != None:
        try:
            root = xml.etree.ElementTree.fromstring(epgfile)
        except:
            root = None
        if root is not None:
            for programme in root.findall("./programme"):
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
                    category = programme.find('category').text
                except:
                    category = "Lspro"
                    pass
                try:
                    episodenum = programme.find('episode-num').text
                except:
                    episodenum = '0'
                    pass

                item = {"episodenum": episodenum,"genre":category,'start': start, 'stop': stop, 'title': title,"subtitle":subtitle,"plot":desc}
                GUIDE.setdefault(channel, {})[start] = item
            GUIDE["FileKEY"] = epgfilewithreg
            with open(epgfilewithreg,"w") as f:
                f.write(json.dumps(GUIDE))
            os.remove(epgxml)
            return epgfilewithreg

        else:
            xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,!!Warning Bad Regex::No Epg found!! ,3000,"+icon+")")
    
    return None

           
def startorstoptodatetime(input):
    return datetime.datetime(*(time.strptime(input, epgtimeformat)[0:6]))           
def down_url(url,filename,_out=None):
    #if addon.getSetting('download_path') == '':
    #        addon.openSettings()
    get_file_name = url.split('/')[-1]
    #if not filename:
        
    #    filename = os.path.join(addon.getSetting('download_path').encode('utf-8'),get_file_name)
    pDialog = xbmcgui.DialogProgress()
    #pDialog = xbmcgui.DialogProgressBG()
    pDialog.create('Downloading ......', 'File to download: %s ...' %get_file_name)
    size = 0
    block_sz = 8192
    headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0'}
    req = urllib2.Request(url,None,headers)
    song = urllib2.urlopen(req)
    meta = song.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    with open(filename, 'wb') as f:

        #mime_type = 'compressed/zip'
        while True:
            buffer = song.read(block_sz)
            if not buffer or pDialog.iscanceled():
                break

            size += len(buffer) 
            f.write(buffer)
            
            pDialog.update(int(size * 100. / file_size),'[COLOR yellow]{0}%[/COLOR]  Done...\n{1}'.format(str(int(size * 100. / file_size)),filename.rsplit('\\',1)[0]))
    xbmc.sleep(3) #change from 10 to 0.5
    if open(filename).read(1024).startswith('\x50\x4b\x03\x04'):
            import zipfile
        #try:
            zfile = zipfile.ZipFile(filename, 'r')
            zfile.extractall(path=_out)
            os.remove(filename)

    elif open(filename).read(1024).startswith('\x1f\x8b\x08'):
            import gzip
        #try:
            zfile = gzip.open(filename, 'rb')
            content= zfile.read()
            zfile.close()
            with open(filename,"wb") as f:
                f.write(content)
    
            #xbmcvfs.delete(filename)
        #except Exception, e:
        #        print str(e)
    #magic_dict = {
    #"\x1f\x8b\x08": "gz",
    #"\x42\x5a\x68": "bz2",
    #"\x50\x4b\x03\x04": "zip"
    #}
    #data = zlib.decompress(data, zlib.MAX_WBITS + 16)
    #f.write(data)
    #f.close()    
    
    pDialog.close()
                
@LS_CACHE_epginfo                
def epginfo(channel,epgdictfile,onedayEPG=False):                            
    summary = ''
    itemart={}
    item_info ={}
    hh= [i for i in GUIDE[channel].values() if  startorstoptodatetime(i['start']) <= now + datetime.timedelta(hours = 4) and startorstoptodatetime(i['stop']) > now ]
    #deg(hh)
    items_list = sorted(hh, key= lambda d: int(d["start"]))
    #deg(items_list)
    #items_list = GUIDE[channel].values()
    #print items_list
    for index,item in enumerate(items_list):
        start = startorstoptodatetime(item['start'])
      
        if index == 0:
            #try:
            #python 2.7 only
            item_info['duration'] = int((startorstoptodatetime(item['stop'])-start).total_seconds())
            summary ='\n[COLOR yellow]' + start.strftime('%H:%M') + ' [/COLOR][COLOR cyan][B]' + item['title']+ ":" +item['subtitle'] + '\n' + item['plot'] + "[/B][/COLOR]"
            continue
        summary = summary + '\n[COLOR skyblue]' + start.strftime('%H:%M') + ' ' + item['title']+ "[/COLOR]:" +item['subtitle'] + '\n' + item['plot']
    item_info['plot'] = summary
    
    return itemart,item_info

    
def lspro_Epg(soup):
    deg("convert xml to dict")
    global GUIDE
    E=  list(set(soup("epg")+soup("itemepg")))
    F = soup("item") + soup("epgitem")

    total = len(F)    
    names = [(index,cleanname(i.title.text.decode('utf-8'))) for index,i in enumerate(F)]
    #deg(names)
    
    for index,E_con in enumerate(E):
        epgdictfile= getepgcontent(E_con)
        GUIDE = json.loads(open(epgdictfile).read())
        deg("Readin file%s : %s" %(epgdictfile,str(index)))
        epgnames=[]
        guidekeys = GUIDE.keys()
        EE=[(starttimeofchannel(name[1]),epgnames.append(name),names.remove(name)) for name in sorted(names,reverse=True)  if  name[1] in guidekeys]
        failcount= Counter(elem[0] for elem in EE).get("1") or 0
        if epgnames and int(failcount*100/len(epgnames)) > 45:
            deg("EPG File update necessary")
            #deg(epgnames)
            deg(failcount)
            
            epgdictfile= getepgcontent(E_con,getnew=True)
            
        #deg(GUIDE.keys())
   
        itemsartinfo =  [(epgitemcount,epginfo(name,epgdictfile)) for epgitemcount,name in epgnames]
        #deg(itemsartinfo)
        
        [getItems(F[epgitemcount],FANART,epgiteminfo[0],epgiteminfo[1],total=total) for epgitemcount,epgiteminfo in itemsartinfo]
        #names = [(epgitemcount,epginfo(name,epgdictfile)) for epgitemcount,name in epgnames]
    
        GUIDE={}
        
    if len(names) > 0:
        [getItems(F[epgitemcount],FANART) for epgitemcount,i in names ]
    