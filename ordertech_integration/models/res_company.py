import json
import typing

from odoo import models, fields, api
import requests

from odoo.api import ValuesType
from odoo.exceptions import UserError
from odoo.http import request


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_restaurant = fields.Boolean()
    open_time = fields.Float(string='Opening Time')
    close_time = fields.Float(string='Closing Time')
    ordertech_tenants_id = fields.Char()


    def float_to_hhmm(self,time_float):
        if time_float is None:
            return "00:00"
        hours = int(time_float)
        minutes = int(round((time_float - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    @api.model_create_multi
    def create(self, vals_list):
        companies = super(ResCompany, self).create(vals_list)
        for company in companies:
            if company.is_restaurant:
                company.create_tenant_api()
        return companies

    def create_tenant_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not instance:
            raise UserError("OrderTech instance is missing.")
        for company in self:
            url = f"{instance.url}/api/tenants"
            payload = json.dumps({
                # "odoo_company_id": company.id,
                "name": company.name,
                "phone": company.phone,
                "email": company.email,
                "openingTime": self.float_to_hhmm(company.open_time),
                "closingTime": self.float_to_hhmm(company.close_time),
                # "tax_id": company.vat,
                # "logo": f"{base_url}/web/image/res.company/{company.id}/logo" if company.logo else None,
                # "website": company.website,
                # "default_currency": company.currency_id.name,
                # "country_code": company.country_code

            })
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {instance.exp_token}'
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload)
            except Exception as e:
                raise UserError(str(e))
            if response.status_code == 201:
                response_data = response.json()
                company.ordertech_tenants_id = response_data.get("id")
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 201:
                    response_data = response.json()
                    company.ordertech_tenants_id = response_data.get("id")
            else:
                raise UserError(f"Tenant update failed: {response.status_code} - {response.text}")


    def write(self, vals):
        res = super(ResCompany, self).write(vals)
        tracked_fields = {
            "name",
            "phone",
            "email",
            "open_time",
            "close_time",
            "vat",
            "logo",
            "website",
            "currency_id",
            "country_code",
        }
        for company in self:
            if company.is_restaurant:
                if any(field in vals for field in tracked_fields):
                    company.update_tenant_api()
        return res

    def update_tenant_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")

        if not instance:
            raise UserError("OrderTech instance is missing.")
        for company in self:
            if not company.ordertech_tenants_id:
                raise UserError("This company has no linked OrderTech tenant (ordertech_tenants_id).")
            url=f"{instance.url}/api/tenants/{company.ordertech_tenants_id}"
            payload = json.dumps({
                "name": company.name,
                "phone": company.phone,
                "email": company.email,
                "openingTime": self.float_to_hhmm(company.open_time),
                "closingTime": self.float_to_hhmm(company.close_time),
            })
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {instance.exp_token}'
            }
            try:
                response = requests.request("PUT",url,headers=headers,data=payload)
            except Exception as e:
                raise UserError(str(e))
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 200:
                    return True
            else:
                raise UserError(f"Tenant update failed: {response.status_code} - {response.text}")