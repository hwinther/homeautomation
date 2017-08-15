#!/usr/bin/python
import urllib2
import json


class WebCli(object):
    def __init__(self, baseurl):
        self.baseurl = baseurl

    def post_request(self, method_uri, **args):
        url = self.baseurl + method_uri  # '/1/input/key'
        data = json.dumps(args)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)  # response.headers.type #'text/html'  'application/json'
        content = response.read()  # response.getcode() #int
        return response.code == 200  # TODO: throw exception in other cases, and include errormessage from content

    def get_request(self, method_uri):
        url = self.baseurl + method_uri
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        content = response.read()
        if response.headers.type == 'application/json':
            content = json.loads(content)
        return response.code == 200, content

    def get_request_json(self, method_uri):
        url = self.baseurl + method_uri
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        content = response.read()
        if response.headers.type == 'application/json':
            return json.loads(content)  # TODO: we may be getting json even if its not code=200.. then what?
        else:
            return '{}'  # empty deserialized json format
