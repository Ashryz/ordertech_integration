import json

import requests

from odoo import fields, models, api
from odoo.exceptions import UserError


class AddonsGroup(models.Model):
    _name = 'addons.group'
    _description = 'Addons Group'

    name = fields.Char(string='Name',translate=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    slug = fields.Char()
    limit_min = fields.Integer()
    limit_max = fields.Integer()
    ordertech_groupId = fields.Char()

    def sync_data_to_ordertech(self):
        for rec in self:
            if rec.company_id and not rec.ordertech_groupId:
                rec.create_ordertech_addons_group()
            else:
                raise UserError("There is not data to sync")

    def create_ordertech_addons_group(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        if not instance or not instance.exp_token:
            raise UserError("OrderTech instance is missing.")
        for group in self:
            if not group.company_id.ordertech_tenantId:
                raise UserError("Parent Restaurant has no linked OrderTech tenant (ordertech_tenantId).")
            url = f"{instance.url}/api/menu/addon-groups/{group.company_id.ordertech_tenantId}"
            payload = json.dumps({
                "name_en": group.with_context(lang='en_US').name,
                # "name_ar": "string",
                "slug": group.slug,
                "limit_min": group.limit_min,
                "limit_max": group.limit_max,
                "is_required": True,
                "sort_order": 0
            })
            # print(payload)
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
                group.ordertech_groupId = response_data.get("id")
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 201:
                    response_data = response.json()
                    group.ordertech_groupId = response_data.get("id")
            else:
                raise UserError(f"Tenant Addons-group create failed: {response.status_code} - {response.text}")
