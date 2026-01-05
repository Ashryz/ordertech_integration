import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { rpc } from "@web/core/network/rpc";

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        // Call original finalize logic
        await super._finalizeValidation();


        const order = this.currentOrder;
        if (!order) return;

        //  Call backend (safe, no CORS, no secrets in JS)
        try {
            await rpc("/pos/order/paid/webhook", {
                order_id: order.id,
            });
        } catch (error) {
            console.error("POS webhook failed:", error);
        }
//        // Backend order id is stored here after push
//        const backendId = order.backendId;
//        if (!backendId) {
//            console.warn("POS order not yet synced with backend");
//            return;
//        }
//
//        try {
//            await rpc("/pos/order/webhook", {
//                order_id: backendId,
//            });
//        } catch (err) {
//            console.error("Webhook call failed:", err);
//        }
    },
});
