from unittest import mock
from reboot_script.get_os import verify_os


def mocked_requests(*args, **kwargs):
    class MockRequestsResponse:
        def __init__(self, json_data, status_code, return_text):
            self.json_data = json_data
            self.status_code = status_code
            self.return_text = return_text

        def json(self):
            return self.json_data

        def status_code(self):
            return self.status_code

        def text(self):
            return self.return_text

    base_link = 'https://<REPLACE>.com/api/v1/server/hostname/dummy_servername'

    if args[0] == base_link and kwargs['auth'] == ('username', 'password'):
        correct_json = {'data': [{'os': 'Linux'}]}
        correct_status_code = 200
        text_not_needed = ""
        return MockRequestsResponse(correct_json, correct_status_code, text_not_needed)

    if args[0] == base_link and kwargs['auth'] == ('incorrect', 'password'):
        json_not_needed = {}
        unauthorized_status_code = 401
        unauthorized_text = '401 Unauthorized'
        return MockRequestsResponse(json_not_needed, unauthorized_status_code, unauthorized_text)


@mock.patch("requests.get", side_effect=mocked_requests)
def test_get_os_type_success(my_mock):
    os = verify_os.get_os_type('username', 'password', server_name='dummy_servername')
    assert os == 'Linux'
    my_mock.assert_called_with('https://<REPLACE>.com/api/v1/server/hostname/dummy_servername',
                               auth=('username', 'password'), headers={'Content-Type': 'application/json'}, verify=False)


@mock.patch("requests.get", side_effect=mocked_requests)
def test_get_os_type_unauthorized(my_mock):
    os = verify_os.get_os_type('incorrect', 'password', server_name='dummy_servername')
    assert os == '401 Unauthorized'
