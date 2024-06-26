from __future__ import annotations
from typing import List
import json
import re

from Log import Log
from FTP import FTP
from HelpersPackage import RemoveAccents, FindBracketedText, FindBracketedText2, ExtractInvisibleTextInsideFanacComment, Float0
from ConpubsCounts import ConpubsCounts, NameLinkCounts
from ConInstance import ConInstance


####################################################################################
class Con:
    def __init__(self, seriesname: str):
        self._name: str=""                  # Name including number designation
        self._seriesname: str=seriesname
        self._URL: str=""                   # The URL of the individual con page, if any


    def FromJson(self, val: str) -> Con:
        d=json.loads(val)
        self._name=RemoveAccents(d["_name"])
        if "_URL" in d.keys():
            self._URL=d["_URL"]
        return self



####################################################################################
class ConSeries():
#    _element=Con

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
    def __init__(self, conseriesname: str):

        assert len(conseriesname) > 0
        self.Seriesname=conseriesname
        self.SeriesCons=ConSeries(conseriesname)
        self.Counts=ConpubsCounts()
        self.Counts.title=conseriesname

        Log(f"Loading /{self.Seriesname}/index.html from fanac.org")
        file=FTP().GetFileAsString("/"+self.Seriesname, "index.html")

        # Figure out what version this conseriespage is
        # V1.0 is the old json-based format (we have this format if there is a block of json in the file)
        # V2.0 (and potentially higher) is the new pure-HTML format

        # Try to get the JSON and the version from the file
        version=0   # If we find json, then for our purposes, this is a version 0 file. (There are versions in the json, but they are not the overall version)
        j=FindBracketedText(file, "fanac-json")[0]
        if j is None or len(j) < 20:
            version=Float0(ExtractInvisibleTextInsideFanacComment(file, "version"))     # Look for a version in the file
            if version == 0:
                version=1       # If this is not a version 0 file and no version is found in it, it's version 1
        Log(f"{conseriesname}: {version=}")

        # Extract the list of con instances
        # Version 0 files store data entirely differently from version 1 and above, so we handle them differently here
        listOfNLCs: list[NameLinkCounts]=[]
        if version < 0.99:
            try:
                self.FromJson(j)
            except (json.decoder.JSONDecodeError):
                Log(f"DownloadConSeries: JSONDecodeError when loading convention information from /{self.Seriesname}index.html")
                return

            # Extract the info we need
            for coninstance in self.SeriesCons._series:
                listOfNLCs.append(NameLinkCounts(Name=coninstance._name, URL=coninstance._URL))

        else:
            # Interpret the HTML
            listOfNLCs=self.LoadConSeriesFromHTML(file)

        Log(f"{len(listOfNLCs)} instances found")

        # Process the con instances getting a count for each and sum them up
        numcons=0
        for nlc in listOfNLCs:
            if nlc.URL != "":   # No URL is a con that is in the list, but with no data yet
                # Load the con instance from the server and compute its counts
                ci=ConInstance("/"+self.Seriesname, nlc.name)
                numcons+=1
                self.Counts+=ci.ComputeCounts

        self.Counts.numcons=numcons
        self.Counts.numseries=1     # We just finished a series


    def FromJson(self, val: str) -> ConSeriesPage:                    # MainConSeriesFrame
        d=json.loads(val)
        if d["ver"] >= 3:
            self.Seriesname=RemoveAccents(d["_textConSeries"])
            #self.TextFancyURL=RemoveAccents(d["_textFancyURL"])
            #self.TextComments=d["_textComments"]
            self.SeriesCons=ConSeries(self.Seriesname).FromJson(d["_datasource"])
        return self

    #----------------------------
    # Populate the ConSeriesFrame structure
    def LoadConSeriesFromHTML(self, file: str) -> List[NameLinkCounts]:
        # Look for the series name in the header
        head, rest=FindBracketedText2(file, "head", caseInsensitive=True)

        # There should only be one table and that contains the list of con instances
        table, _=FindBracketedText2(rest, "fanac-table", caseInsensitive=True)
        if table == "":
            Log(f"DecodeConSeriesHTML(): failed to find the <fanac-table> tags")
            return []

        # Read the table
        # Get the table header and decode the columns
        header, rest=FindBracketedText2(table, "thead", caseInsensitive=True)
        if header == "":
            Log(f"DecodeConSeriesHTML(): failed to find the <thead> tags in the body")
            return []
        # Find the column headings
        headers=self.ReadTableRow(header, "th")

        # Now read the rows
        rows=[]
        while True:
            rowtext, rest=FindBracketedText2(rest, "tr", caseInsensitive=True)
            if rowtext == "":
                break
            row=self.ReadTableRow(rowtext)
            if len(row) < len(headers):
                row.extend(" "*(len(headers)-len(row)))
            rows.append(row)

        cons: List[NameLinkCounts]=[]
        for row in rows:
            name=""
            URL=""
            cpc=ConpubsCounts()
            for icol, header in enumerate(headers):
                match header:
                    case "Convention":
                        name, URL, _ = self.ConNameInfoUnpack(row[icol])

            cons.append(NameLinkCounts(Name=name, URL=URL))

        return cons


    #----------------------------------------------------------------------
    # Read a row from an HTML table and output a list of cell contents
    # The input is normally the text bounded by <tr>...</tr>
    # The cells are all the strings delimited by <delim>...</delim>
    def ReadTableRow(self, row: str, delim="td") -> list[str]:
        rest=row
        out=[]
        while True:
            item, rest=FindBracketedText2(rest, delim, caseInsensitive=True)
            if item == "":
                break
            if f"<{delim}>" in item:    # This corrects for an error in which we have the pattern '<td>xxx<td>yyy</td>' which displays perfectly well
                item=item.split(f"<{delim}>")
                out.extend(item)
            else:
                out.append(item)

        return out


    #---------------------
    # Unpack a conpubs conname from a con instance convention column  which may include a url, the url's text (a name), and some extra material
    # header is of the form <a href=xxxx>yyyy</a>zzzz
    # Generate the Name, URL and extra columns
    # Reversed by ConNameInfoPack()
    def ConNameInfoUnpack(self, packed: str) -> (str, str, str):
        name=packed
        url=""
        extra=""

        m=re.match('<a href=\"?(.*?)\"?>(.*?)</a>(.*)$', packed, re.IGNORECASE)
        if m is not None:
            url=m.groups()[0].strip()
            name=m.groups()[1].strip()
            extra=m.groups()[2].strip()

        return name, url, extra
