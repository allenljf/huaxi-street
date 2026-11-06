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
        with self.assertRaises(HTTPError):configure_project('a'*32,'hidden','huaxi-street',request)

    def test_invalid_project_name_rejected_before_any_request(self):
        with self.assertRaises(ValueError):configure_project('a'*32,'hidden','bad;name')

if __name__=='__main__':unittest.main()
