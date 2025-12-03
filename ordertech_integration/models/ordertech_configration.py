from odoo import models, fields


class OrderTechConfigration(models.Model):
    _name = 'ordertech.configration'
    _description = 'OrderTech Connector'


    name = fields.Char(string='Instance Name',required=True)
    url = fields.Char(string='OrderTech URL', required=True)
    email = fields.Char(string='Email', required=True)
    password = fields.Char(string='Password', required=True)
    exp_token = fields.Char()
    refresh_token = fields.Char()
    active = fields.Boolean(default=True)
    state = fields.Selection(selection=[
        ('unconnected', 'Unconnected'),
        ('connected', 'Connected')
    ],default='unconnected')