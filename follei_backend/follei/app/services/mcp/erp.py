def get_invoice(invoice_id: str, customer_id: str | None = None) -> dict:
    return {"invoice": {"id": invoice_id, "customer_id": customer_id, "amount": 5000, "status": "paid"}}


def update_payment(invoice_id: str, payment_amount: float, payment_method: str) -> dict:
    return {"invoice_id": invoice_id, "payment_amount": payment_amount, "payment_method": payment_method, "updated": True, "new_balance": 0}
