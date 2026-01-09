def classify(subject, body):
    text = (subject or "").lower() + " " + (body or "").lower()
    if any(k in text for k in ["invoice","inv","payment"]):
        return {"label":"invoice","confidence":0.6}
    if any(k in text for k in ["complaint","damaged","delay","late delivery","poor quality","issue"]):
        return {"label":"complaint","confidence":0.6}
    if any(k in text for k in ["rfq","quotation","quote","best price"]):
        return {"label":"quotation","confidence":0.6}
    if any(k in text for k in ["purchase order","po ","po-","order"]):
        return {"label":"purchase_order","confidence":0.6}
    return {"label":"inquiry","confidence":0.55}
