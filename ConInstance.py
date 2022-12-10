from __future__ import annotations
from typing import List, Union, Optional

import os
import json
from Log import Log
from FTP import FTP
from ConpubsCounts import ConpubsCounts
from HelpersPackage import FindBracketedText, RemoveHTTP


# An individual file to be listed under a convention
class ConInstanceFile:
    def __init__(self):
        self._sitefilename: str=""      # The name to be used for this file on the website
        self._size: int=0               # The file's size in bytes
        self._isText: bool=False        # Is this a piece of text rather than a convention?
        self._isLink: bool=False        # Is this a link?
        self._URL: str=""               # The URL to be used for a link. (This is ignored if _isLink == False.) It will be displayed using displayTitle as the link text.
        self._pages: Optional[int]=None # Page count


    def FromJson(self, val: str) -> ConInstanceFile:
        d=json.loads(val)
        self._displayTitle=d["_displayTitle"]
        self._notes=d["_notes"]
        #self._localpathname=d["_localpathname"]
        #self._localfilename=d["_filename"]
        self._size=d["_size"]
        if d["ver"] > 4:
            self._sitefilename=d["_sitefilename"]
        if d["ver"] <= 4 or self._sitefilename.strip() == "":
            self._sitefilename=self._displayTitle
        if d["ver"] > 5:
            self._isText=d["_isText"]
        if d["ver"] > 6:
            self._pages=d["_pages"]
        if d["ver"] > 7:
            self._isLink=d["_isLink"]
        if d["ver"] > 8:
            self._URL=d["_URL"]
        return self

    def Counts(self) -> ConpubsCounts:
        Log("ConInstanceFile.Counts("+self._sitefilename+")")
        cpc=ConpubsCounts()
        _, ext = os.path.splitext(self._sitefilename.lower())

        if ext == ".pdf":
            cpc.numpdfs=1
        if ext in [".jpeg", ".jpg", ".gif", ".png"]:
            cpc.numimages=1
        if self._isLink:
            cpc.numlinks=1

        if self._pages is not None:
            cpc.numpages=self._pages

        return cpc



#####################################################################################################

class ConInstancePage():
    Element=ConInstanceFile

    def __init__(self):
        self._conFileList: List[ConInstanceFile]=[]

    def FromJson(self, val: str) -> ConInstancePage:
        d=json.loads(val)
        if d["ver"] >= 1:
            #self._name=d["_name"]
            cfld=d["_conFileList"]
            self._conFileList=[]
            for c in cfld:
                self._conFileList.append(ConInstanceFile().FromJson(c))

        return self


#####################################################################################
class ConInstanceClass():

    def __init__(self, seriesname, coninstancename):

        self.Datasource=ConInstancePage()

        self._coninstancename=coninstancename

        # Read the existing CIP
        Log("Downloading /"+seriesname+"/"+self._coninstancename+"/index.html")
        file=FTP().GetFileAsString("/"+seriesname+"/"+self._coninstancename, "index.html")
        if file is None:
            Log("DownloadConInstancePage: /"+seriesname+"/"+self._coninstancename+"/index.html does not exist")
            return  # Just return with the ConInstance page empty

        # Get the JSON
        j=FindBracketedText(file, "fanac-json")[0]
        if j is not None and j != "":
            self.FromJson(j)

        Log("/"+seriesname+"/"+self._coninstancename+"/index.html downloaded")

    # ----------------------------------------------
    def FromJson(self, val: str) -> ConInstanceClass:
        d=json.loads(val)
        try:
            self.ConInstanceName=d["ConInstanceName"]
        except:
            LogError(f"ConInstanceClass.FronJson of {self._coninstancename} failed to find member 'ConInstanceName'")
        #self.ConInstanceTopText=d["ConInstanceStuff"]
        #self.ConInstanceFancyURL=d["ConInstanceFancyURL"]
        #if d["ver"] > 3:
        #    self.Credits=d["Credits"]
        #self.ConInstanceFancyURL=RemoveHTTP(self.ConInstanceFancyURL)
        self.Datasource=ConInstancePage().FromJson(d["_datasource"])
        return self

