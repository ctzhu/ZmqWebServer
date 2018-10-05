from zmq.eventloop.zmqstream import ZMQStream
import functools
import json
import logging
import os
import tornado
import tornado.ioloop
import tornado.web
import uuid
import zmq

__UPLOADS__ = "uploads/"
__POUT__ = 'tcp://127.0.0.1:12345'
__PIN__ = 'tcp://127.0.0.1:12346'


def response_callback(msg):
    return [b'Yes']


def addzmq_device(pubipport, repipport, callback):
    def inner_func(func):
        @functools.wraps(func)
        def res_func(*args, **kwargs):
            app = func(*args, **kwargs)
            ctx = zmq.Context.instance()
            sOut = ctx.socket(zmq.PUB)
            sOut.bind(pubipport)
            sIn = ctx.socket(zmq.REP)
            sIn.bind(repipport)
            streamOut = ZMQStream(sOut)
            streamIn = ZMQStream(sIn)
            def callback_in(msg):
                streamIn.send_multipart(response_callback(msg))
            streamIn.on_recv(callback_in)
            app.__setattr__('streamIn', streamIn)
            app.__setattr__('streamOut', streamOut)
            return app
        return res_func
    return inner_func


class Userform(tornado.web.RequestHandler):
    def get(self):
        self.render("fileuploadform.html")


class Upload(tornado.web.RequestHandler):
    def post(self):
        fileinfo = self.request.files['filearg'][0]
        print("fileinfo is", fileinfo)
        fname = fileinfo['filename']
        extn = os.path.splitext(fname)[1]
        cname = str(uuid.uuid4()) + extn
        fh = open(__UPLOADS__ + cname, 'w')
        fh.write(fileinfo['body'])
        self.finish(cname + " is uploaded!! Check %s folder" % __UPLOADS__)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.application.streamOut.send_multipart([b'msg', b'Hello world'])
        self.write("Hello, world")


class PathHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        logging.info(self.request.uri)
        logging.info(json.dumps(args))
        logging.info(json.dumps(kwargs))
        logging.info('%s' % id(self.application.streamIn))
        self.write(b'Good')
        self.finish(b'Done')


@addzmq_device(__POUT__, __PIN__, response_callback)
def make_app():
    # Here if you put capture groups in the endpoints definition
    # You either use all named capture groups or all position capture groups
    # Not a mixture of both
    return tornado.web.Application([
                (r"/", Userform),
                (r"/main", MainHandler),
                (r"/upload", Upload),
                (r"/rest/(?P<name>.*)/get/(?P<key>.*)", PathHandler),
                (r"/rest/(.*)/get2/(.*)", PathHandler)
               ], debug=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        loop = tornado.ioloop.IOLoop.current()
        app = make_app()
        app.listen(8999)
        loop.start()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()       # might be redundant, the loop has already stopped
        loop.close(True)  # needed to close all open sockets
    print("Server shut down, exiting...")
