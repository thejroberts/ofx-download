#!/usr/bin/python
from client import OFXClient
import json, sys, time, os

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
    if len(argv) < 4:
        print "Usage:",argv[0], "site user password [account1,[account2,[account3...]]] [CHECKING/SAVINGS/.. if downloading from bank account]"
        print "available sites:",join(", ",sites.keys())
        sys.exit()
    passwd = argv[3]
    client = OFXClient(sites[argv[1]], argv[2], passwd)

    if len(argv) < 5:
        query = client.acctQuery("19700101000000")
        client.doQuery(query, argv[1]+"_acct.ofx")
    else:
        if "CCSTMT" in sites[argv[1]]["caps"]:
            query = client.ccQuery(argv[4].split(","), dtstart)
        elif "INVSTMT" in sites[argv[1]]["caps"]:
            query = client.invstQuery(sites[argv[1]]["fiorg"], argv[4].split(","), dtstart, dtnow)
        elif "BASTMT" in sites[argv[1]]["caps"]:
            query = client.baQuery(sites[argv[1]]["bankid"], argv[4].split(","), dtstart, dtnow, argv[5])
        client.doQuery(query, argv[1]+dtnow+".ofx")

    os.startfile("\"" + os.getcwd() + "\\" + outfile + "\"")
