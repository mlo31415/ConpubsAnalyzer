from __future__ import annotations
from typing import List

from ConSeries import ConSeriesPage
from FTP import FTP
from ConpubsCounts import ConpubsCounts, NameLinkCounts

from HelpersPackage import ExtractInvisibleTextInsideFanacComment, FindBracketedText2, FindLinkInString
from Log import LogOpen, Log


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

    # The main page is in V2 (or later) format
    version=ExtractInvisibleTextInsideFanacComment(file, "version")
    if version == "":
        version="2.0"

    listOfConSeries=DownloadMainConlist()
    listOfConSeries=[x for x in listOfConSeries if "Natcon" in x.name]# or "Capclave" in x .name]

    FTP().SetLogging(False)

    # Walk the list of ConSeries, loading each in turn
    cpc=ConpubsCounts()
    csplist: List[ConpubsCounts]=[]
    for csnl in listOfConSeries:
        csp=ConSeriesPage(csnl.name)
        counts=csp.Counts
        counts.title=csnl.name
        csplist.append(counts)
        cpc+=counts

    Log("\n\n")
    for csp in csplist:
        Log(f"{csp}")

    Log("\nGrand Total: "+cpc.Debug(), isError=True)


###############################################################################


# (Heavily) modified version of function of same name from ConEditor
def DownloadMainConlist() -> list[NameLinkCounts]:

    Log("Loading root/index.html")
    file=FTP().GetFileAsString("", "index.html")
    if file is None:
        return []

    table, rest=FindBracketedText2(file, "fanac-table", caseInsensitive=True)
    tbody, _=FindBracketedText2(table, "tbody", caseInsensitive=True)

    listOfConSeries=[]
    while True:
        tr, tbody=FindBracketedText2(tbody, "tr", caseInsensitive=True)
        if tr == "":
            break
        td, _=FindBracketedText2(tr, "td", caseInsensitive=True)
        if "----" in td:
            continue  # Skip over dividing lines
        _, link, text, _=FindLinkInString(td)
        listOfConSeries.append(NameLinkCounts(Name=text, URL=link))

    return listOfConSeries


#############################################
if __name__ == "__main__":
    main()
