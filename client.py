import time, httplib, urllib2, uuid

join = str.join

def _field(tag,value):
    return "<"+tag+">"+value

def _tag(tag,*contents):
    return join("\r\n",["<"+tag+">"]+list(contents)+["</"+tag+">"])

def _date():
    return time.strftime("%Y%m%d%H%M%S",time.localtime())

def _genuuid():
    return uuid.uuid4().hex

class OFXClient:
    """Encapsulate an ofx client, config is a dict containing configuration"""
    def __init__(self, config, user, password):
        self.password = password
        self.user = user
        self.config = config
        self.cookie = 3
        config["user"] = user
        config["password"] = password
        if "appid" not in config:
            config["appid"] = "QWIN"
            config["appver"] = "1800"

    def _cookie(self):
        self.cookie += 1
        return str(self.cookie)

    """Generate signon message"""
    def _signOn(self):
        config = self.config
        fidata = [ _field("ORG",config["fiorg"]) ]
        if "fid" in config:
            fidata += [ _field("FID",config["fid"]) ]
        return _tag("SIGNONMSGSRQV1",
                    _tag("SONRQ",
                         _field("DTCLIENT",_date()),
                         _field("USERID",config["user"]),
                         _field("USERPASS",config["password"]),
                         _field("LANGUAGE","ENG"),
                         _tag("FI", *fidata),
                         _field("APPID",config["appid"]),
                         _field("APPVER",config["appver"]),
                         ))

    def _acctreq(self, dtstart):
        req = _tag("ACCTINFORQ",_field("DTACCTUP",dtstart))
        return self._message("SIGNUP","ACCTINFO",req)

# this is from _ccreq below and reading page 176 of the latest OFX doc.
    def _bareq(self, bankid, acctid, dtstart, dtend, accttype):
        config=self.config
        req = _tag("STMTRQ",
                    _tag("BANKACCTFROM",
                        _field("BANKID",bankid),
                        _field("ACCTID",acctid),
                        _field("ACCTTYPE",accttype)),
                    _tag("INCTRAN",
                        _field("DTSTART",dtstart),
                        _field("DTEND",dtend),
                        _field("INCLUDE","Y")))
        return self._message("BANK","STMT",req)

    def _ccreq(self, acctid, dtstart):
        config=self.config
        req = _tag("CCSTMTRQ",
                    _tag("CCACCTFROM",
                        _field("ACCTID",acctid)),
                    _tag("INCTRAN",
                        _field("DTSTART",dtstart),
                        _field("INCLUDE","Y")))
        return self._message("CREDITCARD","CCSTMT",req)

    def _invstreq(self, brokerid, acctid, dtstart, dtend):
        req = _tag("INVSTMTRQ",
                    _tag("INVACCTFROM",
                        _field("BROKERID", brokerid),
                        _field("ACCTID",acctid)),
                    _tag("INCTRAN",
                        _field("DTSTART",dtstart),
                        _field("INCLUDE","Y")),
                    _field("INCOO","Y"),
                    _tag("INCPOS",
                        _field("DTASOF", dtend),
                        _field("INCLUDE","Y")),
                    _field("INCBAL","Y"))
        return self._message("INVSTMT","INVSTMT",req)

    def _message(self,msgType,trnType,request):
        config = self.config
        return _tag(msgType+"MSGSRQV1",
                    _tag(trnType+"TRNRQ",
                         _field("TRNUID",_genuuid()),
                         _field("CLTCOOKIE",self._cookie()),
                         request))

    def _header(self):
        return join("\r\n",[ "OFXHEADER:100",
                           "DATA:OFXSGML",
                           "VERSION:102",
                           "SECURITY:NONE",
                           "ENCODING:USASCII",
                           "CHARSET:1252",
                           "COMPRESSION:NONE",
                           "OLDFILEUID:NONE",
                           "NEWFILEUID:"+_genuuid(),
                           ""])

    def baQuery(self, bankid, acctid, dtstart, dtend, accttype):
        """Bank account statement request"""
        return join("\r\n",[self._header(),
                       _tag("OFX",
                                self._signOn(),
                                self._bareq(bankid, acctid, dtstart, dtend, accttype))])

    def ccQuery(self, acctid, dtstart):
        """CC Statement request"""
        return join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._ccreq(acctid, dtstart))])

    def acctQuery(self,dtstart):
        return join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._acctreq(dtstart))])

    def invstQuery(self, brokerid, acctid, dtstart, dtend):
        return join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._invstreq(brokerid, acctid, dtstart, dtend))])

    def doQuery(self,query,name):
        # N.B. urllib doesn't honor user Content-type, use urllib2
        garbage, path = urllib2.splittype(self.config["url"])
        host, selector = urllib2.splithost(path)
        h = httplib.HTTPSConnection(host)
        h.request('POST', selector, query,
                  { "Content-type": "application/x-ofx",
                    "Accept": "*/*, application/x-ofx"
                  })
        if 1:
            res = h.getresponse()
            response = res.read()
            res.close()

            with open(name,"w") as f:
                f.write(response)
        else:
            print self.config["url"]
            print query
