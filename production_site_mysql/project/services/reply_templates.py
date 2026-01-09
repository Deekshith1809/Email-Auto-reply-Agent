def render(intent, sender_email, subject, body):
    name = (sender_email or "there").split("@")[0].replace("."," ").title()
    if intent == "invoice":
        return f"Hi {name},\n\nThanks for the invoice. Our finance team will verify and process it within 2–3 business days.\n\nBest regards,\nOperations"
    if intent == "complaint":
        return f"Hi {name},\n\nSorry for the inconvenience. We've logged your complaint and will update you with a resolution/ETA within 24 hours.\n\nRegards,\nSupport"
    if intent == "purchase_order":
        return f"Hi {name},\n\nThanks for the PO. We have started processing and will share confirmation and ship date shortly.\n\nRegards,\nOrder Management"
    if intent == "quotation":
        return f"Subject: Re: {subject}\n\nDear {name},\n\nThank you for your inquiry regarding 300 units. We will prepare a quotation with best price and delivery schedule and send it to you shortly.\n\nSincerely,\nSales"
    return f"Hi {name},\n\nThanks for reaching out. Please share quantity and timeline so we can tailor the proposal.\n\nRegards,\nSales"
