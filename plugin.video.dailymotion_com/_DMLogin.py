import urllib
import urllib2
import xbmcvfs
import os,xbmc,xbmcaddon,xbmcgui,re,xbmcplugin,sys
import json
import datetime
addon = xbmcaddon.Addon('plugin.video.live.streamspro')
profile = xbmc.translatePath(addon.getAddonInfo('profile').decode('utf-8'))
cacheDir = os.path.join(profile, 'cachedir')
headers=dict({"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-GB,en;q=0.5","Accept-Encoding": "gzip, deflate, br","X-Requested-With" :"XMLHttpRequest","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Referer": "http://www.dailymotion.com/ca-en"})
U
P
import requests
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
def _login():
    if Doridro_USER == '' :
        return
    

    if checkfile(saved_cookie_file,timeforfileinsec=24*2*3600):
            with open( cookie_jar, "rb") as f:
                cookiess = pickle.load(f)
    else:
        session = requests.Session()
        rawbody = "form_name=dm_pageitem_authenticationform&_csrf={0}&_fid=&username={1}&authChoice=login&password={2}&from_request=%2Fsignin"
        r=session.get("http://www.dailymotion.com/signin",headers=headers)
        _csrf = re.compile(r'(?<=<input).+?id="_csrf".+?value="([^"]+)',re.DOTALL).findall(r.text)
        if _csrf:
            body = rawbody.format(_csrf,urllib.quote_plus(U),P)
        r = session.post(login_url,data = body,headers=headers)

        Cookie =  session.cookies.get_dict()      #str(r.headers['set-cookie'])
        #print r.cookies
        if re.search(r'Welcome back',r.text,re.I):
            notification('Login Succes','Succesfully loged_in to dailymotion.Com as %s ::.'%Doridro_USER,2000)
            #return r.cookies
            pickle.dump( Cookie, open( cookie_jar, "wb" ) )
           
def make_requests():
    response = [None]
    responseText = None

    if(signin_request_dailymotion_com(response)):
        responseText = read_response(response[0])

        response[0].close()
        _csrf = re.compile(r'(?<=<input).+?id="_csrf".+?value="([^"]+)',re.DOTALL).findall(responseText)
        #if _csrf:
        #    if request_www_dailymotion_com(response,_csrf,U,P):
                #abandonnnnn

def read_response(response):
    if response.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(response.read())
        return gzip.GzipFile(fileobj=buf).read()

    elif response.info().get('Content-Encoding') == 'deflate':
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)
        inflated = decompress.decompress(response.read())
        inflated += decompress.flush()
        return inflated

    return response.read()

def signin_request_dailymotion_com(response):
    response[0] = None

    try:
        req = urllib2.Request("http://www.dailymotion.com/signin")

        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0")

        response[0] = urllib2.urlopen(req)

    except urllib2.URLError, e:
        if not hasattr(e, "code"):
            return False
        response[0] = e
    except:
        return False

    return True
def request_www_dailymotion_com(response,_csrf,U,P):
    response[0] = None

    try:
        req = urllib2.Request("http://www.dailymotion.com/ajax/user")

        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0")
        req.add_header("Accept", "*/*")
        req.add_header("Accept-Language", "en-US,en;q=0.5")
        req.add_header("Accept-Encoding", "gzip, deflate")
        req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        req.add_header("X-Requested-With", "XMLHttpRequest")
        req.add_header("Referer", "http://www.dailymotion.com/ca-en")
        req.add_header("Connection", "keep-alive")

        body = "form_name=dm_pageitem_authenticationform&_csrf=0b_CZNV5eJ262qfvdKTXxcRK7dLMAGH4xlUDLlJZCLU&_fid=&username=kabilhabil99%40gmail.com&authChoice=login&password=22qazxsw&from_request=%2Fsignin"



        response[0] = urllib2.urlopen(req, body)

    except urllib2.URLError, e:
        if not hasattr(e, "code"):
            return False
        response[0] = e
    except:
        return False

    return True