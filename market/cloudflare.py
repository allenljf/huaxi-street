"""One-time Pages provisioning. Token is accepted through environment, never args."""
import argparse
import json
import os
import re
import urllib.request
from urllib.error import HTTPError


def api_request(method,url,token,body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(url,data=data,method=method,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)


def configure_project(account,token,project,request=api_request):
    if not re.fullmatch(r'[0-9a-fA-F]{32}',account) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,57}',project):raise ValueError('帳號ID或專案名稱格式不正確')
    base=f'https://api.cloudflare.com/client/v4/accounts/{account}/pages/projects'
    try:response=request('GET',base+'/'+project,token)
    except HTTPError as e:
        if e.code!=404:raise
        response=request('POST',base,token,{'name':project,'production_branch':'main'})
    if response.get('success') is not True:raise ValueError('Cloudflare未確認專案設定成功')
    domain=response.get('result',{}).get('subdomain','')
    if not domain.endswith('.pages.dev') or not re.fullmatch(r'[a-z0-9.-]+',domain):raise ValueError('Cloudflare未回傳有效Pages網址')
    return 'https://'+domain

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);args=p.parse_args()
    try:print(configure_project(os.environ['CLOUDFLARE_ACCOUNT_ID'],os.environ['CLOUDFLARE_API_TOKEN'],args.project))
    except HTTPError as e:p.exit(1,f'Cloudflare API 回應HTTP {e.code}；請檢查帳號與Pages Edit權限。\n')
    except (ValueError,KeyError,OSError):p.exit(1,'Cloudflare設定未完成，請檢查帳號ID、專案名稱與授權。\n')
