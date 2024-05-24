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
        self._sitefilename: str=""      # The name to be used for this file on the website
        self._size: int=0               # The file's size in bytes
        self._isText: bool=False        # Is this a piece of text rather than a convention?
        self._isLink: bool=False        # Is this a link?
        self._URL: str=""               # The URL to be used for a link. (This is ignored if _isLink == False.) It will be displayed using displayTitle as the link text.
        self._pages: int|None=None      # Page count


    def FromJson(self, val: str):
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

    @property
    def Counts(self) -> ConpubsCounts:
        Log(f"ConInstanceFile.Counts({self._sitefilename})")
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

###################################################################
# An individual file to be listed under a convention
# This is a single row
class ConFileData:
    def __init__(self, CIL: ConInstanceLine=None):
        self._displayTitle: str=""      # The name as shown to the world on the website
        self._notes: str=""             # The free-format description
        self._localfilename: str=""     # The filename of the source file
        self._localpathname: str="."    # The local pathname of the source file (path+filename)
        self._sitefilename: str=""      # The name to be used for this file on the website (It will be (part of) the URL and holds the URL for link rows.)
        self._size: int=0               # The file's size in bytes
        self._isText: bool=False        # Is this a piece of text rather than a convention?
        self._isLink: bool=False        # Is this a link?
        self._pages: int=0              # Page count

        if CIL is not None:
            self._displayTitle=CIL._displayTitle
            self._sitefilename=CIL._sitefilename
            self._size=CIL._size
            self._isText=CIL._isText
            self._isLink=CIL._isLink
            self._pages=CIL._pages



    def __str__(self):
        s=""
        if len(self.SourceFilename) > 0:
            s+="Source="+self.SourceFilename+"; "
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
        Log(f"ConInstanceFile.Counts({self._sitefilename})")
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

    # Make a deep copy of a ConFileData
    def Copy(self):
        cf=ConFileData()
        cf._displayTitle=self._displayTitle
        cf._notes=self._notes
        cf._localfilename=self._localfilename
        cf._localpathname=self._localpathname
        cf._sitefilename=self._sitefilename
        cf._size=self._size
        cf._isText=self._isText
        cf._isLink=self._isLink
        cf._pages=self._pages
        return cf

    def Signature(self) -> int:
        tot=hash(self._displayTitle.strip()+self._notes.strip()+self._localfilename.strip()+self._localpathname.strip()+self._sitefilename.strip())
        return tot+hash(self._size)+hash(self._isText)+Int0(self.Pages)


    @property
    def DisplayTitle(self) -> str:
        return self._displayTitle
    @DisplayTitle.setter
    def DisplayTitle(self, val: str) -> None:
        self._displayTitle=val

    @property
    def Notes(self) -> str:
        return self._notes
    @Notes.setter
    def Notes(self, val: str) -> None:
        self._notes=val

    @property
    def SourcePathname(self) -> str:
        return self._localpathname
    @SourcePathname.setter
    def SourcePathname(self, val: str) -> None:
        self._localpathname=val
        self._localfilename=os.path.basename(val)


    @property
    def SourceFilename(self) -> str:
        return self._localfilename
    @SourceFilename.setter
    def SourceFilename(self, val: str) -> None:
        self._localfilename=val
        self._localpathname="invalidated"

    # When a line is a text line, it stores the text in DisplayTitle.  This is just an alias to make the code a bit more comprehensible.
    @property
    def TextLineText(self) -> str:
        return self.DisplayTitle
    @TextLineText.setter
    def TextLineText(self, val: str) -> None:
        self.DisplayTitle=val


    @property
    def SiteFilename(self) -> str:
        return self._sitefilename
    @SiteFilename.setter
    def SiteFilename(self, val: str) -> None:
        self._sitefilename=RemoveAccents(val)


    # Size is in MB
    @property
    def Size(self) -> float:
        return self._size
    @Size.setter
    def Size(self, val: int|float|str) -> None:
        if isinstance(val, str):
            val=Float0(val)
        if val > 500:  # We're looking for a value in MB, but if we get a value in bytess, convert it
            val=val/(1024**2)
        self._size=val

    @property
    def Pages(self) -> int:
        if self._pages is None:
            return 0
        return self._pages
    @Pages.setter
    def Pages(self, val: int|str) -> None:
        if type(val) is str:
            val=Int0(val)
        self._pages=val

    @property
    def IsTextRow(self) -> bool:
        return self._isText
    @IsTextRow.setter
    def IsTextRow(self, val: bool) -> None:
        self._isText=val

    @property
    def IsLinkRow(self) -> bool:
        return self._isLink
    @IsLinkRow.setter
    def IsLinkRow(self, val: bool) -> None:
        self._isLink=val


    # Get or set a value by name or column number in the grid
    def __getitem__(self, index: int|slice) -> str|int|float:
        # (Could use return eval("self."+name))
        if index == 0:
            return self.DisplayTitle
        if index == 1:
            return self.SourceFilename
        if index == 2:
            return self.SiteFilename
        if index == 3:
            if self.Pages == 0:
                return ""
            return self.Pages
        if index == 4:
            return f"{self.Size:.1f}"
        if index == 5:
            return self.Notes
        return "Val can't interpret '"+str(index)+"'"

    def __setitem__(self, index: int|slice, value: str) -> None:
        # (Could use return eval("self."+name))
        if index == 0:
            self.DisplayTitle=value
            return
        if index == 1:
            self.SourceFilename=value
            return
        if index == 2:
            self.SiteFilename=value
            return
        if index == 3:
            if isinstance(value, int):
                self.Pages=value
            else:
                self.Pages=Int0(value.strip())
            return
        if index == 4:
            self.Size=Float0(value)
            return
        if index == 5:
            self.Notes=value
            return
        print("SetVal can't interpret '"+str(index)+"'")
        raise KeyError


    @property
    def IsEmptyRow(self) -> bool:
        return self.SourceFilename == "" and self.SiteFilename == "" and self.DisplayTitle == "" and Int0(self.Pages) == 0 and self.Notes != ""
