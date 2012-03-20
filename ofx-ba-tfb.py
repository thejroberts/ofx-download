#!/usr/bin/python
from client import OFXClient
import getpass, json, sys, time

argv = sys.argv
join = str.join

if __name__=="__main__":
    try:
        with open("sites.json", "r") as f:
            sites = json.load(f)
    except IOError as e:
        print 'no "sites.json" file detected'

    dtstart = time.strftime("%Y%m%d",time.localtime(time.time()-31*86400))
    dtnow = time.strftime("%Y%m%d%H%M%S",time.localtime())
    if len(argv) < 3:
        print "Usage:",argv[0], "site user [account] [CHECKING/SAVINGS/.. if downloading from bank account]"
        print "available sites:",join(", ",sites.keys())
        sys.exit()
    passwd = getpass.getpass()
    client = OFXClient(sites[argv[1]], argv[2], passwd)
    if len(argv) < 4:
       query = client.acctQuery("19700101000000")
       client.doQuery(query, argv[1]+"_acct.ofx")
    else:
       if "CCSTMT" in sites[argv[1]]["caps"]:
          query = client.ccQuery(argv[3], dtstart)
       elif "INVSTMT" in sites[argv[1]]["caps"]:
          query = client.invstQuery(sites[argv[1]]["fiorg"], argv[3], dtstart, dtnow)
       elif "BASTMT" in sites[argv[1]]["caps"]:
          query = client.baQuery(sites[argv[1]]["bankid"], argv[3], dtstart, dtnow, argv[4])
       client.doQuery(query, argv[1]+dtnow+".ofx")
