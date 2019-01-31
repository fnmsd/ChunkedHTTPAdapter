#coding=utf8
'''
Origin Source from request.adapters.HTTPAdaptor
Modify by fnmsd
'''
from requests.adapters import HTTPAdapter
import socket
from urllib3.util import Timeout as TimeoutSauce
from urllib3.exceptions import ClosedPoolError
from urllib3.exceptions import ConnectTimeoutError
from urllib3.exceptions import HTTPError as _HTTPError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import NewConnectionError
from urllib3.exceptions import ProxyError as _ProxyError
from urllib3.exceptions import ProtocolError
from urllib3.exceptions import ReadTimeoutError
from urllib3.exceptions import SSLError as _SSLError
from urllib3.exceptions import ResponseError
from requests.exceptions import (ConnectionError, ConnectTimeout, ReadTimeout, SSLError, ProxyError, RetryError)
from urllib3.response import HTTPResponse
from string import ascii_letters,octdigits
import random

DEFAULT_POOL_TIMEOUT = None


class ChunkedHTTPAdapter(HTTPAdapter):



    _keyword_list = []

    def get_random_lenth(self):
        return random.randint(10, 1000)

    get_chunk_length = get_random_lenth


    py_version = 2

    def checkKeyword(self, data):
        data = str(data)
        _ret = list(map(lambda z:z[1]+int(z[0]/2),
                    filter(lambda y:y[1]!=-1,
                          map(lambda x: (len(x), data.find(x)), self.keyword_list)
                          )
                   ))

        if len(_ret) == 0:
            return -1
        else:
            return min(_ret)

        self._keyword_list = []

    @property
    def keyword_list(self):
        #print("get name called")
        return self._keyword_list

    @keyword_list.setter
    def keyword_list(self,keyword_list):
        self._keyword_list = list(filter(lambda x:isinstance(x,str) and len(x)>1,keyword_list))
        if len(keyword_list) != len(self._keyword_list):
            print("Dropped Keyword："+",".join(list(filter(lambda x:not(isinstance(x,str) and len(x)>1),keyword_list))))







    def __init__(self,chunk_length=None):
        if chunk_length is None:
            self.get_chunk_length = self.get_random_lenth
        else:
            if isinstance(chunk_length,int):
                self.get_chunk_length = lambda:chunk_length
            elif isinstance(chunk_length,function):
                self.get_chunk_length = chunk_length
            else:
                raise Exception("Unkown type {}"% type(chunk_length))

        import sys
        if sys.version_info >= (3,0):
            self.py_version = 3



        super(ChunkedHTTPAdapter, self).__init__()

    def gen_data(self,request_data):
        pointer = 0
        while pointer < len(request_data):
            now_length = self.get_chunk_length()
            new_length = self.checkKeyword(request_data[pointer:pointer+now_length])
            if(new_length != -1):
                now_length = new_length
            yield request_data[pointer:pointer+now_length]
            pointer += now_length


    def get_random(self):
        length = random.randint(1,15)
        _ret = ""
        for i in range(length):
            _ret += random.choice(ascii_letters+octdigits)
        return _ret
    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        """Sends PreparedRequest object. Returns Response object.

        :param request: The :class:`PreparedRequest <PreparedRequest>` being sent.
        :param stream: (optional) Whether to stream the request content.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple or urllib3 Timeout object
        :param verify: (optional) Either a boolean, in which case it controls whether
            we verify the server's TLS certificate, or a string, in which case it
            must be a path to a CA bundle to use
        :param cert: (optional) Any user-provided SSL certificate to be trusted.
        :param proxies: (optional) The proxies dictionary to apply to the request.
        :rtype: requests.Response
        """
        conn = self.get_connection(request.url, proxies)

        self.cert_verify(conn, request.url, verify, cert)
        url = self.request_url(request, proxies)
        self.add_headers(request)


        chunked = not (request.body is None or 'Content-Length' in request.headers)


        #非chunked还存在request.body的情况,自动转换为trunked
        if not chunked and request.body is not None:
            if request.headers.get("Transfer-Encoding",None) != "chunked":
                request.headers["Transfer-Encoding"] = "chunked"
                if 'Content-Length' in request.headers:
                    del request.headers['Content-Length']
            request.body = self.gen_data(request.body)
            chunked = True


        if isinstance(timeout, tuple):
            try:
                connect, read = timeout
                timeout = TimeoutSauce(connect=connect, read=read)
            except ValueError as e:
                # this may raise a string formatting error.
                err = ("Invalid timeout {0}. Pass a (connect, read) "
                       "timeout tuple, or a single float to set "
                       "both timeouts to the same value".format(timeout))
                raise ValueError(err)
        elif isinstance(timeout, TimeoutSauce):
            pass
        else:
            timeout = TimeoutSauce(connect=timeout, read=timeout)

        try:
            if not chunked:
                resp = conn.urlopen(
                    method=request.method,
                    url=url,
                    body=request.body,
                    headers=request.headers,
                    redirect=False,
                    assert_same_host=False,
                    preload_content=False,
                    decode_content=False,
                    retries=self.max_retries,
                    timeout=timeout
                )

            # Send the request.
            else:
                if hasattr(conn, 'proxy_pool'):
                    conn = conn.proxy_pool

                low_conn = conn._get_conn(timeout=DEFAULT_POOL_TIMEOUT)

                try:
                    low_conn.putrequest(request.method,
                                        url,
                                        skip_accept_encoding=True)

                    for header, value in request.headers.items():
                        low_conn.putheader(header, value)

                    low_conn.endheaders()
                    is_first = True
                    for i in request.body:
                        low_conn.send((hex(len(i))[2:]+";"+self.get_random()).encode('utf-8'))
                        low_conn.send(b'\r\n')
                        #Python3适配，不确定会不会有问题┑(￣Д ￣)┍
                        if self.py_version == 2 or isinstance(i,bytes):
                            low_conn.send(i)
                        else:
                            low_conn.send(i.encode())
                        low_conn.send(b'\r\n')


                    low_conn.send(b'0\r\n\r\n')

                    # Receive the response from the server
                    try:
                        # For Python 2.7+ versions, use buffering of HTTP
                        # responses
                        r = low_conn.getresponse(buffering=True)
                    except TypeError:
                        # For compatibility with Python 2.6 versions and back
                        r = low_conn.getresponse()

                    resp = HTTPResponse.from_httplib(
                        r,
                        pool=conn,
                        connection=low_conn,
                        preload_content=False,
                        decode_content=False
                    )
                except:
                    # If we hit any problems here, clean up the connection.
                    # Then, reraise so that we can handle the actual exception.
                    low_conn.close()
                    raise

        except (ProtocolError, socket.error) as err:
            raise ConnectionError(err, request=request)

        except MaxRetryError as e:
            if isinstance(e.reason, ConnectTimeoutError):
                # TODO: Remove this in 3.0.0: see #2811
                if not isinstance(e.reason, NewConnectionError):
                    raise ConnectTimeout(e, request=request)

            if isinstance(e.reason, ResponseError):
                raise RetryError(e, request=request)

            if isinstance(e.reason, _ProxyError):
                raise ProxyError(e, request=request)

            if isinstance(e.reason, _SSLError):
                # This branch is for urllib3 v1.22 and later.
                raise SSLError(e, request=request)

            raise ConnectionError(e, request=request)

        except ClosedPoolError as e:
            raise ConnectionError(e, request=request)

        except _ProxyError as e:
            raise ProxyError(e)

        except (_SSLError, _HTTPError) as e:
            if isinstance(e, _SSLError):
                # This branch is for urllib3 versions earlier than v1.22
                raise SSLError(e, request=request)
            elif isinstance(e, ReadTimeoutError):
                raise ReadTimeout(e, request=request)
            else:
                raise

        return self.build_response(request, resp)
