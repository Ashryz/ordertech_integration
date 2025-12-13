import json

from odoo import models, fields, api, _
import requests

from odoo.exceptions import UserError
from odoo.http import request


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_restaurant = fields.Boolean()
    is_branch = fields.Boolean()
    notes = fields.Char()
    slug = fields.Char()
    delivery_radius_km = fields.Integer()
    opening_time = fields.Float()
    closing_time = fields.Float()
    ordertech_tenantId = fields.Char()
    ordertech_tenant_branchId = fields.Char()

    @api.onchange('parent_id')
    def check_branch(self):
        for rec in self:
            if rec.parent_id:
                rec.is_branch = True
            else:
                rec.is_branch = False

    def float_to_hhmm(self, time_float):
        if time_float is None:
            return "00:00"
        hours = int(time_float)
        minutes = int(round((time_float - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    # @api.model_create_multi
    # def create(self, vals_list):
    #     companies = super(ResCompany, self).create(vals_list)
    #     for company in companies:
    #         if company.is_restaurant:
    #             company.create_tenant_api()
    #         if company.is_branch and company.parent_id:
    #             company.create_branch_api()
    #     return companies
    def sync_data_to_ordertech(self):
        for rec in self:
            if rec.is_restaurant and not rec.ordertech_tenantId:
                rec.create_tenant_api()
            elif rec.is_branch and rec.parent_id and  not rec.ordertech_tenant_branchId:
                rec.create_branch_api()
            else:
                raise UserError("There is not data to sync")
    def create_tenant_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not instance or not instance.exp_token:
            raise UserError("OrderTech instance is missing.")
        for company in self:
            url = f"{instance.url}/api/tenants"
            payload = json.dumps({
                # "odoo_company_id": company.id,
                "name": company.name,
                "phone": company.phone,
                "email": company.email,
                "openingTime": self.float_to_hhmm(company.opening_time),
                "closingTime": self.float_to_hhmm(company.closing_time),
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
                company.ordertech_tenantId = response_data.get("id")
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 201:
                    response_data = response.json()
                    company.ordertech_tenantId = response_data.get("id")
            else:
                raise UserError(f"Tenant create failed: {response.status_code} - {response.text}")

    def create_branch_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")
        if not instance or not instance.exp_token:
            raise UserError("OrderTech instance is missing.")
        for company in self:
            if not company.parent_id.ordertech_tenantId:
                raise UserError("Parent Restaurant has no linked OrderTech tenant (ordertech_tenantId).")
            url = f"{instance.url}/api/branches"
            payload = json.dumps({
                "name": company.name,
                "slug": company.slug,
                "tenantId": company.parent_id.ordertech_tenantId,
                "status": "open",
                "timezone": self.env.context.get('tz'),
                "addressLine1": company.street,
                "addressLine2": company.street2,
                "city": company.state_id.name,
                "region": company.city,
                "postalCode": company.zip,
                "countryCode": company.country_code,
                "phonePublic": company.phone,
                "email": company.email,
                "deliveryRadiusKm": company.delivery_radius_km,
                "notes": company.notes,
                "openingTime": self.float_to_hhmm(company.opening_time),
                "closingTime": self.float_to_hhmm(company.closing_time)
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
                company.ordertech_tenant_branchId = response_data.get("id")
                company.ordertech_tenantId = response_data.get("tenantId")
            elif response.status_code == 401:
                instance.refresh_tokens()
                headers['Authorization'] = f'Bearer {instance.exp_token}'
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e:
                    raise UserError(str(e))
                if response.status_code == 201:
                    response_data = response.json()
                    company.ordertech_tenant_branchId = response_data.get("id")
                    company.ordertech_tenantId = response_data.get("tenantId")
            else:
                raise UserError(f"Tenant Branch create failed: {response.status_code} - {response.text}")

    # def write(self, vals):
    #     res = super(ResCompany, self).write(vals)
    #     tenant_tracked_fields = {"name", "phone", "email", "opening_time", "closing_time"}
    #     branch_tracked_fields = {"name", "phone", "email", "opening_time", "closing_time", "slug", "street", "street2",
    #                              "state_id", "city", "zip", "delivery_radius_km", "notes"}
    #     for company in self:
    #         if company.is_restaurant:
    #             if any(field in vals for field in tenant_tracked_fields):
    #                 company.update_tenant_api()
    #         if company.is_branch and company.parent_id:
    #             if any(field in vals for field in branch_tracked_fields):
    #                 company.update_branch_api()
    #     return res

    def update_tenant_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")

        if not instance:
            raise UserError("OrderTech instance is missing.")
        for company in self:
            if not company.ordertech_tenantId:
                raise UserError("This company has no linked OrderTech tenant (ordertech_tenantId).")
            url = f"{instance.url}/api/tenants/{company.ordertech_tenantId}"
            payload = json.dumps({
                "name": company.name,
                "phone": company.phone,
                "email": company.email,
                "openingTime": self.float_to_hhmm(company.opening_time),
                "closingTime": self.float_to_hhmm(company.closing_time),
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
                raise UserError(f"Tenant update failed: {response.status_code} - {response.text}")

    def update_branch_api(self):
        instance = self.env.ref("ordertech_integration.default_ordertech_instance")

        if not instance:
            raise UserError("OrderTech instance is missing.")
        for company in self:
            if not company.ordertech_tenant_branchId:
                raise UserError("This company has no linked OrderTech tenant (ordertech_tenant_branchId).")
            url = f"{instance.url}/api/branches/{company.ordertech_tenant_branchId}"
            payload = json.dumps({
                "name": company.name,
                "slug": company.slug,
                "status": "open",
                "timezone":  self.env.context.get('tz'),
                "addressLine1": company.street,
                "addressLine2": company.street2,
                "city": company.state_id.name,
                "region": company.city,
                "postalCode": company.zip,
                "countryCode": company.country_code,
                "phonePublic":company.phone,
                "email": company.email,
                "deliveryRadiusKm": company.delivery_radius_km,
                "notes": company.notes,
                "openingTime": self.float_to_hhmm(company.opening_time),
                "closingTime": self.float_to_hhmm(company.closing_time)
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
                raise UserError(f"Tenant Branch update failed: {response.status_code} - {response.text}")

    def action_all_company_branches(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Branches'),
            'res_model': 'res.company',
            'domain': [('parent_id', '=', self.id)],
            'context': {
                'active_test': False,
                'default_parent_id': self.id,
            },
            'views': [[self.env.ref('base.view_company_tree').id, 'list'], [False, 'kanban'], [False, 'form']],
        }
