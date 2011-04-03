import web

import json
from mimerender import mimerender

import xdapy

global mapper

def info():
    return "Database: " + mapper.connection.db

def JsonHandler(full=False):
    def wrapper(obj):
        if hasattr(obj, 'to_json'):
            return obj.to_json(full)
        else:
            raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))
    return wrapper


render_xml = lambda title, body: '<message>%s</message>'%body

def render_json(**kwargs):
    return json.dumps(kwargs, default=JsonHandler())

def render_html(**kwargs):
    return RenderHtml(title="", body=json.dumps(kwargs, default=JsonHandler())).render() # lambda title, body: RenderHtml(title=title, body=body).render()

render_txt = lambda title, body: body

class RenderHtml(object):
    template = u"""<!doctype html>
<head>
  <meta charset="utf-8">
  <title  dir="ltr">{title}</title> 
</head>
<body>
{body}
</body>"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def render(self):
        return RenderHtml.template.format(*self.args, **self.kwargs)

render = mimerender(
        default = 'html',
        override_input_key = 'format',
        html = render_html,
        #        xml  = render_xml,
        json = render_json,
        txt  = render_txt
        )

class Main(object):
    from web import form

    render = web.template.render('templates', globals={'information': info}) # your templates

    vpass = form.regexp(r".{3,20}$", 'must be between 3 and 20 characters')
    vemail = form.regexp(r".*@.*", "must be a valid email address")

    register_form = web.form.Form(
                web.form.Textbox('', class_='textfield', id='textfield'),
                )

    def GET(self):
        f = Main.register_form()
        return Main.render.index(f, "TEXT")
    
    def POST(self):
        form = Main.register_form()
        form.validates()
        s = form.value['textfield']
        return s


class Entity(object):
    def analyse_path(self, path):
        splitted = path.split("/")
        id = collection = key = None
        try:
            id = splitted[0]
            collection = splitted[1]
            key = splitted[2]
        except IndexError:
            pass
        return id, collection, key
    
    @render
    def PUT(self, path):
        id, collection, key = self.analyse_path(path)
        
        if not id:
            data = web.data()
            data_dict = json.loads(data)
            type = data_dict["type"]
            del data_dict["type"]
            
            entity = mapper.create(type, **data_dict)
            return entity.to_json()
            
        
        print web.data()
        return {'res': "PUT" + id}
    
    @render
    def DELETE(self, path):
        id, collection, key = self.analyse_path(path)

        obj = mapper.find_by_id(xdapy.structures.Entity, id)
        if obj is None:
            return {'res': None}
        mapper.delete(obj)
        return {'deleted': 'ok'}
    
    @render
    def POST(self, path):
        print "POST"
        
        id, collection, key = self.analyse_path(path)
        data = web.data()
        
        if collection == "param" and not key:
            data_dict = json.loads(data)
            
            entity = mapper.find_by_id(xdapy.structures.Entity, id)
            setattr(entity, collection, data_dict)
            return {'success': 'ok'}

        return {'res': "POST" + id}
    
    @render
    def GET(self, path=None):
        id, collection, key = self.analyse_path(path)
        
        if not id:
            filter = web.input(filter=None)['filter']
            if filter:
                entities = mapper.find_all(xdapy.structures.Entity, filter)
            else:
                entities = mapper.find_all(xdapy.structures.Entity)
            return { 'count': len(entities), 'items': entities }

        if not collection:
            entity = mapper.find_by_id(xdapy.structures.Entity, id)
            if entity is None:
                entity = {'res': None}
            else:
                entity = entity.to_json(True)
            return entity
        
        if not key:
            entity = mapper.find_by_id(xdapy.structures.Entity, id)
            if hasattr(getattr(entity, collection), "copy"):
                res = getattr(entity, collection).copy()
            else:
                res = getattr(entity, collection)
            return {'res': res}

import argparse


web.webapi.internalerror = web.debugerror
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str)
    parser.add_argument('-o', '--objects', type=str, nargs='+', default=['xdapy.objects'])
    parser.add_argument('-p', '--port', type=int, nargs='?', default=8080)

    args, rest = parser.parse_known_args()

    import sys
    for obj in args.objects:
        __import__(obj)

    # remove our arguments from the rest of the arguments
    sys.argv[1:] = [str(args.port)] + rest

    from xdapy import Connection
    from xdapy import Mapper

    connection = Connection.profile(args.database) # use standard profile
    mapper = Mapper(connection)

    urls = (
            '/', Main,
            '/entity/(.*)', Entity
            )
    app = web.application(urls, globals())
    app.run()

