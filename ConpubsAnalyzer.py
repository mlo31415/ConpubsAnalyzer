from __future__ import annotations
from typing import List

import json

from ConSeries import ConSeriesPage
from FTP import FTP
from ConpubsCounts import ConpubsCounts

from HelpersPackage import FindBracketedText
from Log import LogOpen, Log


class Convention:
    def __init__(self):
        self.name: str=""      # The name of the convention series


    def FromJson(self, val: str) -> Convention:
        dx=json.loads(val)
        self.name=dx["_name"]

        return self


class ConList:
    Element=Convention

    def __init__(self):
        self.conlist: List[Convention]=[]

    # -----------------------------
    def FromJson(self, val: str) -> ConList:
        dx=json.loads(val)
        self.conlist=[]
        i=0
        while str(i) in dx.keys():       # Using str(i) is because json merges 1 and "1" as the same. (It appears to be a bug.)
            self.conlist.append(Convention().FromJson(dx[str(i)]))
            i+=1
        return self


###############################################################################
###############################################################################


def main():
    LogOpen("Log -- ConpubsAnalyzer.txt", "Log (Errors) -- ConpubsAnalyzer.txt")

    f=FTP()
    if not f.OpenConnection("FTP Credentials.json"):
        Log("Main: OpenConnection('FTP Credentials.json' failed")
        exit(0)

    Log("Loading root/index.html")
    file=FTP().GetFileAsString("", "index.html")
    if file is None:
        assert False

    # Get the JSON
    j=FindBracketedText(file, "fanac-json")[0]
    if j is None or j == "":
        Log("Can't find convention information json in conpubs' index.html")
        exit(0)

    listOfConSeries=[]
    try:
        d=json.loads(j)
        listOfConSeries=ConList().FromJson(d["_datasource"])
    except json.decoder.JSONDecodeError:
        Log("JSONDecodeError when loading convention information from conpubs' index.html")
        exit(0)

    # Walk the list of ConSeries, loading each in turn
    cpc=ConpubsCounts()
    csplist: List[ConpubsCounts]=[]
    for row in listOfConSeries.conlist:
        csp=ConSeriesPage(row.name)
        counts=csp.Counts()
        counts.title=row.name
        csplist.append(counts)
        cpc+=counts

    Log("\n\n")
    for csp in csplist:
        Log(str(csp))

    Log(str(cpc))
    Log("\nGrand Total: "+cpc.Debug(), isError=True)


if __name__ == "__main__":
    main()
