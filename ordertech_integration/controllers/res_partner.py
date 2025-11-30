import json
import logging

from odoo import http
from odoo.http import request

from .general_functions import valid_response, invalid_response, check_api_key

_logger = logging.getLogger(__name__)


class ResPartner(http.Controller):

    @http.route('/api/v1/customers', type='http', methods=['GET'], auth='none', csrf=False)
    def get_all_customers(self):

        if not check_api_key():
            return invalid_response(
                error='Unauthorized: you have no permission to access these data!',
                status=401
            )
        try:
            customers = request.env['res.partner'].sudo().search([('customer_rank', '>', 0)])
            customer_list = [{
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "mobile": c.mobile,
                "email": c.email,
                "tags": [t.name for t in c.category_id],
                "company": [c.company_id.id, c.company_id.name] if c.company_id else None,
                "address": {
                    "street": c.street,
                    "city": c.city,
                    "state": [c.state_id.id, c.state_id.name] if c.state_id else None,
                    "zip": c.zip,
                    "country": [c.country_id.id, c.country_id.name] if c.country_id else None,
                    "country_code": c.country_code,
                    "latitude": c.partner_latitude,
                    "longitude": c.partner_longitude
                }
            } for c in customers]

            return valid_response(
                message="Success",
                data={'customers': customer_list},
            )

        except Exception as e:
            _logger.exception("Error fetching customers api request")
            return invalid_response(
                error= str(e),
            )

    @http.route('/api/v1/customer',type='http',methods=['POST'],auth='none',csrf=False)
    def create_customer(self):
        if not check_api_key():
            return invalid_response(
                error='Unauthorized',
                status=401
            )
        args = request.httprequest.data.decode()
        vals = json.loads(args)

        required_fields = ['ordertech_customer_id', 'name']
        missing_fields = [field for field in required_fields if not vals.get(field)]

        if missing_fields:
            return invalid_response(
                error= f"Missing required field(s): {', '.join(missing_fields)}"
            )
        print (vals)
