import time, httplib, urllib2, uuid

join = str.join

def _field(tag,value):
    return "<"+tag+">"+value

def _tag(tag,*contents):
    return join("\r\n",["<"+tag+">"]+list(contents)+["</"+tag+">"])

def _message(msgType,*trans):
    return _tag(msgType+"MSGSRQV1", *trans)

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
        return _message("SIGNUP",self._transaction("ACCTINFO",req))

    def _bareq(self, bankid, acctids, dtstart, dtend, accttype):
        trans = [self._transaction("STMT",
                        _tag("STMTRQ",
                            _tag("BANKACCTFROM",
                                _field("BANKID",bankid),
                                _field("ACCTID",acctid),
                                _field("ACCTTYPE",accttype)),
                            _tag("INCTRAN",
                                _field("DTSTART",dtstart),
                                _field("DTEND",dtend), # required for MS Money
                                _field("INCLUDE","Y"))))
                        for acctid in acctids]
        return _message("BANK",*trans)

    def _ccreq(self, acctids, dtstart):
        trans = [self._transaction("CCSTMT",
                        _tag("CCSTMTRQ",
                            _tag("CCACCTFROM",
                                _field("ACCTID",acctid)),
                            _tag("INCTRAN",
                                _field("DTSTART",dtstart),
                                _field("INCLUDE","Y"))))
                        for acctid in acctids]
        return _message("CREDITCARD",*trans)

    def _invstreq(self, brokerid, acctid, dtstart, dtend):
        trans = [self._transaction("INVSTMT",
                        _tag("INVSTMTRQ",
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
                            _field("INCBAL","Y")))
                        for acctid in acctids]
        return _message("INVSTMT",*trans)

    def _transaction(self,trnType,request):
        return _tag(trnType+"TRNRQ",
                         _field("TRNUID",_genuuid()),
                         _field("CLTCOOKIE",self._cookie()),
                         request)

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

    def baQuery(self, bankid, acctids, dtstart, dtend, accttype):
        """Bank account statement request"""
        return join("\r\n",[self._header(),
                       _tag("OFX",
                                self._signOn(),
                                self._bareq(bankid, acctids, dtstart, dtend, accttype))])

    def ccQuery(self, acctids, dtstart):
        """CC Statement request"""
        return join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._ccreq(acctids, dtstart))])

    def acctQuery(self,dtstart):
        return join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._acctreq(dtstart))])

    def invstQuery(self, brokerid, acctids, dtstart, dtend):
        return join("\r\n",[self._header(),
                          _tag("OFX",
                               self._signOn(),
                               self._invstreq(brokerid, acctids, dtstart, dtend))])

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
