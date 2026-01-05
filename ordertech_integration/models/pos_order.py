from  odoo import models, fields, api
import logging
import requests
import json
from odoo.http import request

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    ordertech_orderId = fields.Char()


    def action_pos_order_cancel(self):
        res = super(PosOrder, self).action_pos_order_cancel()
        self._send_ordertech_cancel_webhook()
        return res

    def _send_ordertech_cancel_webhook(self):
        instance = request.env.ref("ordertech_integration.default_ordertech_instance")
        if not instance or not instance.ordertech_token:
            _logger.error("OrderTech instance missing, order status sync skipped.")
            return False
        for order in self:
            if order.ordertech_orderId:
                url = f"{instance.url}/api/integrations/odoo/webhook/order-status"
                headers = {
                    'accept': '*/*',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {instance.ordertech_token}'
                }
                payload = json.dumps({
                    "order_id": order.id,
                    "status": 'cancelled',
                })
                try:
                    response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
                    if response.status_code != 201:
                        _logger.error(
                            "OrderTech update order status failed for order %s: %s ",
                            order.id, response.text,
                        )
                        continue
                    _logger.info("Successfully update order status for order %s", order.id)
                except Exception as e:
                    _logger.error(
                        "OrderTech API request error for order %s: %s",
                        order.id,
                        str(e),
                    )
