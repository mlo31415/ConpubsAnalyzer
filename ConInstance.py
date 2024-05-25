from __future__ import annotations
from typing import List

import json
import re

from Log import Log, LogError
from FTP import FTP
from ConpubsCounts import ConpubsCounts
from HelpersPackage import FindBracketedText, Float0, Int0, ExtractInvisibleTextInsideFanacComment, FindBracketedText2
from HelpersPackage import FindNextBracketedText, FindLinkInString

from ConFileData import ConFileData, ConInstanceLine


#####################################################################################################
# A ConInstancePage is needed to read json data
# It gets turned into a ConInstance, which is the structure holding all the relevant parts of a ConInstance


class ConInstancePage:
    def __init__(self):
        self._conPageFileList: List[ConInstanceLine]=[]


    def FromJson(self, val: str) -> ConInstancePage:
        d=json.loads(val)
        if d["ver"] >= 1:
            #self._name=d["_name"]
            cfld=d["_conFileList"]
            self._conPageFileList=[]
            for c in cfld:
                cil=ConInstanceLine().FromJson(c)
                cp=ConFileData(CIL=cil)
                self._conPageFileList.append(cp)

        return self


#####################################################################################
class ConInstance:

    def __init__(self, seriesname, coninstancename):
        self._listConFiles: list[ConFileData]=[]
        self._coninstancename=coninstancename
        self._seriesname=seriesname

        Log(f"CIC.__init__: Loading /{seriesname}/{coninstancename}/index.html")

        # Read the existing CIP
        file=FTP().GetFileAsString(f"/{seriesname}/{self._coninstancename}", "index.html")
        if file is None:
            Log(f"CI.__init__: Download ConInstance Page: /{seriesname}/{self._coninstancename}/index.html does not exist")
            return  # Just return with the ConInstance page empty

        version=0
        j=FindBracketedText(file, "fanac-json")[0]
        if j is None or len(j) < 20:
            version=2
        else:
            version=Float0(ExtractInvisibleTextInsideFanacComment(file, "version"))

        Log(f"{coninstancename} -- {version}")

        if version < 1.99:
            # Load it from json
            try:
                self.FromJson(j)
            except (json.decoder.JSONDecodeError):
                LogError(f"CI.__init__: JSONDecodeError when loading convention information from /{coninstancename}index.html")
                return

            # Extract the info we need
            self._listConFiles=[ConFileData(CIL=x) for x in self.CIP._conPageFileList]

        else:
            # Interpret the HTML
            if not self.LoadConInstanceFromHTML(file):
                LogError(f"CI.__init__: LoadConInstanceFromHTML() failed when loading convention information from /{coninstancename}index.html")
                return

        Log(f"CIC: /{seriesname}/{self._coninstancename}/index.html downloaded")


    # ----------------------------------------------
    @property
    def ComputeCounts(self) -> ConpubsCounts:
        counts=ConpubsCounts()
        for cf in self._listConFiles:
            if not cf.IsTextRow and not cf.IsEmptyRow:
                counts+=cf.Counts
        Log(f"{self._coninstancename} = {counts}")
        return counts


    # ----------------------------------------------
    def FromJson(self, val: str) -> ConInstance:
        d=json.loads(val)
        try:
            self.ConInstanceName=d["ConInstanceName"]
        except:
            LogError(f"ConInstanceClass.FronJson of {self._coninstancename} failed to find member 'ConInstanceName'")

        self.CIP=ConInstancePage().FromJson(d["_datasource"])
        return self


    def LoadConInstanceFromHTML(self, file: str) -> bool:

        file=file.replace("/n", "")  # I don't know where these are coming from, but they don't belong there!

        body, _=FindBracketedText2(file, "body", caseInsensitive=True)
        if body is None:
            LogError("LoadConInstanceFromHTML(): Can't find <body> tag")
            return False

        rows: list[tuple[str, str]]=[]
        ulists, _=FindBracketedText2(body, "fanac-table", caseInsensitive=True)

        # The ulists are a series of ulist items, each ulist is a series of <li></li> items
        # The tags usually have ' id="conpagetable"' which can be ignored
        remainder=ulists.replace(' id="conpagetable"', "")
        while True:
            lead, tag, contents, remainder=FindNextBracketedText(remainder)
            if tag == "":
                break
            Log(f"*** {tag=}  {contents=}")
            if tag == "ul":
                remainder=lead+contents+remainder  # If we encounter a <ul>...</ul> tag, we edit it out, keeping what's outside it and what's inside it
                continue
            rows.append((tag, contents))

        # Now decode the lines
        for row in rows:
            if row[0] == "li":
                Log(f"\n{row[1]=}")
                conf=ConFileData()
                # We're looking for an <a></a> followed by <small>/</small>
                a, rest=FindBracketedText2(row[1], "a", includeBrackets=True)
                Log(f"{a=}   {rest=}")
                if a == "":
                    LogError(f"LoadConInstanceFromHTML(): Can't find <a> tag in {row}")
                    return False
                _, href, text, _=FindLinkInString(a)
                if href == "":
                    LogError(f"LoadConInstanceFromHTML(): Can't find href= in <a> tag in {row}")
                    return False
                # if href is a foreign link, then this is a link line
                if "/" in href:
                    conf.DisplayTitle=text
                    conf.SiteFilename=href
                    conf.IsLinkRow=True
                    self._listConFiles.append(conf)
                    continue

                # Strip any view-Fit specs from the end of the URL.  There may be more than one.
                # They may be of the form
                #       #view=Fit
                #       #xxx=yyy&view-Fit
                # Strategy is to first remove all view=Fit&, then any #view=Fit
                while "view=fit" in href.lower():
                    href=re.sub("view=fit&", "", href, count=99, flags=re.IGNORECASE)
                    href=re.sub("#view=fit", "", href, count=1, flags=re.IGNORECASE)

                # It appears to be an ordinary file like
                conf.DisplayTitle=text
                conf.SiteFilename=href

                if len(rest.strip()) > 0:
                    small, _=FindBracketedText2(rest, "small")
                    if small == "":
                        LogError(f"LoadConInstanceFromHTML(): Can't find <small> tag in {rest}")
                        return False
                    small=small.replace("&nbsp;", " ")
                    m=re.match(".*?([0-9.]+) MB", small, re.IGNORECASE)
                    if m is not None:
                        val=Float0(m.group(1))
                        if val > 500:  # We're looking for a value in MB, but if we get a value in bytes, convert it
                            val=val/(1024**2)
                        conf.Size=val
                    m=re.match(".*?([0-9]+) pp", small, re.IGNORECASE)
                    if m is not None:
                        conf.Pages=Int0(m.group(1))

                self._listConFiles.append(conf)

            elif row[0] == "b":
                conf=ConFileData()
                conf.IsTextRow=True
                conf.DisplayTitle=row[1]
                #self._listConFiles.append(conf)
                Log(f"LoadConInstanceFromHTML(): Text line: {conf.DisplayTitle}")

        return True


