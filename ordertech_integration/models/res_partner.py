import json

import requests

from odoo import models , fields, api
from odoo.exceptions import UserError
from bs4 import BeautifulSoup


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ordertech_customerId = fields.Char()
    ordertech_tenantId = fields.Char(related='company_id.ordertech_tenantId')

    def default_get(self, default_fields):
        defaults = super().default_get(default_fields)
        if not defaults.get('parent_id'):
            defaults['company_id'] = self.env.company.id
        return defaults
    def sync_data_to_ordertech(self):
        for rec in self:
            if rec.company_id and rec.company_id.is_restaurant and not rec.ordertech_customerId:
                rec.create_tenant_customer_api()
            else:
                raise UserError("There is not data to sync")
    # @api.model_create_multi
    # def create(self, vals_list):
    #     partners = super(ResPartner, self).create(vals_list)
    #     for partner in partners:
    #         if partner.company_id and partner.company_id.is_restaurant:
    #             partner.create_tenant_customer_api()
    #     return partners

    def create_tenant_customer_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        if not instance:
            raise UserError("OrderTech instance is missing.")
        for partner in self:
            if not partner.ordertech_tenantId:
                raise UserError("Customer Company has no linked OrderTech tenant yet.")
            url = f"{instance.url}/api/customers/tenant/{partner.ordertech_tenantId}"
            payload = json.dumps({
                "full_name": partner.name,
                "phone_e164": partner.phone,
                "email": partner.email,
                "language": partner.lang,
                "notes": BeautifulSoup(partner.comment, "html.parser").get_text().strip() if partner.comment else None,
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
                partner.ordertech_customerId = response_data.get("id")
                partner.ordertech_tenantId = response_data.get("tenantId")
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 201:
                    response_data = response.json()
                    partner.ordertech_customerId = response_data.get("id")
                    partner.ordertech_tenantId = response_data.get("tenantId")

            else:
                raise UserError(f"Tenant Customer create failed: {response.status_code} - {response.text}")

    # def write(self, vals):
    #     res = super(ResPartner, self).write(vals)
    #     partner_tracked_fields = {"name", "phone", "email", "lang", "notes"}
    #     for partner in self:
    #         if partner.company_id and partner.company_id.is_restaurant:
    #             if any(field in vals for field in partner_tracked_fields):
    #                 partner.update_tenant_customer_api()
    #     return res

    def update_tenant_customer_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        if not instance:
            raise UserError("OrderTech instance is missing.")
        for partner in self:
            if not partner.ordertech_tenantId:
                raise UserError("Customer Company has no linked OrderTech tenant yet.")
            url = f"{instance.url}/api/customers/{partner.ordertech_customerId}/tenant/{partner.ordertech_tenantId}"
            payload = json.dumps({
                "full_name": partner.name,
                "phone_e164": partner.phone,
                "email": partner.email,
                "language": partner.lang,
                "notes": BeautifulSoup(partner.comment, "html.parser").get_text().strip() if partner.comment else None,
            })
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {instance.exp_token}'
            }
            try:
                response = requests.request("PUT", url, headers=headers, data=payload)
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
                raise UserError(f"Tenant Customer update failed: {response.status_code} - {response.text}")
