"""Local offline dashboard server. Reads saved OD; never calls a routing service."""
import argparse
import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from data_access import ROOT,SavedRoads


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    roads=SavedRoads()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
        def do_GET(self):
            parsed=urlparse(self.path)
            if parsed.path=='/api/route':
                try:
                    q=parse_qs(parsed.query);case=q['case'][0]
                    if case not in ['S1','S2','S3']:raise ValueError('Unknown scenario')
                    value=roads.pair(case,int(q['i'][0]),int(q['j'][0]));status=200
                    if not value['geometry_check']['passed']:value['coordinates']=[];value['error']='HOLD: road shape length mismatch';status=422
                except Exception as e:value={'error':str(e)};status=400
                payload=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
                self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
            else:super().do_GET()
    print(f'Local dashboard: http://127.0.0.1:{args.port}/index.html',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()


if __name__=='__main__':main()
