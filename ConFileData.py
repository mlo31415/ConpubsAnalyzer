import os
import json

from Log import Log
from HelpersPackage import Float0, Int0, RemoveAccents
from ConpubsCounts import ConpubsCounts


# An individual file to be listed under a convention
# This is a version 0 format which is now used just to retrieve data from embedded json
# Once retrieved, we move the data to a ConFileData class
class ConInstanceLine:
    def __init__(self):
        self.SiteFilename: str=""      # The name to be used for this file on the website
        self.Size: int=0               # The file's size in bytes
        self.IsTextRow: bool=False        # Is this a piece of text rather than a convention?
        self.IsLinkRow: bool=False        # Is this a link?
        self._URL: str=""               # The URL to be used for a link. (This is ignored if _isLink == False.) It will be displayed using displayTitle as the link text.
        self.Pages: int|None=None      # Page count


    def FromJson(self, val: str):
        d=json.loads(val)
        self.DisplayTitle=d["_displayTitle"]
        self.Notes=d["_notes"]
        val=Float0(d["_size"])
        if val > 500:  # We're looking for a value in MB, but if we get a value in bytes, convert it
            val=val/(1024**2)
        self.Size=val
        if d["ver"] > 4:
            self.SiteFilename=d["_sitefilename"]
        if d["ver"] <= 4 or self.SiteFilename.strip() == "":
            self.SiteFilename=self.DisplayTitle
        if d["ver"] > 5:
            self.IsTextRow=d["_isText"]
        if d["ver"] > 6:
            self.Pages=d["_pages"]
        if d["ver"] > 7:
            self.IsLinkRow=d["_isLink"]
        if d["ver"] > 8:
            self._URL=d["_URL"]
        return self



###################################################################
# An individual file to be listed under a convention
# This is a single row
class ConFileData:
    def __init__(self, CIL: ConInstanceLine=None):
        self.DisplayTitle: str=""      # The name as shown to the world on the website
        self.Notes: str=""             # The free-format description
        self._localfilename: str=""     # The filename of the source file
        self._localpathname: str="."    # The local pathname of the source file (path+filename)
        self.SiteFilename: str=""      # The name to be used for this file on the website (It will be (part of) the URL and holds the URL for link rows.)
        self.Size: int=0               # The file's size in bytes
        self.IsTextRow: bool=False        # Is this a piece of text rather than a convention?
        self.IsLinkRow: bool=False        # Is this a link?
        self.Pages: int=0              # Page count

        if CIL is not None:
            self.DisplayTitle=CIL.DisplayTitle
            self.SiteFilename=CIL.SiteFilename
            self.Size=CIL.Size
            self.IsTextRow=CIL.IsTextRow
            self.IsLinkRow=CIL.IsLinkRow
            self.Pages=CIL.Pages



    def __str__(self):
        s=""
        if len(self.SiteFilename) > 0:
            s+="Sitename="+self.SiteFilename+"; "
        if len(self.DisplayTitle) > 0:
            s+="Display="+self.DisplayTitle+"; "
        if len(self.Notes) > 0:
            s+="Notes="+self.Notes+"; "
        if Float0(self.Size) > 0:
            s+="Size="+str(self.Size)+"; "
        if Int0(self.Pages) > 0:
            s+="Pages="+str(self.Pages)+"; "
        if self.IsTextRow:
            s+="IsTextRow; "
        if self.IsLinkRow:
            s+="IsLinkRow; "

        return s

    @property
    def Counts(self) -> ConpubsCounts:
        Log(f"ConInstanceFile.Counts({self.SiteFilename})")
        cpc=ConpubsCounts()
        _, ext = os.path.splitext(self.SiteFilename.lower())

        if ext == ".pdf":
            cpc.numpdfs=1
        if ext in [".jpeg", ".jpg", ".gif", ".png"]:
            cpc.numimages=1
        if self.IsLinkRow:
            cpc.numlinks=1

        if self.Pages is not None:
            cpc.numpages=self.Pages

        return cpc


    @property
    def IsEmptyRow(self) -> bool:
        return self.SiteFilename == "" and self.DisplayTitle == "" and Int0(self.Pages) == 0 and self.Notes != ""
