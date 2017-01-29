import sys,traceback,urllib2,re, urllib,xbmc
def createCookie(url,cj=None,agent='Mozilla/5.0 (Windows NT 6.1; rv:32.0) Gecko/20100101 Firefox/32.0',sendcfcookie=False):
    urlData=''
    try:
        import urlparse,cookielib,urllib2

        class NoRedirection(urllib2.HTTPErrorProcessor):    
            def http_response(self, request, response):
                return response

        def parseJSString(s):
            try:
                offset=1 if s[0]=='+' else 0
                val = int(eval(s.replace('!+[]','1').replace('!![]','1').replace('[]','0').replace('(','str(')[offset:]))
                return val
            except:
                pass

        #agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        if cj==None:
            cj = cookielib.CookieJar()
        
        opener = urllib2.build_opener(NoRedirection, urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-Agent', agent)]
        response = opener.open(url)
        result=urlData = response.read()
        response.close()
#        print result
#        print response.headers
        jschl = re.compile('name="jschl_vc" value="(.+?)"/>').findall(result)
   
        init = re.compile('setTimeout\(function\(\){\s*.*?.*:(.*?)};').findall(result)[0]
        builder = re.compile(r"challenge-form\'\);\s*(.*)a.v").findall(result)[0]
        decryptVal = parseJSString(init)
        lines = builder.split(';')

        for line in lines:
            if len(line)>0 and '=' in line:
                sections=line.split('=')

                line_val = parseJSString(sections[1])
                decryptVal = int(eval(str(decryptVal)+sections[0][-1]+str(line_val)))

#        print urlparse.urlparse(url).netloc
        answer = decryptVal + len(urlparse.urlparse(url).netloc)

        u='/'.join(url.split('/')[:-1])  
        if '<form id="challenge-form" action="/cdn' in urlData:
            u='/'.join(url.split('/')[:3])
        query = urlparse.urljoin(url,'/cdn-cgi/l/chk_jschl?jschl_vc=%s&jschl_answer=%s' % ( jschl, answer))
        passval=None
        if 'type="hidden" name="pass"' in result:
            passval=re.compile('name="pass" value="(.*?)"').findall(result)[0]
            query = '%s/cdn-cgi/l/chk_jschl?pass=%s&jschl_vc=%s&jschl_answer=%s' % (u,urllib.quote_plus(passval), jschl, answer)
            xbmc.sleep(4*1000) ##sleep so that the call work

        response = opener.open(query)
        print list(cj)
        cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in list(cj)])
       
        print cookie
        response.close()


    except:
        traceback.print_exc(file=sys.stdout)
        cookie = '; '.join(['%s=%s' % (i.name, i.value) for i in list(cj)])
    if sendcfcookie:
        return (agent,cookie,urlData)
    else:
        return urldata
#url = 'http://www.ecanlitvizle.net/al-jazeera-tv-izle/3/'
#agent,cookie,urlData = createCookie(url,sendcfcookie=True)
#print g[0] 
#print g[1]
#print g[2

