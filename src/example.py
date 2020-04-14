# Taken from https://github.com/dmnfarrell/pandastable/wiki/Code-Examples
# https://gist.github.com/gugat/7cf57eb628f3bb0a3d54b3f8d0023b63
from tkinter import *
from pandastable import Table, TableModel

class TestApp(Frame):
    """Basic test frame for the table"""
    def __init__(self, parent=None):
        self.parent = parent
        Frame.__init__(self)
        self.main = self.master
        self.main.geometry('600x400+200+100')
        self.main.title('Table app')
        f = Frame(self.main)
        f.pack(fill=BOTH,expand=1)
        df = TableModel.getSampleData()
        self.table = pt = Table(f, dataframe=df,
                                showtoolbar=True, showstatusbar=True)
        pt.show()
        return

app = TestApp()
#launch the app
app.mainloop()