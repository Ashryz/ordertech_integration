from odoo.http import request
import secrets


def get_api_key():
    params = request.env['ir.config_parameter'].sudo()
    saved_key = params.get_param('api.rest.key')
    if not saved_key:
        saved_key = secrets.token_hex(32)
        params.set_param('api.rest.key', saved_key)
    return saved_key

def check_api_key():
    request_key = request.httprequest.headers.get('X-API-KEY')
    saved_key = get_api_key()
    return request_key == saved_key

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