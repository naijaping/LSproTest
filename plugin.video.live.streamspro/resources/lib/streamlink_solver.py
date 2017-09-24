
import xbmc
#try:
#    import livestreamer
#    xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Please install streamlink.Search Google - ,10000)")
#except:
#    import streamlink    
import streamlink    
s=streamlink.Streamlink()

def GetLivestreamerLink(url):

    try:
        get_streams = s.streams(url)
        stream = get_streams["best"]
        if not get_streams:
            xbmc.log("No streams found on URL '{0}'".format(url),xbmc.LOGNOTICE)
            return
    except Exception:
        return
    final_url = ''
    if isinstance(stream, streamlink.stream.hls.HLSStream):
        return stream.url
    elif isinstance(stream, streamlink.stream.RTMPStream):
        #xbmc.log('RTMP Trouble ahead for kodi 17' + url)
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
