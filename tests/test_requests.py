from config import application, providers
from pydoc import locate
from app.http.test_controllers.TestController import TestController
from cgi import MiniFieldStorage

from masonite.request import Request
from masonite.app import App
from masonite.routes import Get, Route
from masonite.helpers.routes import flatten_routes, get, group
from masonite.helpers.time import cookie_expire_time
from masonite.testsuite.TestSuite import generate_wsgi, TestSuite

WEB_ROUTES = flatten_routes([
    get('/test', 'Controller@show').name('test'),
    group('/a', [
        get('/account', 'Controller@show').name('a_account'),
    ])
])

wsgi_request = generate_wsgi()

class TestRequest:

    def setup_method(self):
        self.request = Request(wsgi_request).key(
            'NCTpkICMlTXie5te9nJniMj9aVbPM6lsjeq5iDZ0dqY=')

    def test_request_is_callable(self):
        """ Request should be callable """
        if callable(self.request):
            assert True


    def test_request_input_should_return_input_on_get_request(self):
        assert self.request.input('application') == 'Masonite'
        assert self.request.input('application', 'foo') == 'Masonite'

    def test_request_input_should_return_default_when_not_exists(self):
        assert self.request.input('foo', 'bar') == 'bar'

    def test_request_all_should_return_params(self):
        assert self.request.all() == {'application': 'Masonite'}
    
    def test_request_all_without_internal_request_variables(self):
        self.request.request_variables.update({'__token': 'testing', 'application': 'Masonite'})
        assert self.request.all() == {'__token': 'testing', 'application': 'Masonite'}
        assert self.request.all(internal_variables=False) == {'application': 'Masonite'}


    def test_request_has_should_return_bool(self):
        assert self.request.has('application') == True
        assert self.request.has('shouldreturnfalse') == False


    def test_request_has_should_accept_multiple_values(self):
        self.request.request_variables.update({'__token': 'testing', 'application': 'Masonite'})
        assert self.request.has('application') == True
        assert self.request.has('shouldreturnfalse') == False
        assert self.request.has('__token') == True
        assert self.request.has('__token', 'shouldreturnfalse') == False
        assert self.request.has('__token', 'application') == True
        assert self.request.has('__token', 'application', 'shouldreturnfalse') == False


    def test_request_set_params_should_return_self(self):
        assert self.request.set_params({'value': 'new'}) == self.request
        assert self.request.url_params == {'value': 'new'}


    def test_request_param_returns_parameter_set_or_false(self):
        self.request.set_params({'value': 'new'})
        assert self.request.param('value') == 'new'
        assert self.request.param('nullvalue') == False


    def test_request_appends_cookie(self):
        assert self.request.cookie('appendcookie', 'value') == self.request
        assert 'appendcookie' in self.request.environ['HTTP_COOKIE']


    def test_request_sets_and_gets_cookies(self):
        self.request.cookie('setcookie', 'value')
        assert self.request.get_cookie('setcookie') == 'value'


    def test_request_sets_expiration_cookie_2_months(self):
        self.request.cookies = []
        self.request.cookie('setcookie_expiration', 'value', expires='2 months')

        time = cookie_expire_time('2 months')

        assert self.request.get_cookie('setcookie_expiration') == 'value'
        assert 'Expires={0}'.format(time) in self.request.cookies[0][1]


    def test_delete_cookie(self):
        self.request.cookies = []
        self.request.cookie('delete_cookie', 'value')

        assert self.request.get_cookie('delete_cookie') == 'value'
        self.request.delete_cookie('delete_cookie')
        assert not self.request.get_cookie('delete_cookie')


    def test_delete_cookie_with_wrong_key(self):
        self.request.cookies = []
        self.request.cookie('cookie', 'value')
        self.request.key('wrongkey_TXie5te9nJniMj9aVbPM6lsjeq5iDZ0dqY=')
        assert self.request.get_cookie('cookie') is None


    def test_redirect_returns_request(self):
        assert self.request.redirect('newurl') == self.request
        assert self.request.redirect_url == '/newurl'


    def test_request_no_input_returns_false(self):
        assert self.request.input('notavailable') == False

    def test_request_mini_field_storage_returns_single_value(self):
        storages = {'test': [MiniFieldStorage('key', '1')]}
        self.request._set_standardized_request_variables(storages)
        assert self.request.input('test') == '1'

    def test_request_mini_field_storage_doesnt_return_brackets(self):
        storages = {'test[]': [MiniFieldStorage('key', '1')]}
        self.request._set_standardized_request_variables(storages)
        assert self.request.input('test') == '1'

    def test_request_mini_field_storage_index(self):
        storages = {'test[index]': [MiniFieldStorage('key', '1')]}
        self.request._set_standardized_request_variables(storages)
        assert self.request.input('test[index]') == '1'

    def test_request_mini_field_storage_with_dot_notation(self):
        storages = {'test[index]': [MiniFieldStorage('key', '1')]}
        self.request._set_standardized_request_variables(storages)
        assert self.request.input('test.index') == '1'

    def test_request_mini_field_storage_returns_a_list(self):
        storages = {'test': [MiniFieldStorage(
            'key', '1'), MiniFieldStorage('key', '2')]}
        self.request._set_standardized_request_variables(storages)
        assert self.request.input('test') == ['1', '2']

    def test_request_get_cookies_returns_cookies(self):
        assert self.request.get_cookies() == self.request.cookies


    def test_request_set_user_sets_object(self):
        assert self.request.set_user(object) == self.request
        assert self.request.user_model == object
        assert self.request.user() == object


    def test_request_loads_app(self):
        app = App()
        app.bind('Request', self.request)
        app.make('Request').load_app(app)

        assert self.request.app() == app
        assert app.make('Request').app() == app


    def test_request_gets_input_from_container(self):
        container = App()
        container.bind('Application', application)
        container.bind('Providers', providers)
        container.bind('WSGI', object)
        container.bind('Environ', wsgi_request)

        for provider in container.make('Providers').PROVIDERS:
            container.resolve(provider().load_app(container).register)

        container.bind('Response', 'test')
        container.bind('WebRoutes', [
            Get().route('url', None),
            Get().route('url/', None),
            Get().route('url/@firstname', None),
        ])

        container.bind('Response', 'Route not found. Error 404')

        for provider in container.make('Providers').PROVIDERS:
            located_provider = provider().load_app(container)

            container.resolve(provider().load_app(container).boot)

        assert container.make('Request').input('application') == 'Masonite'
        assert container.make('Request').all() == {'application': 'Masonite'}
        container.make('Request').environ['REQUEST_METHOD'] = 'POST'
        assert container.make('Request').environ['REQUEST_METHOD'] == 'POST'
        assert container.make('Request').input('application') == 'Masonite'


    def test_redirections_reset(self):
        app = App()
        app.bind('Request', self.request)
        app.bind('WebRoutes', WEB_ROUTES)
        request = app.make('Request').load_app(app)

        request.redirect('test')

        assert request.redirect_url == '/test'

        request.reset_redirections()

        assert request.redirect_url is False

        request.redirect_to('test')

        assert request.redirect_url == '/test'

        request.reset_redirections()

        assert request.redirect_url is False


    def test_request_has_subdomain_returns_bool(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        assert request.has_subdomain() is False
        assert request.subdomain is None

        request.environ['HTTP_HOST'] = 'test.localhost.com'

        request.header('TEST', 'set_this')
        assert request.header('HTTP_TEST') == 'set_this'

        request.header('TEST', 'set_this', http_prefix = None)
        assert request.header('TEST') == 'set_this'


    def test_redirect_compiles_url(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = '/test/url'

        assert request.compile_route_to_url(route) == '/test/url'


    def test_redirect_compiles_url_with_1_slash(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = '/'

        assert request.compile_route_to_url(route) == '/'
    
    def test_request_route_returns_url(self):
        app = App()
        app.bind('Request', self.request)
        app.bind('WebRoutes', [
            get('/test/url', None).name('test.url'),
            get('/test/url/@id', None).name('test.id')
        ])
        request = app.make('Request').load_app(app)

        assert request.route('test.url') == '/test/url'
        assert request.route('test.id', {'id': 1}) == '/test/url/1'

    def test_request_route_returns_full_url(self):
        app = App()
        app.bind('Request', self.request)
        app.bind('WebRoutes', [
            get('/test/url', None).name('test.url'),
            get('/test/url/@id', None).name('test.id')
        ])
        request = app.make('Request').load_app(app)

        assert request.route('test.url', full=True) == 'http://localhost/test/url'

    def test_redirect_compiles_url_with_multiple_slashes(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = 'test/url/here'

        assert request.compile_route_to_url(route) == '/test/url/here'


    def test_redirect_compiles_url_with_trailing_slash(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = 'test/url/here/'

        assert request.compile_route_to_url(route) == '/test/url/here/'


    def test_redirect_compiles_url_with_parameters(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = 'test/@id'
        params = {
            'id': '1',
        }

        assert request.compile_route_to_url(route, params) == '/test/1'


    def test_redirect_compiles_url_with_multiple_parameters(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = 'test/@id/@test'
        params = {
            'id': '1',
            'test': 'user',
        }


    def test_redirect_compiles_url_with_http(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        route = "http://google.com"

        assert request.compile_route_to_url(route) == 'http://google.com'


    def test_request_gets_correct_header(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        assert request.header('UPGRADE_INSECURE_REQUESTS') == '1'
        assert request.header('RAW_URI') == '/'
        assert request.header('NOT_IN') == None

    def test_request_sets_correct_header(self):
        app = App()
        app.bind('Request', self.request)
        request = app.make('Request').load_app(app)

        request.header('TEST', 'set_this')
        assert request.header('HTTP_TEST') == 'set_this'

        request.header('TEST', 'set_this', http_prefix = None)
        assert request.header('TEST') == 'set_this'


    def test_request_gets_all_headers(self):
        app = App()
        app.bind('Request', Request(wsgi_request))
        request = app.make('Request').load_app(app)

        request.header('TEST1', 'set_this_item')
        request.header('TEST2', 'set_this_item', http_prefix = None)
        assert request.get_headers() == [('HTTP_TEST1', 'set_this_item'), ('TEST2', 'set_this_item')]

    def test_request_sets_status_code(self):
        app = App()
        app.bind('Request', self.request)
        app.bind('StatusCode', '404 Not Found')
        request = app.make('Request').load_app(app)

        request.status('200 OK')
        assert request.get_status_code() == '200 OK'

    def test_request_sets_request_method(self):
        wsgi = generate_wsgi()
        wsgi['QUERY_STRING'] = '__method=PUT'
        request = Request(wsgi)

        assert request.has('__method')
        assert request.input('__method') == 'PUT'
        assert request.get_request_method() == 'PUT'
    
    def test_request_has_should_pop_variables_from_input(self):
        self.request.request_variables.update({'key1': 'test', 'key2': 'test'})
        self.request.pop('key1', 'key2')
        assert self.request.request_variables == {'application': 'Masonite'}
        self.request.pop('shouldnotexist')
        assert self.request.request_variables == {'application': 'Masonite'}
        self.request.pop('application')
        assert self.request.request_variables == {}
        
    def test_is_named_route(self):
        app = App()
        app.bind('Request', self.request)
        app.bind('WebRoutes', [
            get('/test/url', None).name('test.url'),
            get('/test/url/@id', None).name('test.id')
        ])
        request = app.make('Request').load_app(app)

        request.path = '/test/url'
        assert request.is_named_route('test.url')

        request.path = '/test/url/1'
        assert request.is_named_route('test.id', {'id': 1})

    def test_request_url_from_controller(self):
        app = App()
        app.bind('Request', self.request)
        app.bind('WebRoutes', [
            get('/test/url', 'TestController@show').name('test.url'),
            get('/test/url/@id', 'ControllerTest@show').name('test.id'),
            get('/test/url/controller/@id', TestController.show).name('test.controller'),
        ])

        request = app.make('Request').load_app(app)

        assert request.url_from_controller('TestController@show') == '/test/url'
        assert request.url_from_controller('ControllerTest@show', {'id': 1}) == '/test/url/1'
        assert request.url_from_controller(TestController.show, {'id': 1}) == '/test/url/controller/1'


    def test_contains_for_path_detection(self):
        self.request.path = '/test/path'
        assert self.request.contains('/test/*')        
        assert self.request.contains('/test/path')        
        assert not self.request.contains('/test/wrong')     

    def test_contains_for_path_with_digit(self):
        self.request.path = '/test/path/1'
        assert self.request.contains('/test/path/*')    
        assert self.request.contains('/test/path/*:int')   

    def test_contains_for_path_with_digit_and_wrong_contains(self):
        self.request.path = '/test/path/joe' 
        assert not self.request.contains('/test/path/*:int')    

    def test_contains_for_path_with_alpha_contains(self):
        self.request.path = '/test/path/joe' 
        assert self.request.contains('/test/path/*:string')    

    def test_contains_multiple_asteriks(self):
        self.request.path = '/dashboard/user/edit/1' 
        assert self.request.contains('/dashboard/user/*:string/*:int')
        
    def test_back_returns_correct_url(self):
        self.request.path = '/dashboard/create'
        self.request.back()
        assert self.request.redirect_url == '/dashboard/create'

        self.request.back(default='/home')
        assert self.request.redirect_url == '/home'

        self.request.request_variables = {'__back': '/login'}
        self.request.back(default='/home')
        assert self.request.redirect_url == '/login'
