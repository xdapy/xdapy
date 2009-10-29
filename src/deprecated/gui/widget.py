'''
Created on Jul 17, 2009

@author: hannah
To build this widget run:
/<your pyjamas installation path>/bin/pyjsbuild widget
'''
from pyjamas.ui.Button import Button
from pyjamas.ui.CheckBox import CheckBox
from pyjamas.ui.RootPanel import RootPanel
from pyjamas.ui.HTML import HTML
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas import Window
from test import Test

def greet(sender):
    RootPanel().add(HTML("Not in Kansas no more"))
    y = CheckBox("yellow road")
    r = CheckBox("red road")
    g = CheckBox("green road")
   # p = HorizontalPanel()
    #p.add(y)
    #p.add(r)
    RootPanel().add(y)
    
if __name__ == '__main__':
    b = Button("Click me", greet)
    hw = HTML("Hello <b>World</b>")

    p = HorizontalPanel()
    p.add(b)
    p.add(hw)

    RootPanel().add(p)