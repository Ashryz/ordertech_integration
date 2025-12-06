import secrets

def post_init_generate_api_key(env):
    params = env['ir.config_parameter'].sudo()
    api_key_param = 'api.rest.key'

    if not params.get_param(api_key_param):
        new_key = secrets.token_hex(32)
        params.set_param(api_key_param, new_key)