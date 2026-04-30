from app.ai.email_intelligence import AnalysisResult


def generate_support_reply(
    *,
    customer_name: str,
    subject: str,
    message: str,
    analysis: AnalysisResult,
) -> str:
    greeting_name = customer_name.split()[0] if customer_name else "there"
    intent_line = {
        "Complaint": "I understand this has been frustrating, and I’m sorry for the experience.",
        "Refund": "I understand you’re looking for help with a refund, and I’ll make this clear and simple.",
        "Delivery Issue": "I understand the delivery concern and will help get this checked quickly.",
        "Product Inquiry": "Thank you for your interest. I’m happy to help with the product details.",
        "Technical Issue": "I understand you’re running into a technical issue, and I’ll help you move forward.",
        "Feedback": "Thank you for sharing your feedback with us.",
    }.get(analysis.category, "Thank you for contacting our support team.")

    priority_line = (
        "I’ve marked this as a high-priority case for faster handling."
        if analysis.priority in {"High", "Critical"}
        else "I’ve reviewed the details and will help with the next steps."
    )

    return (
        f"Hi {greeting_name},\n\n"
        f"{intent_line} {priority_line}\n\n"
        "We have reviewed your message and will take the appropriate action based on the details provided. "
        "If we need any additional information, we will contact you right away.\n\n"
        "Thank you for your patience,\n"
        "Customer Support Team"
    )


def generate_auto_reply(*, customer_name: str, analysis: AnalysisResult) -> str:
    greeting_name = customer_name.split()[0] if customer_name else "there"
    if analysis.category == "Feedback":
        message = "Thank you for your feedback. We appreciate you taking the time to share your experience with us."
    else:
        message = "Thank you for your message. We appreciate your interest and have received your query."

    return (
        f"Hi {greeting_name},\n\n"
        f"{message}\n\n"
        "Your message has been recorded successfully. If any follow-up is needed, our support team will reach out.\n\n"
        "Best regards,\n"
        "Customer Support Team"
    )
