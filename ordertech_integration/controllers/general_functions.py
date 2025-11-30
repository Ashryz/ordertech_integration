from odoo.http import request


API_KEY = 'bfr8sd73vcfd3e6a63d182f26cbca87f4f3723e0e'

def check_api_key():
    api_key = request.httprequest.headers.get('X-API-KEY')
    if api_key != API_KEY:
        return False
    return True

def valid_response(message=None, data=None, status=200):
    response_body = {
        key: value for key, value in {
            "message": message,
            "data": data
        }.items() if value is not None
    }
    return request.make_json_response(response_body,status=status)

def invalid_response(error,status=400):
    response_body = {
        'error': error,
    }
    return request.make_json_response(response_body, status=status)