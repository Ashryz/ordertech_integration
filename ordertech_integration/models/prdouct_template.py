import json

import requests

from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    ordertech_group_id = fields.Many2one('addons.group')
    ordertech_itemId = fields.Char()
    ordertech_productId = fields.Char()
    company_id = fields.Many2one(
        'res.company', 'Company', index=True, default=lambda self: self.env.company.id)
    is_addons = fields.Boolean(default=False,compute='_check_addons_categ_ids',store=True)

    @api.depends('pos_categ_ids','pos_categ_ids.name')
    def _check_addons_categ_ids(self):
        for rec in self:
            if rec.pos_categ_ids:
                rec.is_addons = any(categ.name == 'addons' for categ in rec.pos_categ_ids)
            else:
                rec.is_addons = False
    def sync_data_to_ordertech(self):
        for rec in self:
            if rec.company_id and rec.is_addons and not rec.ordertech_itemId:
                rec.create_ordertech_addon_item()
            elif rec.company_id and not rec.ordertech_productId:
                rec.create_ordertech_product()
            else:
                raise UserError("There is not data to sync")

    def create_ordertech_addon_item(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        if not instance or not instance.exp_token:
            raise UserError("OrderTech instance is missing.")
        for item in self:
            if not item.company_id.ordertech_tenantId:
                raise UserError("Parent Restaurant has no linked OrderTech tenant (ordertech_tenantId).")

            url = f"{instance.url}/api/menu/addon-items/{item.company_id.ordertech_tenantId}"
            payload = json.dumps({
                "name_en": item.name,
                # "name_ar": "string",
                # "group_id": item.pos_categ_ids[0].ordertech_addonsId,
                "group_id": "e2922c24-ccb8-4689-ab4f-59379238e9a4",
                "source_product_id": item.id,
                "price_cents_base": item.list_price,
                "is_active": True,
                "sort_order": 0
            })
            headers = {
                'accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {instance.exp_token}'
            }
            # try:
            response = requests.request("POST", url, headers=headers, data=payload)
            print(response.text)
            # except Exception as e:
            #     raise UserError(str(e))
            if response.status_code == 201:
                response_data = response.json()
                print(response_data)
                item.ordertech_itemId = response_data.get("id")
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 201:
                    response_data = response.json()
                    print(response_data)
                    item.ordertech_itemId = response_data.get("id")
                else:
                    raise UserError(f"Tenant Addons-item create failed: {response.status_code} - {response.text}")
            else:
                raise UserError(f"Tenant Addons-item create failed: {response.status_code} - {response.text}")

    def create_ordertech_product(self):
        pass
        # instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        # if not instance or not instance.exp_token:
        #     raise UserError("OrderTech instance is missing.")
        # for item in self:
        #     if not item.company_id.ordertech_tenantId:
        #         raise UserError("Parent Restaurant has no linked OrderTech tenant (ordertech_tenantId).")
        #
        #     url = f"{instance.url}/api/menu/addon-items/{item.company_id.ordertech_tenantId}"
        #     payload = json.dumps({
        #         "name_en": item.name,
        #         # "name_ar": "string",
        #         # "group_id": item.pos_categ_ids[0].ordertech_addonsId,
        #         "group_id": "e2922c24-ccb8-4689-ab4f-59379238e9a4",
        #         "source_product_id": item.id,
        #         "price_cents_base": item.list_price,
        #         "is_active": True,
        #         "sort_order": 0
        #     })
        #     headers = {
        #         'accept': '*/*',
        #         'Content-Type': 'application/json',
        #         'Authorization': f'Bearer {instance.exp_token}'
        #     }
        #     try:
        #         response = requests.request("POST", url, headers=headers, data=payload)
        #     except Exception as e:
        #         raise UserError(str(e))
        #     if response.status_code == 201:
        #         response_data = response.json()
        #         item.ordertech_itemId = response_data.get("id")
        #     elif response.status_code == 401:
        #         instance.refresh_tokens()
        #         headers['Authorization'] = f'Bearer {instance.exp_token}'
        #         try:
        #             response = requests.request("POST", url, headers=headers, data=payload)
        #         except Exception as e:
        #             raise UserError(str(e))
        #         if response.status_code == 201:
        #             response_data = response.json()
        #             item.ordertech_itemId = response_data.get("id")
        #         else:
        #             raise UserError(f"Tenant Addons-item create failed: {response.status_code} - {response.text}")
        #     else:
        #         raise UserError(f"Tenant Addons-item create failed: {response.status_code} - {response.text}")
