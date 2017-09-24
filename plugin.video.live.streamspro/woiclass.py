
#whatsonindia epg dont fit with NA schedule   
class WOI():
    def __init__(self,url):
        self.source= cacheKey(url)
        self.url = url
        self.channel = ''
        try:
            from sqlite3 import dbapi2 as database
        except:
            from pysqlite2 import dbapi2 as database
        self.now = datetime.datetime.now().replace(microsecond=0)
        self.fromdatetime= self.now.strftime(epgtimeformat)[:12] 
        self.todatetime= (self.now + datetime.timedelta(days=4)).strftime(epgtimeformat)[:12]
        self.channeldisplayname=""
        self.databasePath = os.path.join(profile, 'lsproepg.db')
        self.dbcon = database.connect(self.databasePath)
        self.c = self.dbcon.cursor()  
    #  
        #dbcur.execute('ALTER TABLE programs ADD COLUMN source')
        self.c.execute('CREATE TABLE IF NOT EXISTS channels(id TEXT, channeldisplayname TEXT, alt_title TEXT,categories TEXT, logo TEXT,image_small TEXT, lang TEXT,expire_at TEXT, source TEXT, PRIMARY KEY (id))')
        self.c.execute('CREATE TABLE IF NOT EXISTS programs(channel TEXT, title TEXT, start_date TIMESTAMP, end_date TIMESTAMP, description TEXT, subTitle TEXT, image_large TEXT, expire_at TEXT,source TEXT)') 
        self.c.execute('CREATE TABLE IF NOT EXISTS up_source(source_id TEXT, title TEXT, url TEXT,start_date TIMESTAMP, PRIMARY KEY (source_id))') 
        
        self._update_xml()
        #self.c.execute('DELETE FROM channels ', )
        #self.c.execute('DELETE FROM programs ', )
        

        #channelexist = self.c.fetchone()
        
        #if channelexist is None:
        #    self.getsource_woi()
    def matchChannel(self,xmlname):
        #deg("matching channel name: " + xmlname)
        self.c.execute('SELECT id FROM channels WHERE id=? ',[xmlname] )

        _getnow = self.c.fetchone()
        if _getnow:
            #print "exact match found"
            return _getnow[0]
        else:

            self.c.execute('SELECT id FROM channels WHERE id LIKE ? ', [xmlname[:1]+'%'] )

            _getnow = self.c.fetchall()
            _getchannels = [(index,str(i[0])) for index,i in enumerate(_getnow)]
            #print _getchannels
            k= df.get_close_matches(xmlname.replace(" ","").lower(),[i[1].replace(" ","").lower() for i in _getchannels],cutoff=0.6)
            #deg( str(k))
            if k:
                k = [index for index,i in enumerate(_getnow) if str(i[0]).replace(" ","").lower() == k[0]]
            
                channel=_getchannels[k[0]][1]
                #deg("EPG Channel match to:" + channel)
                return channel
            else:
                #self.dbcon.close()
                return          
        #CurrentProgram=self._getCurrentProgram(channel)
        #if not CurrentProgram:
        #    self.getsource_woi(channel)
        #CurrentProgram=self._getCurrentProgram(channel)
        #deg(str(CurrentProgram))
        #NextProgram = self._getNextProgram(channel,CurrentProgram[3])
        #NextProgram=NextProgram.append(CurrentProgram)
        #deg(str(NextProgram))
        
        #self.dbcon.close()    
        
        #return CurrentProgram
    def _update_xml(self):
        up_source=self.c.execute('SELECT * FROM up_source WHERE source_id=?',[self.source]) 
        up_source = up_source.fetchone()
        #deg(self.url + str(up_source))
        if up_source:
            url = up_source[2]
            
        else:
            #if url.startswith("http"):
                epgxml=  getepgcontent(self.url,replacefile=True)
                
                
                self.get_channels_db(epgxml)
                self.c.execute('INSERT INTO up_source(source_id,title,url,start_date) VALUES(?,?,?,?) ',[self.source,self.url.split("/")[-1],self.url,datetime.datetime.fromtimestamp(float(time.time())).strftime(epgtimeformat)[:10]]) 

        #up_source=self.c.execute('SELECT * FROM up_source WHERE source_id=?)',[source_id]) 
                self.dbcon.commit()        
    def get_channels_db(self,channel=''):
        #channellist="9X%20Jalwa,9XM,Aakash%20Aath,And%20Pictures,And%20TV,B4U%20Movies,B4U%20Music,Balle%20Balle,BIG%20MAGIC,Bindass,Bindass%20Play,Colors,Colors%20Bangla,Dabangg%20TV,Dhoom%20Music,Dillagi,E24,Enterr%2010,Filmy,Firangi,Jalsha%20Movies,Khushboo%20TV,Life%20OK,Magic%20of%20Cinema,Manoranjan%20TV,Mastiii,Movie%20House,Movies%20OK,MTunes,Music%20Fatafati,Music%20India,Music%20Xpress,Rishtey,Rishtey%20Cineplex,RT%20Movies,SAB,Sahara%20One,Sangeet%20Bangla,SET,Sony%20AATH,SONY%20MAX,SONY%20MAX%202,SONY%20MIX,SONY%20PAL,Star%20Gold,Star%20Jalsha,STAR%20PLUS,Star%20Utsav,Tara%20Muzik,The%20EPIC%20Channel,UTV%20Action,UTV%20Movies,Z%20ETC%20Bollywood,Zee%20Action,Zee%20Bangla,Zee%20Bangla%20Cinema,Zee%20Cinema,Zee%20Classic,Zee%20TV,Zindagi,ZING,Zoom,Star%20Sports%201,Star%20Sports%202,SONY%20SIX"
        
        #dump for test purpose
        #data = makeRequest(url) # timeout error
        #chdata =open(os.path.join(profile,"whatsonindia_data.json")).read()
            #f.write(json.dumps(data))
        match = json.loads(makeRequest(self.url))
        #print match.get("Schedule")["channel"]  #.get("channel").get("display-name")
        chdata = match["ScheduleGrid"]["channel"]  #[0].get("display-name")       #["display-name"]
        for ch in chdata:
            self.channeldisplayname = ch.get("display-name")
            self.chid = cleanname(ch.get("-id"),removecolorcode=True)
            self.channelgenre = ch.get("channelgenre")
            self.channellogourl = ch.get("channellogourl") #channelgenre=Hindi Entertainment
            self.c.execute('INSERT OR IGNORE INTO channels(id, channeldisplayname, alt_title, categories, logo, image_small, lang, expire_at, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?,?)',
                                        [self.chid, self.channeldisplayname, live_tv_name(self.channeldisplayname).replace(" ", ""), self.channelgenre, '', self.channellogourl, self.channelgenre.split(" ")[0], self.todatetime,self.source])             
            ch_programs =  ch['programme']
            deg( len(ch_programs)    )
            if ch_programs:
                self.epg_programes_todb(ch_programs)
    #def _tochanneltable(self):
    #    self.c.execute('INSERT INTO channels(id, channeldisplayname, alt_title, categories, logo, image_small,lang, expire_at, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?,?)',
    #                                [self.channel, title, live_tv_name(self.channeldisplayname), endDate, desc, subTitle, imageLarge, self.todatetime,self.source])        
    #
    def startorstoptodatetime(self,input):
        return int(time.mktime(time.strptime(input, epgtimeformat)))

    def epg_programes_todb(self,ch_programs)  :
        item_info={}
        for i in ch_programs:
            startDate = self.startorstoptodatetime(i.get("start"))
            endDate = self.startorstoptodatetime(i.get("stop"))
            item_info['plot'] = i.get("desc")
            imageLarge = i.get("programmeurl")
            if "video.zipazap.com" in imageLarge:
            #http://video.zipazap.com/promofile1/88FDE8E4EE5DBEF8FC3402BB1ABE72D96EE4DE41E.jpg
                imageLarge ="http://images.whatsonindia.com/dasimages/landscape/880x660/" + imageLarge.split('/')[-1]
                #imageLarge =imageLarge.replace("http://video.zipazap.com/promofile1/ProgrammeOfficialPoster/","http://images.whatsonindia.com/dasimages/landscape/880x660/")
            item_info["episode"] = i.get("episode-num",0)
            item_info['tag']=subTitle = i.get("sub-title")
            item_info['duration'] = str(int(i.get("duration",22))*60) #duration=225
            item_info["tvshowtitle"]=title = i.get("title")
            #programmescore=0.361909

            item_info['genre'] = i.get("genre", " ") + i.get("subgenre"," ")+ i.get("languagename"," ")
            credits = i.get("credits")
            if credits:
                item_info['director'] = credits.get("director")[0]
                item_info['cast'] = credits.get("actor")
            self.c.execute('INSERT INTO programs(channel, title, start_date, end_date, description, subTitle, image_large, expire_at, source) VALUES(?, ?, ?, ?, ?, ?, ?, ?,?)',
                                    [self.chid, title, startDate, endDate, json.dumps(item_info), subTitle, imageLarge, self.todatetime,self.source])
        self.dbcon.commit()
    def _getCurrentProgram(self,channel):
        """
    
        @param channel:
        @type channel: source.Channel
        @return:
        """
        now = int(time.time())+ (10*60*60) #forward for 10*60*60
        deg(str(now))
        
        program = None
        self.c.execute('SELECT * FROM programs WHERE channel= ? AND source=? AND start_date <= ? AND end_date >= ?', [channel, self.source, now, now])
        
        _getnow = self.c.fetchone()
        if _getnow:
            return _getnow
        
        return
    def _getNextProgram(self,channel,end_date):
        
        #end_date = _getnow[3]
        #print end_date
        self.c.execute('SELECT start_date, end_date,description FROM programs WHERE channel=? AND source=? AND start_date >= ? ORDER BY start_date ASC LIMIT 4', [channel, self.source, end_date])
        #deg("_getNextProgram getting" +channel +str( end_date))
        _getNextPrograms = self.c.fetchall()
        #self.dbcon.close()
        #deg(str(_getNextPrograms))
        return _getNextPrograms