'''
Created on Jul 2, 2009

'''
import networkx as nx 
import xml.sax.saxutils
from mpl_toolkits.basemap import Basemap as Basemap 
#from pylab import title, show
import matplotlib.pyplot as plt 

__author__=['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
if __name__ == '__main__':
    m = Basemap(llcrnrlon=-125.5,llcrnrlat=20., 
                urcrnrlon=-50.566,urcrnrlat=40.0, 
                resolution='l',area_thresh=1000.,projection='lcc', 
                lat_1=50.,lon_0=-107.) 
    # position in decimal lat/lon 
    lats=[37.96,42.82] 
    lons=[-121.29,-73.95] 
    # convert lat and lon to map projection 
    mx,my=m(lons,lats) 
    # The NetworkX part 
    # put map projection coordinates in pos dictionary 
    G=nx.Graph() 
    G.add_edge('a','b') 
    pos={} 
    pos['a']=(mx[0],my[0]) 
    pos['b']=(mx[1],my[1]) 
    # draw 
    nx.draw_networkx(G,pos,node_size=200) 
    # Now draw the map 
    m.drawcoastlines() 
    m.drawcountries() 
    m.drawstates() 
    #m.scatter(x,y,25,colors,marker='o',edgecolors='none',zorder=10) 
    plt.title('How to get from point a to point b') 
    plt.show() 