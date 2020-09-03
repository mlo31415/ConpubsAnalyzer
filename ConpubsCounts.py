from __future__ import annotations

class ConpubsCounts():

    def __init__(self):
        self.title: str=""      # We can add a title to a cpc.  Note that it does not copy or add, though it is not destroyed by something being added to it
        self.numpdfs: int=0     # Number of PDFs
        self.numpages: int=0    # Number of pages in all kinds of file
        self.numimages: int=0   # Number of jog/png/gif, etc
        self.numcons: int=0     # Number of conventions
        self.numseries: int=0   # Number of convention series
        self.numlinks: int=0    # Number of external links

    def __add__(self, other: ConpubsCounts) -> ConpubsCounts:
        self.numpdfs+=other.numpdfs
        self.numpages+=other.numpages
        self.numimages+=other.numimages
        self.numcons+=other.numcons
        self.numseries+=other.numseries
        self.numlinks+=other.numlinks
        return self

    def __str__(self) -> str:
        s=""
        if self.title is not None and len(self.title) > 0:
            s+=self.title+"\n"
        s+="#pagess="+str(self.numpages)+"\n"
        s+="#PDFs="+str(self.numpdfs)+"\n"
        s+="#imagess="+str(self.numimages)+"\n"
        s+="#linkss="+str(self.numlinks)+"\n"
        if self.numcons > 0:
            s+="#cons="+str(self.numcons)+"\n"
        if self.numseries > 0:
            s+="#series="+str(self.numseries)+"\n"

        return s