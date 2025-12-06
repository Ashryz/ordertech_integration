import json
import logging

from odoo import http
from odoo.http import request

from .general_functions import valid_response, invalid_response, check_api_key

_logger = logging.getLogger(__name__)

class ResCompany(http.Controller):

    @http.route('/api/v1/restaurants',type='http',methods=['GET'],auth='none',csrf=False)
    def get_all_restaurants(self):
        if not check_api_key():
            return invalid_response(
                error='Unauthorized: you have no permission to access these data!',
                status=401
            )

        try:
            restaurants = request.env['res.company'].sudo().search([('is_restaurant', '=', True)])
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            restaurant_list = [{
                "id": r.id,
                "name": r.name,
                "vat": r.vat,
                "country_id": [r.country_id.id, r.country_id.name],
                "country_code": r.country_id.code,
                "currency_id": [r.currency_id.id, r.currency_id.name],
                "phone": r.phone,
                "email": r.email,
                "website": r.website,
                "logo": f"{base_url}/web/image/res.company/{r.id}/logo" if r.logo else None,
                "open_time": r.open_time,
                "close_time": r.close_time
            } for r in restaurants ]

            return valid_response(
                message="Success",
                data={'restaurants': restaurant_list},
            )

        except Exception as e:
            _logger.exception("Error fetching customers api request")
            return invalid_response(
                error=str(e),
                status=500
            )