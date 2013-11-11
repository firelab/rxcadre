import wx
import gui_kyle_1

class MakeFrame(gui_kyle_1.MyFrame1):

    def __init__(self,parent):
        #initialize parent class
        gui_kyle_1.MyFrame1.__init__(self,parent)
 

    def makeFile(self,event):
        try:
            filename = self.text.GetLabel()
            target = open (filename, 'a')
            target.write("Bet you thought this file would be empty.")
            target.close()
            self.text.SetLabel(filename + " Created.  Would you like to make another?")
        except Exception:
            print 'error'
    
 
#mandatory in wx, create an app, False stands for not deteriction stdin/stdout

app = wx.App(False)
 
#create an object of CalcFrame
frame = MakeFrame(None)
#show the frame
frame.Show(True)
#start the applications
app.MainLoop()
