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
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            customer_list = [{
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "mobile": c.mobile,
                "email": c.email,
                "tags": [t.name for t in c.category_id],
                "company_id": [c.company_id.id, c.company_id.name] if c.company_id else None,
                "ordertech_tenantId": c.ordertech_tenantId,
                "address": {
                    "street": c.street,
                    "city": c.city,
                    "state_id": [c.state_id.id, c.state_id.name] if c.state_id else None,
                    "zip": c.zip,
                    "country_id": [c.country_id.id, c.country_id.name] if c.country_id else None,
                    "country_code": c.country_code,
                    "latitude": c.partner_latitude,
                    "longitude": c.partner_longitude
                }
            } for c in customers]

            return valid_response(
                message="Success",
                data={'webhookUrl':f"{base_url}/api/v1/webhooks/ordertech/customerId",
                    'customers': customer_list
                },
            )

        except Exception as e:
            _logger.exception("Error fetching customers api request")
            return invalid_response(
                error= str(e),
                status=500
            )

    @http.route('/api/v1/customer',type='http',methods=['POST'],auth='none',csrf=False)
    def create_customer(self):
        if not check_api_key():
            return invalid_response(
                error='Unauthorized',
                status=401
            )
        try:
            args = request.httprequest.data.decode()
            vals = json.loads(args)
        except Exception as e:
            return invalid_response(
                error=f"invalid Json type : {str(e)}"
            )
        required_fields = ['ordertech_customerId', 'name']
        missing_fields = [field for field in required_fields if not vals.get(field)]

        if missing_fields:
            return invalid_response(
                error= f"Missing required field(s): {', '.join(missing_fields)}"
            )

        company_id = vals.get('company_id')
        if company_id is not None:
            if not isinstance(company_id, int):
                return invalid_response(error="'company_id' must be an integer")
            company = request.env['res.company'].sudo().browse(company_id).exists()
            if not company:
                return invalid_response(error="Company not found, please enter correct id")

        address = vals.get('address', {})
        if address and not isinstance(address, dict):
            return invalid_response(error="'address' must be an object")

        state_id = address.get('state_id')
        if state_id is not None:
            if not isinstance(state_id, int):
                return invalid_response(error="'state_id' must be an integer")
            state = request.env['res.country.state'].sudo().browse(state_id).exists()
            if not state:
                return invalid_response(error="State not found, please enter correct id")

        country_id = address.get('country_id')
        if country_id is not None:
            if not isinstance(country_id, int):
                return invalid_response(error="'country_id' must be an integer")
            country = request.env['res.country'].sudo().browse(country_id).exists()
            if not country:
                return invalid_response(error="Country not found, please enter correct id")

        longitude = address.get('longitude')
        latitude = address.get('latitude')
        if (longitude is not None and latitude is None) or (longitude is None and latitude is not None):
            return invalid_response(error="'longitude' and 'latitude' must be provided together")
        if longitude is not None:
            if not isinstance(longitude, float):
                return invalid_response(error="'longitude' must be an float")
        if latitude is not None:
            if not isinstance(latitude, float):
                return invalid_response(error="'latitude' must be a float")

        customer_vals = {
            "ordertech_customerId": vals['ordertech_customerId'],
            "name": vals['name'],
            "phone": vals.get("phone"),
            "mobile": vals.get("mobile"),
            "email": vals.get("email"),
            "company_id": vals.get('company_id'),
            "country_id": vals.get('address',{}).get('country_id'),
            "state_id": vals.get('address', {}).get('state_id'),
            "city": vals.get('address', {}).get('city'),
            "street": vals.get('address', {}).get('street'),
            "zip": vals.get('address', {}).get('zip'),
            "partner_latitude": vals.get('address', {}).get('latitude'),
            "partner_longitude": vals.get('address', {}).get('longitude'),
        }
        try:
            customer = request.env['res.partner'].sudo().create(customer_vals)
            if customer:
                return valid_response(
                    message="Customer created successfully",
                    data={
                        "odoo_customer_id": customer.id,
                        "ordertech_customerId": customer.ordertech_customerId
                    },
                    status=201
                )
        except Exception as e:
            _logger.exception("Error create customers api request")
            return invalid_response(
                error=str(e),
                status=400
            )

    @http.route('/api/v1/customer/<int:customer_id>', type='http', methods=['PUT'], auth='none', csrf=False)
    def update_customer(self, customer_id):

        if not check_api_key():
            return invalid_response(
                error='Unauthorized',
                status=401
            )

        customer = request.env['res.partner'].sudo().browse(customer_id).exists()
        if not customer:
            return invalid_response(
                error="Customer not found",
                status=404
            )

        try:
            args = request.httprequest.data.decode()
            vals = json.loads(args)
        except Exception as e:
            return invalid_response(
                error=f"Invalid JSON type: {str(e)}",
                status=400
            )

        company_id = vals.get('company_id')
        if company_id is not None:
            if not isinstance(company_id, int):
                return invalid_response(error="'company_id' must be an integer")
            company = request.env['res.company'].sudo().browse(company_id).exists()
            if not company:
                return invalid_response(error="Company not found, please enter correct id")

        address = vals.get('address', {})
        if address and not isinstance(address, dict):
            return invalid_response(error="'address' must be an object")

        state_id = address.get('state_id')
        if state_id is not None:
            if not isinstance(state_id, int):
                return invalid_response(error="'state_id' must be an integer")
            state = request.env['res.country.state'].sudo().browse(state_id).exists()
            if not state:
                return invalid_response(error="State not found, please enter correct id")

        country_id = address.get('country_id')
        if country_id is not None:
            if not isinstance(country_id, int):
                return invalid_response(error="'country_id' must be an integer")
            country = request.env['res.country'].sudo().browse(country_id).exists()
            if not country:
                return invalid_response(error="Country not found, please enter correct id")

        longitude = address.get('longitude')
        latitude = address.get('latitude')
        if (longitude is not None and latitude is None) or (longitude is None and latitude is not None):
            return invalid_response(error="'longitude' and 'latitude' must be provided together")
        if longitude is not None:
            if not isinstance(longitude, float):
                return invalid_response(error="'longitude' must be an float")
        if latitude is not None:
            if not isinstance(latitude, float):
                return invalid_response(error="'latitude' must be a float")


        update_vals = {
            "name": vals.get("name"),
            "phone": vals.get("phone"),
            "mobile": vals.get("mobile"),
            "email": vals.get("email"),
            "company_id": vals.get("company_id"),
            "country_id": address.get("country_id"),
            "state_id": address.get("state_id"),
            "city": address.get("city"),
            "street": address.get("street"),
            "zip": address.get("zip"),
            "partner_latitude": address.get("latitude"),
            "partner_longitude": address.get("longitude"),
        }

        update_vals = {k: v for k, v in update_vals.items() if v is not None}

        try:
            customer.sudo().write(update_vals)

            return valid_response(
                message="Customer updated successfully",
                data={
                    "odoo_customer_id": customer.id,
                    "ordertech_customerId": customer.ordertech_customerId,
                    "updated_values": update_vals
                },
                status=200
            )

        except Exception as e:
            _logger.exception("Error updating customer from API")
            return invalid_response(
                error=str(e),
                status=400
            )

    @http.route('/api/v1/webhooks/ordertech/customerId', methods=["PUT"], type='http', auth='none', csrf=False)
    def update_customerId(self, *kwargs):
        if not check_api_key():
            return invalid_response(
                error='Unauthorized',
                status=401
            )
        try:
            args = request.httprequest.data.decode()
            vals = json.loads(args)
        except Exception as e:
            return invalid_response(
                error=f"invalid Json type : {str(e)}"
            )
        required_fields = ['odoo_customer_id', 'ordertech_customerId']
        missing_fields = [field for field in required_fields if not vals.get(field)]

        if missing_fields:
            return invalid_response(
                error=f"Missing required field(s): {', '.join(missing_fields)}"
            )
        customer = request.env['res.partner'].sudo().browse(vals.get('odoo_customer_id')).exists()
        if not customer:
            return invalid_response(
                error="customer not found",
                status=404
            )
        updated_vals = {
            "ordertech_customerId": vals.get('ordertech_customerId')
        }
        try:
            customer.sudo().write(updated_vals)
            return valid_response(
                message="customer updated ordertech_cusotmerId successfully",
                data={
                    "updated_values": updated_vals
                },
                status=200
            )
        except Exception as e:
            _logger.exception("Error updating customer from API")
            return invalid_response(
                error=str(e),
                status=400
            )
