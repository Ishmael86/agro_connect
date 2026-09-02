import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

def get_admin_recipient_email():
    """Retrieve the primary administrative contact email."""
    return getattr(settings, 'CONTACT_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@agroconnect.com'))

def send_admin_support_ticket_email(request, ticket, message_text, is_reply=False):
    """
    Dispatches an instant email notification to the Administrator when a Farmer
    or Buyer creates a new support ticket or posts a reply message.
    """
    admin_recipient = get_admin_recipient_email()
    sender = ticket.user
    
    try:
        admin_ticket_url = request.build_absolute_uri(
            reverse('admin_ticket_detail', kwargs={'id': ticket.id})
        )
    except Exception:
        admin_ticket_url = None
        
    sender_name = sender.get_full_name() or sender.username
    if hasattr(sender, 'farmer_profile') and sender.farmer_profile.farm_name:
        sender_name += f" ({sender.farmer_profile.farm_name})"
        
    action_verb = "New Reply on" if is_reply else "New"
    subject = f"📬 [{action_verb} Support Ticket #{ticket.id}] {ticket.subject} - {sender_name}"
    
    plain_text = (
        f"Support Ticket Update - AgroConnect\n\n"
        f"Ticket #{ticket.id}: {ticket.subject}\n"
        f"Status: {ticket.get_status_display()} | Priority: {ticket.get_priority_display()}\n"
        f"From: {sender_name} ({sender.email})\n"
        f"Action: {'New reply posted' if is_reply else 'New ticket submitted'}\n\n"
        f"Message Content:\n{message_text}\n\n"
        f"Respond in Admin Panel: {admin_ticket_url or 'Admin Dashboard'}\n\n"
        f"---\nAgroConnect Admin Notification"
    )
    
    html_body = render_to_string('admin_panel/email_admin_support_alert.html', {
        'ticket': ticket,
        'sender': sender,
        'message_text': message_text,
        'is_reply': is_reply,
        'admin_ticket_url': admin_ticket_url
    })
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_recipient],
            reply_to=[sender.email] if sender.email else None
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        print(f"[AgroConnect] Admin support alert email sent to {admin_recipient} for ticket #{ticket.id}")
        logger.info(f"Admin support alert email sent to {admin_recipient} for ticket #{ticket.id}")
    except Exception as e:
        print(f"[AgroConnect ERROR] Failed to send admin support alert: {e}")
        logger.error(f"Failed to send admin support alert: {e}")

def send_user_support_reply_email(request, ticket, reply_message):
    """
    Dispatches an instant email notification to the Farmer or Buyer when the
    Administrator submits an official reply to their support ticket.
    """
    recipient = ticket.user
    if not recipient.email:
        return
        
    user_name = recipient.get_full_name() or recipient.username
    subject = f"💬 Re: [Support #{ticket.id}] {ticket.subject} - AgroConnect Response"
    
    try:
        if recipient.account_type == 'FARMER':
            ticket_url = request.build_absolute_uri(
                reverse('farmer_ticket_detail', kwargs={'ticket_id': ticket.id})
            )
        else:
            ticket_url = request.build_absolute_uri(reverse('buyer_help'))
    except Exception:
        ticket_url = None
        
    plain_text = (
        f"Hello {user_name},\n\n"
        f"AgroConnect Administration has replied to your support ticket #{ticket.id} ({ticket.subject}).\n\n"
        f"Official Response:\n{reply_message}\n\n"
        f"View ticket on your dashboard: {ticket_url or 'Dashboard'}\n\n"
        f"Best regards,\nAgroConnect Customer Care"
    )
    
    html_body = render_to_string('admin_panel/email_user_support_reply.html', {
        'ticket': ticket,
        'reply_message': reply_message,
        'ticket_url': ticket_url
    })
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email]
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        print(f"[AgroConnect] User support reply email sent to {recipient.email} for ticket #{ticket.id}")
        logger.info(f"User support reply email sent to {recipient.email} for ticket #{ticket.id}")
    except Exception as e:
        print(f"[AgroConnect ERROR] Failed to send user support reply email: {e}")
        logger.error(f"Failed to send user support reply email: {e}")

def send_chat_message_email_notification(request, conversation, message_obj):
    """
    Dispatches an email notification to the recipient when a buyer or farmer
    sends them a direct conversation message.
    """
    sender = message_obj.sender
    if sender == conversation.buyer:
        recipient_user = conversation.farmer.user if hasattr(conversation.farmer, 'user') else conversation.farmer
    else:
        recipient_user = conversation.buyer
    
    if not recipient_user or not getattr(recipient_user, 'email', None):
        return
        
    sender_name = sender.get_full_name() or sender.username
    if hasattr(sender, 'farmer_profile') and sender.farmer_profile.farm_name:
        sender_name = f"{sender.farmer_profile.farm_name} ({sender_name})"
        
    subject = f"💬 New Message from {sender_name} on AgroConnect"
    
    try:
        if getattr(recipient_user, 'account_type', None) == 'FARMER':
            chat_url = request.build_absolute_uri(
                reverse('farmer_messages') + f"?conv={conversation.id}"
            )
        else:
            chat_url = request.build_absolute_uri(
                reverse('buyer_messages') + f"?conv={conversation.id}"
            )
    except Exception:
        chat_url = None
        
    plain_text = (
        f"Hello {recipient_user.get_full_name() or recipient_user.username},\n\n"
        f"You have received a new message from {sender_name} on AgroConnect:\n\n"
        f"\"{message_obj.message}\"\n\n"
        f"View and reply to this conversation:\n{chat_url or 'Dashboard Messages'}\n\n"
        f"Best regards,\nAgroConnect Team"
    )
    
    html_body = render_to_string('accounts/email_chat_notification.html', {
        'sender': sender,
        'recipient': recipient_user,
        'message_text': message_obj.message,
        'chat_url': chat_url
    })
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_user.email]
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
        print(f"[AgroConnect] Chat email notification sent to {recipient_user.email} from {sender_name}")
        logger.info(f"Chat email notification sent to {recipient_user.email} from {sender_name}")
    except Exception as e:
        print(f"[AgroConnect ERROR] Failed to send chat email notification: {e}")
        logger.error(f"Failed to send chat email notification: {e}")
