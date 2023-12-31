#! /usr/bin/env python2

import os
import re
import sys

aws_access_key_id = '1FKQS2A3QG79VFXNWWG2'
bucketname = 's3.ardith.org'
bucketurl = 'http://%s/' % bucketname
imgprefix = 'img'

# begin S3.py
import base64
import hmac
import httplib
import re
import sha
import sys
import time
import urllib
import xml.sax

DEFAULT_HOST = 's3.amazonaws.com'
PORTS_BY_SECURITY = { True: 443, False: 80 }
METADATA_PREFIX = 'x-amz-meta-'
AMAZON_HEADER_PREFIX = 'x-amz-'

# generates the aws canonical string for the given parameters
def canonical_string(method, path, headers, expires=None):
    interesting_headers = {}
    for key in headers:
        lk = key.lower()
        if lk in ['content-md5', 'content-type', 'date'] or lk.startswith(AMAZON_HEADER_PREFIX):
            interesting_headers[lk] = headers[key].strip()

    # these keys get empty strings if they don't exist
    if not interesting_headers.has_key('content-type'):
        interesting_headers['content-type'] = ''
    if not interesting_headers.has_key('content-md5'):
        interesting_headers['content-md5'] = ''

    # just in case someone used this.  it's not necessary in this lib.
    if interesting_headers.has_key('x-amz-date'):
        interesting_headers['date'] = ''

    # if you're using expires for query string auth, then it trumps date
    # (and x-amz-date)
    if expires:
        interesting_headers['date'] = str(expires)

    sorted_header_keys = interesting_headers.keys()
    sorted_header_keys.sort()

    buf = "%s\n" % method
    for key in sorted_header_keys:
        if key.startswith(AMAZON_HEADER_PREFIX):
            buf += "%s:%s\n" % (key, interesting_headers[key])
        else:
            buf += "%s\n" % interesting_headers[key]

    # don't include anything after the first ? in the resource...
    buf += "/%s" % path.split('?')[0]

    # ...unless there is an acl or torrent parameter
    if re.search("[&?]acl($|=|&)", path):
        buf += "?acl"
    elif re.search("[&?]torrent($|=|&)", path):
        buf += "?torrent"
    elif re.search("[&?]logging($|=|&)", path):
        buf += "?logging"

    return buf

# computes the base64'ed hmac-sha hash of the canonical string and the secret
# access key, optionally urlencoding the result
def encode(aws_secret_access_key, str, urlencode=False):
    b64_hmac = base64.encodestring(hmac.new(aws_secret_access_key, str, sha).digest()).strip()
    if urlencode:
        return urllib.quote_plus(b64_hmac)
    else:
        return b64_hmac

def merge_meta(headers, metadata):
    final_headers = headers.copy()
    for k in metadata.keys():
        final_headers[METADATA_PREFIX + k] = metadata[k]

    return final_headers



class AWSAuthConnection:
    def __init__(self, aws_access_key_id, aws_secret_access_key, is_secure=True,
                 server=DEFAULT_HOST, port=None):

        if not port:
            port = PORTS_BY_SECURITY[is_secure]

        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        if (is_secure):
            self.connection = httplib.HTTPSConnection("%s:%d" % (server, port))
        else:
            self.connection = httplib.HTTPConnection("%s:%d" % (server, port))


    def create_bucket(self, bucket, headers={}):
        return Response(self.make_request('PUT', bucket, headers))

    def list_bucket(self, bucket, options={}, headers={}):
        path = bucket
        if options:
            path += '?' + '&'.join(["%s=%s" % (param, urllib.quote_plus(str(options[param]))) for param in options])

        return ListBucketResponse(self.make_request('GET', path, headers))

    def delete_bucket(self, bucket, headers={}):
        return Response(self.make_request('DELETE', bucket, headers))

    def put(self, bucket, key, object, headers={}):
        if not isinstance(object, S3Object):
            object = S3Object(object)

        return Response(
                self.make_request(
                    'PUT',
                    '%s/%s' % (bucket, urllib.quote_plus(key)),
                    headers,
                    object.data,
                    object.metadata))

    def get(self, bucket, key, headers={}):
        return GetResponse(
                self.make_request('GET', '%s/%s' % (bucket, urllib.quote_plus(key)), headers))

    def head(self, bucket, key, headers={}):
        return GetResponse(
                self.make_request('HEAD', '%s/%s' % (bucket, urllib.quote_plus(key)), headers))

    def delete(self, bucket, key, headers={}):
        return Response(
                self.make_request('DELETE', '%s/%s' % (bucket, urllib.quote_plus(key)), headers))

    def get_bucket_logging(self, bucket, headers={}):
        return GetResponse(self.make_request('GET', '%s?logging' % (bucket), headers))

    def put_bucket_logging(self, bucket, logging_xml_doc, headers={}):
        return Response(self.make_request('PUT', '%s?logging' % (bucket), headers, logging_xml_doc))

    def get_bucket_acl(self, bucket, headers={}):
        return self.get_acl(bucket, '', headers)

    def get_acl(self, bucket, key, headers={}):
        return GetResponse(
                self.make_request('GET', '%s/%s?acl' % (bucket, urllib.quote_plus(key)), headers))

    def put_bucket_acl(self, bucket, acl_xml_document, headers={}):
        return self.put_acl(bucket, '', acl_xml_document, headers)

    def put_acl(self, bucket, key, acl_xml_document, headers={}):
        return Response(
                self.make_request(
                    'PUT',
                    '%s/%s?acl' % (bucket, urllib.quote_plus(key)),
                    headers,
                    acl_xml_document))

    def list_all_my_buckets(self, headers={}):
        return ListAllMyBucketsResponse(self.make_request('GET', '', headers))

    def make_request(self, method, path, headers={}, data='', metadata={}):
        final_headers = merge_meta(headers, metadata);
        # add auth header
        self.add_aws_auth_header(final_headers, method, path)

        self.connection.request(method, "/%s" % path, data, final_headers)
        return self.connection.getresponse()


    def add_aws_auth_header(self, headers, method, path):
        if not headers.has_key('Date'):
            headers['Date'] = time.strftime("%a, %d %b %Y %X GMT", time.gmtime())

        c_string = canonical_string(method, path, headers)
        headers['Authorization'] = \
            "AWS %s:%s" % (self.aws_access_key_id, encode(self.aws_secret_access_key, c_string))


class QueryStringAuthGenerator:
    # by default, expire in 1 minute
    DEFAULT_EXPIRES_IN = 60

    def __init__(self, aws_access_key_id, aws_secret_access_key, is_secure=True,
                 server=DEFAULT_HOST, port=None):

        if not port:
            port = PORTS_BY_SECURITY[is_secure]

        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        if (is_secure):
            self.protocol = 'https'
        else:
            self.protocol = 'http'

        self.server_name = "%s:%d" % (server, port)
        self.__expires_in = QueryStringAuthGenerator.DEFAULT_EXPIRES_IN
        self.__expires = None

    def set_expires_in(self, expires_in):
        self.__expires_in = expires_in
        self.__expires = None

    def set_expires(self, expires):
        self.__expires = expires
        self.__expires_in = None

    def create_bucket(self, bucket, headers={}):
        return self.generate_url('PUT', bucket, headers)

    def list_bucket(self, bucket, options={}, headers={}):
        path = bucket
        if options:
            path += '?' + '&'.join(["%s=%s" % (param, urllib.quote_plus(options[param])) for param in options])

        return self.generate_url('GET', path, headers)

    def delete_bucket(self, bucket, headers={}):
        return self.generate_url('DELETE', bucket, headers)

    def put(self, bucket, key, object, headers={}):
        if not isinstance(object, S3Object):
            object = S3Object(object)

        return self.generate_url(
                'PUT',
                '%s/%s' % (bucket, urllib.quote_plus(key)),
                merge_meta(headers, object.metadata))

    def get(self, bucket, key, headers={}):
        return self.generate_url('GET', '%s/%s' % (bucket, urllib.quote_plus(key)), headers)

    def delete(self, bucket, key, headers={}):
        return self.generate_url('DELETE', '%s/%s' % (bucket, urllib.quote_plus(key)), headers)

    def get_bucket_logging(self, bucket, headers={}):
        return self.generate_url('GET', '%s?logging' % (bucket), headers)

    def put_bucket_logging(self, bucket, logging_xml_doc, headers={}):
        return self.generate_url('PUT', '%s?logging' % (bucket), headers)

    def get_bucket_acl(self, bucket, headers={}):
        return self.get_acl(bucket, '', headers)

    def get_acl(self, bucket, key='', headers={}):
        return self.generate_url('GET', '%s/%s?acl' % (bucket, urllib.quote_plus(key)), headers)

    def put_bucket_acl(self, bucket, acl_xml_document, headers={}):
        return self.put_acl(bucket, '', acl_xml_document, headers)

    # don't really care what the doc is here.
    def put_acl(self, bucket, key, acl_xml_document, headers={}):
        return self.generate_url('PUT', '%s/%s?acl' % (bucket, urllib.quote_plus(key)), headers)

    def list_all_my_buckets(self, headers={}):
        return self.generate_url('GET', '', headers)

    def make_bare_url(self, bucket, key=''):
        return self.protocol + '://' + self.server_name + '/' + bucket + '/' + key

    def generate_url(self, method, path, headers):
        expires = 0
        if self.__expires_in != None:
            expires = int(time.time() + self.__expires_in)
        elif self.__expires != None:
            expires = int(self.__expires)
        else:
            raise "Invalid expires state"

        canonical_str = canonical_string(method, path, headers, expires)
        encoded_canonical = encode(self.aws_secret_access_key, canonical_str, True)

        if '?' in path:
            arg_div = '&'
        else:
            arg_div = '?'

        query_part = "Signature=%s&Expires=%d&AWSAccessKeyId=%s" % (encoded_canonical, expires, self.aws_access_key_id)

        return self.protocol + '://' + self.server_name + '/' + path  + arg_div + query_part



class S3Object:
    def __init__(self, data, metadata={}):
        self.data = data
        self.metadata = metadata

class Owner:
    def __init__(self, id='', display_name=''):
        self.id = id
        self.display_name = display_name

class ListEntry:
    def __init__(self, key='', last_modified=None, etag='', size=0, storage_class='', owner=None):
        self.key = key
        self.last_modified = last_modified
        self.etag = etag
        self.size = size
        self.storage_class = storage_class
        self.owner = owner

class CommonPrefixEntry:
    def __init(self, prefix=''):
        self.prefix = prefix

class Bucket:
    def __init__(self, name='', creation_date=''):
        self.name = name
        self.creation_date = creation_date

class Response:
    def __init__(self, http_response):
        self.http_response = http_response
        # you have to do this read, even if you don't expect a body.
        # otherwise, the next request fails.
        self.body = http_response.read()

class ListBucketResponse(Response):
    def __init__(self, http_response):
        Response.__init__(self, http_response)
        if http_response.status < 300:
            handler = ListBucketHandler()
            xml.sax.parseString(self.body, handler)
            self.entries = handler.entries
            self.common_prefixes = handler.common_prefixes
            self.name = handler.name
            self.marker = handler.marker
            self.prefix = handler.prefix
            self.is_truncated = handler.is_truncated
            self.delimiter = handler.delimiter
            self.max_keys = handler.max_keys
            self.next_marker = handler.next_marker
        else:
            self.entries = []

class ListAllMyBucketsResponse(Response):
    def __init__(self, http_response):
        Response.__init__(self, http_response)
        if http_response.status < 300: 
            handler = ListAllMyBucketsHandler()
            xml.sax.parseString(self.body, handler)
            self.entries = handler.entries
        else:
            self.entries = []

class GetResponse(Response):
    def __init__(self, http_response):
        Response.__init__(self, http_response)
        response_headers = http_response.msg   # older pythons don't have getheaders
        metadata = self.get_aws_metadata(response_headers)
        self.object = S3Object(self.body, metadata)

    def get_aws_metadata(self, headers):
        metadata = {}
        for hkey in headers.keys():
            if hkey.lower().startswith(METADATA_PREFIX):
                metadata[hkey[len(METADATA_PREFIX):]] = headers[hkey]
                del headers[hkey]

        return metadata

class ListBucketHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.entries = []
        self.curr_entry = None
        self.curr_text = ''
        self.common_prefixes = []
        self.curr_common_prefix = None
        self.name = ''
        self.marker = ''
        self.prefix = ''
        self.is_truncated = False
        self.delimiter = ''
        self.max_keys = 0
        self.next_marker = ''
        self.is_echoed_prefix_set = False

    def startElement(self, name, attrs):
        if name == 'Contents':
            self.curr_entry = ListEntry()
        elif name == 'Owner':
            self.curr_entry.owner = Owner()
        elif name == 'CommonPrefixes':
            self.curr_common_prefix = CommonPrefixEntry()
            

    def endElement(self, name):
        if name == 'Contents':
            self.entries.append(self.curr_entry)
        elif name == 'CommonPrefixes':
            self.common_prefixes.append(self.curr_common_prefix)
        elif name == 'Key':
            self.curr_entry.key = self.curr_text
        elif name == 'LastModified':
            self.curr_entry.last_modified = self.curr_text
        elif name == 'ETag':
            self.curr_entry.etag = self.curr_text
        elif name == 'Size':
            self.curr_entry.size = int(self.curr_text)
        elif name == 'ID':
            self.curr_entry.owner.id = self.curr_text
        elif name == 'DisplayName':
            self.curr_entry.owner.display_name = self.curr_text
        elif name == 'StorageClass':
            self.curr_entry.storage_class = self.curr_text
        elif name == 'Name':
            self.name = self.curr_text
        elif name == 'Prefix' and self.is_echoed_prefix_set:
            self.curr_common_prefix.prefix = self.curr_text
        elif name == 'Prefix':
            self.prefix = self.curr_text
            self.is_echoed_prefix_set = True            
        elif name == 'Marker':
            self.marker = self.curr_text
        elif name == 'IsTruncated':
            self.is_truncated = self.curr_text == 'true'
        elif name == 'Delimiter':
            self.delimiter = self.curr_text
        elif name == 'MaxKeys':
            self.max_keys = int(self.curr_text)
        elif name == 'NextMarker':
            self.next_marker = self.curr_text

        self.curr_text = ''

    def characters(self, content):
        self.curr_text += content


class ListAllMyBucketsHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.entries = []
        self.curr_entry = None
        self.curr_text = ''

    def startElement(self, name, attrs):
        if name == 'Bucket':
            self.curr_entry = Bucket()

    def endElement(self, name):
        if name == 'Name':
            self.curr_entry.name = self.curr_text
        elif name == 'CreationDate':
            self.curr_entry.creation_date = self.curr_text
        elif name == 'Bucket':
            self.entries.append(self.curr_entry)

    def characters(self, content):
        self.curr_text = content
# end S3.py

def s3secretkey(aws_access_key_id):
	cmd = 'security 2>&1 >/dev/null find-generic-password -ga %s' % \
		aws_access_key_id
	cmdpipe = os.popen(cmd)
	awssecretaccesskey = cmdpipe.read()
	cmdpipe.close()

	m = re.match('password:\s+"(\S+)"', awssecretaccesskey)
	if not m:
		return None
	awssecretaccesskey = m.group(1)
	return awssecretaccesskey

def nextslot(conn):
	response = conn.get(bucketname, imgprefix)
	if response.http_response.status == 404:
		return '1'
	if response.http_response.status != 200:
		raise 'could not get nextslot'
	return response.object.metadata['nextslot']

def mimetype(path):
	cmd = 'file -i %s' % path
	cmdpipe = os.popen(cmd)
	cmdout = cmdpipe.read()
	cmdpipe.close()
	m = re.match('.+:\s+(\S+/.+)', cmdout)
	if not m:
		return 'application/octet-stream'
	return m.group(1).strip()

def store(conn, title, data, mimetype):
	slot = nextslot(conn)
	key = imgprefix + '/' + slot
	response = conn.put(bucketname, key, S3Object(data, {'title': title}),
	    {'x-amz-acl': 'public-read', 'Content-Type': mimetype})
	if response.http_response.status != 200:
		raise 'could not put'
	response = conn.put(bucketname, imgprefix, S3Object('foo', {'nextslot':
	    str(1 + int(slot))}))
	if response.http_response.status != 200:
		raise 'could not put nextslot'
	return bucketurl + key

def add(conn, title, path):
	u = store(conn, title, open(path).read(), mimetype(path))
	print u
	sys.exit(0)

def ls(conn):
	r = conn.list_bucket(bucketname, {'prefix': imgprefix + '/'})
	if r.http_response.status != 200:
		raise 'could not list_bucket'
	ents = map(lambda x: x.key, r.entries)
	for i in ents:
		r = conn.head(bucketname, i)
		if r.http_response.status != 200:
			raise 'get metadata failed'
		print '%s%s  %s' % (bucketurl, i, r.object.metadata['title'])
	sys.exit(0)

def usage():
	print '''Usage: %(cmd)s <cmd> [ <args> ]

    %(cmd)s add <file> "title"
    %(cmd)s list
''' % {'cmd': sys.argv[0]}
	sys.exit(1)

def main(argc, argv):
	c = AWSAuthConnection(aws_access_key_id, s3secretkey(aws_access_key_id))
	if argc < 2: usage()
	if argv[1] == 'list' or argv[1] == 'ls':
		ls(c)
	if argv[1] == 'add':
		if argc != 4:
			print 'Usage: %s add file "title"' % argv[0]
			sys.exit(1)
		add(c, argv[3], argv[2])
	usage()

if __name__ == '__main__':
	main(len(sys.argv), sys.argv)
