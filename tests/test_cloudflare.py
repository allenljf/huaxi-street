import unittest
from urllib.error import HTTPError
from market.cloudflare import configure_project

class CloudflareTests(unittest.TestCase):
    def test_existing_project_is_not_created_again(self):
        calls=[]
        def request(method,url,token,body=None):
            calls.append((method,url));return {'success':True,'result':{'name':'huaxi-street','subdomain':'huaxi-street.pages.dev'}}
        domain=configure_project('a'*32,'hidden','huaxi-street',request)
        self.assertEqual(domain,'https://huaxi-street.pages.dev')
        self.assertEqual([m for m,u in calls],['GET'])

    def test_only_404_allows_project_creation(self):
        calls=[]
        def request(method,url,token,body=None):
            calls.append(method)
            if method=='GET':raise HTTPError(url,404,'missing',{},None)
            self.assertEqual(body,{'name':'huaxi-street','production_branch':'main'})
            return {'success':True,'result':{'name':'huaxi-street','subdomain':'huaxi-street.pages.dev'}}
        self.assertEqual(configure_project('a'*32,'hidden','huaxi-street',request),'https://huaxi-street.pages.dev')
        self.assertEqual(calls,['GET','POST'])

    def test_auth_failure_does_not_trigger_create(self):
        def request(method,url,token,body=None):
            self.assertEqual(method,'GET');raise HTTPError(url,403,'forbidden',{},None)
        with self.assertRaises(HTTPError) as raised:configure_project('a'*32,'hidden','huaxi-street',request)
        raised.exception.close()

    def test_invalid_project_name_rejected_before_any_request(self):
        with self.assertRaises(ValueError):configure_project('a'*32,'hidden','bad;name')


class CloudflareDiagnosticsTests(unittest.TestCase):
    def test_403_keeps_cloudflare_code_and_redacts_token(self):
        import io,json
        from market.cloudflare import describe_http_error
        body=json.dumps({'errors':[{'code':10000,'message':'Authentication error Bearer secret-token; key=secret-token'}],'success':False}).encode()
        error=HTTPError('https://api.cloudflare.com/client/v4/accounts/a/pages/projects/p',403,'Forbidden',{},io.BytesIO(body))
        message=describe_http_error(error,token='secret-token')
        self.assertIn('403',message)
        self.assertIn('10000',message)
        self.assertIn('Authentication error',message)
        self.assertNotIn('secret-token',message)
        self.assertIn('Account / Cloudflare Pages / Edit',message)

    def test_non_json_403_does_not_falsely_claim_invalid_token(self):
        import io
        from market.cloudflare import describe_http_error
        error=HTTPError('https://api.cloudflare.com',403,'Forbidden',{},io.BytesIO(b'<html>Access denied</html>'))
        message=describe_http_error(error,token='private')
        self.assertIn('非JSON',message)
        self.assertNotIn('<html>',message)
        self.assertIn('無法僅憑HTTP狀態判定',message)

    def test_api_request_sends_intentional_headers_without_printing_credentials(self):
        import io
        from unittest.mock import patch
        from market.cloudflare import api_request
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        def urlopen(req,timeout):
            self.assertEqual(req.get_header('Authorization'),'Bearer private')
            self.assertEqual(req.get_header('Accept'),'application/json')
            self.assertIn('HuaxiMarketJournal',req.get_header('User-agent'))
            return Response(b'{"success":true,"result":{}}')
        with patch('market.cloudflare.urllib.request.urlopen',side_effect=urlopen):
            self.assertTrue(api_request('GET','https://api.cloudflare.com','private')['success'])

    def test_token_verification_does_not_claim_pages_access(self):
        from market.cloudflare import token_status
        def request(method,url,token):
            self.assertEqual(url,'https://api.cloudflare.com/client/v4/user/tokens/verify')
            return {'success':True,'result':{'status':'active','id':'not-for-output'}}
        self.assertEqual(token_status('private',request),'active')

if __name__=='__main__':unittest.main()
