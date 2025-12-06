import json

from odoo import models, fields, api
import requests

from odoo.exceptions import UserError


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
        instance = self.env['ordertech.configration'].sudo().search([], limit=1)
        if instance:
            for company in self:
                url = f"{instance.url}/api/tenants"
                payload = json.dumps({
                    "name": company.name,
                    "phone": company.phone,
                    "email": company.email,
                    "openingTime": self.float_to_hhmm(company.open_time),
                    "closingTime": self.float_to_hhmm(company.close_time)
                })
                headers = {
                    'accept': '*/*',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {instance.exp_token}'
                }
                print(headers)
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                    print(response.status_code, response.text)
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
                    raise UserError(response.text)