__version__ = '0.0'
__authors__ = ['"Hannah Dold" <hannah.dold@mailbox.tu-berlin.de>']
__copyright__ = '(c) 2009 Hannah Dold'
__license__ = 'LGPL v3, http://www.gnu.org/licenses/lgpl.html'
__contact__ = 'hannah.dold@mailbox.tu-berlin.de'

# import modules
#import errors
#import proxy
import views 
import objects

from pickle import dumps, loads

def convert(convertible):
    if isinstance(convertible, objects.ObjectDict):
        #create entity of class
        entity = views.Entity(convertible.__class__.__name__)
        
        #add parameters of different types to the entity
        for key,value in  convertible.items():
            if isinstance(value,str):
                entity.parameters.append(views.StringParameter(key,value))
            elif isinstance(value, int):
                entity.parameters.append(views.IntegerParameter(key,value))
            else:
                raise TypeError("Type of attribute '%s' with value '%s' is not supported" %
                                 (key, value))
        #add data to the entity
        for key,value in  convertible.data.items():
            d = views.Data(key,dumps(value))
            entity.data.append(d)
        
        #specify the entity as root
        entity.context.append(views.Context(","))
        return entity
    elif isinstance(convertible,views.Entity):
        #create class for entity
        try:
            exp_obj_class = getattr(objects, convertible.name)
        except KeyError:
            #occurs if the class definition is not know to proxy 
            #that means if not saved in objects
            raise KeyError("Experimental object class definitions must be saved in datamanager.objects")
                
        exp_obj = exp_obj_class()
   
        for parameter in convertible.parameters:
            exp_obj[parameter.name]=parameter.value
       
        for data in convertible.data:
            exp_obj.data[data.name]=loads(data.data)
        
        exp_obj.set_concurrent(True)
        return exp_obj