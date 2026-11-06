"""One-time Pages provisioning. Token is accepted through environment, never args."""
import argparse
import json
import os
import re
import urllib.request
from urllib.error import HTTPError


def api_request(method,url,token,body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(url,data=data,method=method,headers={'Authorization':'Bearer '+token.strip(),'Content-Type':'application/json','Accept':'application/json','User-Agent':'HuaxiMarketJournal/1.0 (Cloudflare Pages setup)'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)


def configure_project(account,token,project,request=api_request):
    if not re.fullmatch(r'[0-9a-fA-F]{32}',account) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,57}',project):raise ValueError('帳號ID或專案名稱格式不正確')
    base=f'https://api.cloudflare.com/client/v4/accounts/{account}/pages/projects'
    try:response=request('GET',base+'/'+project,token)
    except HTTPError as e:
        if e.code!=404:raise
        e.close()
        response=request('POST',base,token,{'name':project,'production_branch':'main'})
    if response.get('success') is not True:raise ValueError('Cloudflare未確認專案設定成功')
    domain=response.get('result',{}).get('subdomain','')
    if not domain.endswith('.pages.dev') or not re.fullmatch(r'[a-z0-9.-]+',domain):raise ValueError('Cloudflare未回傳有效Pages網址')
    return 'https://'+domain

def describe_http_error(error,token=''):
    """Expose only bounded Cloudflare codes/messages, never raw headers or HTML."""
    try:
        raw=error.read(65536)
        payload=json.loads(raw.decode('utf-8','replace'))
    except (ValueError,AttributeError,TypeError):payload=None
    finally:error.close()
    lines=[f'Cloudflare API 回應HTTP {error.code}。']
    if isinstance(payload,dict) and isinstance(payload.get('errors'),list):
        for item in payload['errors'][:3]:
            if not isinstance(item,dict):continue
            code=item.get('code');code=str(code) if isinstance(code,int) else '未提供'
            message=str(item.get('message','未提供訊息'))
            if token:message=message.replace(token,'<REDACTED>')
            message=re.sub(r'(?i)bearer\s+\S+','Bearer <REDACTED>',message)
            message=' '.join(message.split())[:300]
            lines.append(f'Cloudflare錯誤碼 {code}：{message}')
    else:lines.append('Cloudflare未回傳JSON錯誤內容（非JSON）；無法僅憑HTTP狀態判定Token是否有效。')
    if error.code in {401,403}:
        lines.extend(['請逐項核對：',
          '  1. Permissions：Account / Cloudflare Pages / Edit。',
          '  2. Account Resources：Include / Specific account，選擇與輸入帳號ID完全相同的帳號（不是Zone ID）。',
          '  3. Token尚未到期，啟用時間已生效；Client IP filtering須允許本機與之後的GitHub runner。',
          '  4. 只貼Token字串，不含Bearer、引號或整段curl。'])
    return '\n'.join(lines)


def token_status(token,request=api_request):
    try:
        response=request('GET','https://api.cloudflare.com/client/v4/user/tokens/verify',token)
        status=response.get('result',{}).get('status')
        return status if response.get('success') is True and status in {'active','disabled','expired'} else 'unknown'
    except HTTPError as error:
        error.close();return 'unknown'
    except (OSError,ValueError,KeyError,TypeError):return 'unknown'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);args=p.parse_args()
    token=os.environ.get('CLOUDFLARE_API_TOKEN','').strip()
    try:print(configure_project(os.environ['CLOUDFLARE_ACCOUNT_ID'],token,args.project))
    except HTTPError as error:
        message=describe_http_error(error,token)
        if error.code in {401,403}:
            status=token_status(token)
            message+='\n'+('Token狀態：active（本身有效）；這仍不代表具有此帳號的Pages權限。' if status=='active' else f'Token驗證狀態：{status}；請參照上述Cloudflare錯誤碼。')
        p.exit(1,message+'\n')
    except (ValueError,KeyError,OSError):p.exit(1,'Cloudflare設定未完成，請檢查帳號ID、專案名稱與授權。\n')
