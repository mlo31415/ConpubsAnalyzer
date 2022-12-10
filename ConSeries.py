from __future__ import annotations
from typing import Optional, List, Union, Tuple
import json

from Log import Log
from FTP import FTP
from HelpersPackage import RemoveAccents, FindBracketedText
from ConpubsCounts import ConpubsCounts
from ConInstance import ConInstanceClass


####################################################################################
class Con:
    def __init__(self, seriesname: str):
        self._name: str=""                  # Name including number designation
        self._seriesname: str=seriesname
        self._URL: str=""                   # The URL of the individual con page, if any


    def FromJson(self, val: str) -> Con:
        d=json.loads(val)
        self._name=RemoveAccents(d["_name"])
        # self._locale=d["_locale"]
        # self._gohs=d["_gohs"]
        # self._dates=FanzineDateRange().Match(d["_dates"])
        if "_URL" in d.keys():
            self._URL=d["_URL"]
        # else:
        #     self._URL=""
        return self

    def Counts(self) -> ConpubsCounts:
        Log("Con.Counts("+self._seriesname+"/"+self._name+")")
        cidc=ConInstanceClass(self._seriesname, self._name)
        cpc=ConpubsCounts()
        for row in cidc.Datasource._conFileList:        # Walk the list of files in a con instance, counting each in turn
            if row._sitefilename is not None and len(row._sitefilename) > 0:
                cpc+=row.Counts()       # Increment the ConInstance the counts by adding the counts of one ConInstanceFile

        cpc.numcons=1

        return cpc



####################################################################################
class ConSeries():
    _element=Con

    def __init__(self, seriesname: str):
        self._name: str=""
        self._seriesname: str=seriesname
        self._series: List[Con]=[]
        self._stuff: str=""


    def FromJson(self, val: str) -> ConSeries:
        d=json.loads(val)
        self._name=RemoveAccents(d["_name"])      # Clean out old accented entries
        if "_stuff" in d.keys():
            self._stuff=d["_stuff"]
        self._series=[]
        i=0
        while str(i) in d.keys():       # This is because json merges 1 and "1" as the same. (It appears to be a bug.)
            self._series.append(Con(self._seriesname).FromJson(d[str(i)]))
            i+=1

        return self


#####################################################################################
# This holds a con series index page
class ConSeriesPage():

    def __init__(self, conseriesname):

        assert len(conseriesname) > 0
        self.Seriesname=conseriesname
        self.Datasource=ConSeries(conseriesname)

        Log("Loading "+"/"+self.Seriesname+"/index.html from fanac.org")
        file=FTP().GetFileAsString("/"+self.Seriesname, "index.html")

        # Get the JSON from the file
        j=FindBracketedText(file, "fanac-json")[0]
        if j is None or j == "":
            Log("DownloadConSeries: Can't load convention information from /"+self.Seriesname+"index.html")
            return

        try:
            self.FromJson(j)
        except (json.decoder.JSONDecodeError):
            Log("DownloadConSeries: JSONDecodeError when loading convention information from /"+self.Seriesname+"index.html")
            return

        Log(self.Seriesname+" Loaded")


    def FromJson(self, val: str) -> ConSeriesPage:                    # MainConSeriesFrame
        d=json.loads(val)
        if d["ver"] >= 3:
            self.Seriesname=RemoveAccents(d["_textConSeries"])
            #self.TextFancyURL=RemoveAccents(d["_textFancyURL"])
            #self.TextComments=d["_textComments"]
            self.Datasource=ConSeries(self.Seriesname).FromJson(d["_datasource"])
        return self

    # Get the counts for a ConSeries by summing the counts of each ConInstance in the series
    def Counts(self) -> ConpubsCounts:
        Log("ConSeriesFrame.Counts("+self.Seriesname+")")
        cpc=ConpubsCounts()
        cpc.numseries=1
        for con in self.Datasource._series: # Walk the list of con instances opening and counting each in turn
            if con._URL is not None and len(con._URL) > 0:
                cpc+=con.Counts()
        return cpc