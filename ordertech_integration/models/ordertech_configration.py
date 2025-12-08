from odoo import models, fields, _
import requests
import json

from odoo.exceptions import UserError, ValidationError


class OrderTechConfigration(models.Model):
    _name = 'ordertech.configration'
    _description = 'OrderTech Connector'


    name = fields.Char(string='Instance Name',required=True)
    url = fields.Char(string='OrderTech URL', required=True)
    email = fields.Char(string='Email')
    password = fields.Char(string='Password')
    exp_token = fields.Char()
    refresh_token = fields.Char()
    active = fields.Boolean(default=True)

    def action_ordertech_connect(self):
        for rec in self:
            if rec.url and rec.email and rec.password:
                url = f"{rec.url}/api/auth/signin"

                payload = json.dumps({
                    "email": rec.email,
                    "password": rec.password
                })
                headers = {
                    'Content-Type': 'application/json'
                }
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e :
                    raise UserError(str(e))

                if response.status_code == 200:
                    response_data = response.json()
                    rec.exp_token = response_data.get('access_token')
                    rec.refresh_token = response_data.get('refresh_token')

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'success',
                            'message': _("Credentials look good!"),
                            'next': {'type': 'ir.actions.client',
                                     'tag':'soft_reload'},
                        }
                    }
            else:
                raise ValidationError(_('You should provide email , password to connect order tech'))

    def refresh_tokens(self):
        for rec in self:
            if rec.url and rec.refresh_token:
                url = f"{rec.url}/api/auth/refresh"
                payload = json.dumps({
                    "refresh_token": rec.refresh_token
                })
                headers = {
                    'Content-Type': 'application/json'
                }
                try:
                    response = requests.request("POST", url, headers=headers, data=payload)
                except Exception as e :
                    raise UserError(str(e))

                if response.status_code == 200:
                    response_data = response.json()
                    rec.exp_token = response_data.get('access_token')
                    rec.refresh_token = response_data.get('refresh_token')