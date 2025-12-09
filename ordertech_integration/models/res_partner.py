from odoo import models , fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ordertech_customerId = fields.Char()
