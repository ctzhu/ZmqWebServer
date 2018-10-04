import tornado
import tornado.ioloop
import tornado.web
from zmq.eventloop.zmqstream import ZMQStream
# from tornado import gen, ioloop
import zmq
# from zmq.eventloop.future import Context
import os
import uuid
import logging
import json

__UPLOADS__ = "uploads/"


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


def make_app():
    # Here if you put capture groups in the endpoints definition
    # You either use all named capture groups or all position capture groups
    # Not a mixture of both
    app = tornado.web.Application(
            [
             (r"/", Userform),
             (r"/main", MainHandler),
             (r"/upload", Upload),
             (r"/rest/(?P<name>.*)/get/(?P<key>.*)", PathHandler),
             (r"/rest/(.*)/get2/(.*)", PathHandler)
            ], debug=True)
    ctx = zmq.Context.instance()
    sOut = ctx.socket(zmq.PUB)
    sOut.bind('tcp://127.0.0.1:12345')
    sIn = ctx.socket(zmq.REP)
    sIn.bind('tcp://127.0.0.1:12346')
    streamOut = ZMQStream(sOut)
    streamIn = ZMQStream(sIn)
    logging.info('init stream instance %s' % id(streamIn))

    def callback_in(msg):
        streamIn.send_multipart([b'Yes'])
    streamIn.on_recv(callback_in)
    app.__setattr__('streamIn', streamIn)
    app.__setattr__('streamOut', streamOut)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        app = make_app()
        app.listen(8999)
        loop = tornado.ioloop.IOLoop.current()
        loop.start()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()       # might be redundant, the loop has already stopped
        loop.close(True)  # needed to close all open sockets
    print("Server shut down, exiting...")
