"""Partner connection and management routes."""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import uuid

from ..extensions import db, limiter
from ..middleware.auth import token_required
from ..models.user import User
from ..services.email_service import send_partner_request, send_partner_accepted
from ..services.notification_service import NotificationService

# Import PartnerConnection and RememberedPartner models
# These will need to be created based on the migrations
from sqlalchemy import or_
# Import Compatibility model and calculator
from ..models.compatibility import Compatibility
from ..compatibility.calculator import calculate_compatibility
from ..models.profile import Profile
# Import Partner models
from ..models.partner import PartnerConnection, RememberedPartner

partners_bp = Blueprint('partners', __name__, url_prefix='/api/partners')


@partners_bp.route('/connect', methods=['POST'])
@token_required
@limiter.limit("10 per hour")
def create_connection_request(current_user_id):
    """
    Create a partner connection request (FR-55).
    
    Expected payload:
    {
        "recipient_email": "partner@example.com"
    }
    """
    try:
        data = request.get_json()
        
        # Requester is the authenticated user
        requester_id = current_user_id
        recipient_email = data.get('recipient_email')
        
        if not requester_id or not recipient_email:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if requester exists
        # Cast to UUID for query safety (SQLAlchemy with SQLite strictness)
        try:
            requester_uuid = uuid.UUID(str(requester_id))
        except ValueError:
            return jsonify({'error': 'Invalid requester_user_id format'}), 400

        requester = User.query.filter_by(id=requester_uuid).first()
        if not requester:
            return jsonify({'error': 'Requester not found'}), 404
        
        # Generate connection token
        connection_token = str(uuid.uuid4())
        
        # Check if recipient exists
        recipient = User.query.filter_by(email=recipient_email).first()
        recipient_id = recipient.id if recipient else None
        
        # Check for existing active connections
        # We need to check both directions if we know the recipient_id
        # If we only know email, we check connections to that email
        
        # Check for existing active connections
        # We need to check both directions:
        # 1. I (requester) already sent to them (by email or user_id)
        # 2. They already sent to me (need to find them first)

        # Build query conditions
        conditions = [
            # Case 1: I sent request to their email
            (PartnerConnection.requester_user_id == requester_uuid) &
            (PartnerConnection.recipient_email == recipient_email)
        ]

        # If recipient exists as a user, add more precise checks
        if recipient_id:
            conditions.extend([
                # Case 2: I sent request to their user_id
                (PartnerConnection.requester_user_id == requester_uuid) &
                (PartnerConnection.recipient_user_id == recipient_id),
                # Case 3: They sent request to me
                (PartnerConnection.requester_user_id == recipient_id) &
                (PartnerConnection.recipient_user_id == requester_uuid)
            ])
        else:
            # Recipient doesn't exist yet - check if any user with that email sent us a request
            # This handles the case where someone invited us before we had an account
            # We look for connections where:
            # - The requester's email matches the recipient_email we're trying to invite
            # - AND we are the recipient
            # This requires joining with users table or a subquery
            # Note: User is already imported at module level

            # Find if there's a user with the target email who sent us a request
            subquery = db.session.query(User.id).filter(User.email == recipient_email).scalar_subquery()
            conditions.append(
                (PartnerConnection.requester_user_id == subquery) &
                (PartnerConnection.recipient_user_id == requester_uuid)
            )

        existing_query = PartnerConnection.query.filter(or_(*conditions))

        existing_connections = existing_query.filter(
            PartnerConnection.status.in_(['pending', 'accepted'])
        ).all()
        
        for conn in existing_connections:
            if conn.status == 'accepted':
                return jsonify({'error': 'You are already connected to this user'}), 400
            
            if conn.status == 'pending':
                if str(conn.requester_user_id) == str(requester_id):
                    return jsonify({'error': 'You have already sent a request to this user'}), 400
                else:
                    return jsonify({'error': 'You have a pending request from this user. Please check your received requests.'}), 400

        # Create connection request
        connection = PartnerConnection(
            requester_user_id=requester_uuid,
            recipient_email=recipient_email,
            recipient_user_id=recipient_id,
            status='pending',
            connection_token=connection_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1)  # FR-56: 1 day expiry
        )
        
        db.session.add(connection)
        db.session.commit()
        
        # Send email notification
        request_url = "https://getattuned.app/connectionRequestsPage"
        send_partner_request(
            recipient_email=recipient_email,
            requester_name=requester.display_name or "A user",
            request_url=request_url
        )
        
        # Send push notification if recipient exists and has FCM token
        if recipient_id:
            try:
                push_result = NotificationService.send_partner_invitation(
                    recipient_user_id=str(recipient_id),
                    sender_user_id=str(requester_uuid),
                    sender_name=requester.display_name or "Someone",
                    invitation_id=connection.id
                )
                if push_result.get('success'):
                    logger.info(f"Push notification sent for connection {connection.id}")
                else:
                    logger.info(f"Push notification skipped for connection {connection.id}: {push_result.get('reason')}")
            except Exception as push_error:
                logger.warning(f"Push notification failed (non-fatal): {push_error}")
        
        logger.info(f"Connection request created: {connection.id}")
        
        return jsonify({
            'success': True,
            'connection': connection.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Connection request failed: {str(e)}")
        return jsonify({'error': 'Failed to create connection'}), 500


@partners_bp.route('/connections/<connection_id>/accept', methods=['POST'])
@token_required
def accept_connection(current_user_id, connection_id):
    """
    Accept a partner connection request (FR-57).
    
    Expected payload:
    {
        "recipient_user_id": "uuid" (Optional, extracted from token if missing)
    }
    """
    try:
        # We can use current_user_id as the rightful recipient
        accepted_by_user_id = current_user_id
        
        # Override recipient_id with authenticated user to ensure security
        recipient_id = str(accepted_by_user_id)
        
        # Validate format if provided
        if recipient_id:
            try:
                uuid.UUID(recipient_id)
            except ValueError:
                return jsonify({'error': 'Invalid recipient_user_id format'}), 400
        
        # Validate connection_id format (it's an integer in the DB model, but route treats it as string?)
        # Wait, in the model `id` is Integer. So `connection_id` passed in URL must be castable to int.
        try:
            connection_id_int = int(connection_id)
        except ValueError:
             return jsonify({'error': 'Invalid connection_id format'}), 400

        connection = PartnerConnection.query.filter_by(id=connection_id_int).first()

        if not connection:
            return jsonify({'error': 'Connection not found'}), 404

        # CRITICAL: Verify caller is the intended recipient (IDOR protection)
        if connection.recipient_user_id and str(connection.recipient_user_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        # Fallback to DB if recipient_id not provided
        if not recipient_id:
            if connection.recipient_user_id:
                recipient_id = str(connection.recipient_user_id)
            else:
                return jsonify({'error': 'Missing recipient_user_id (and not found in record)'}), 400
        
        # Check if already accepted
        if connection.status == 'accepted':
             return jsonify({
                'message': 'Connection already accepted',
                'connection': connection.to_dict()
             }), 200

        # Check if expired
        # Ensure safe comparison between naive and aware datetimes
        expires_at = connection.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            connection.status = 'expired'
            db.session.commit()
            return jsonify({'error': 'Connection request expired'}), 410
        
        # Accept connection
        connection.status = 'accepted'
        connection.recipient_user_id = recipient_id
        
        # Add to remembered partners for both users
        # Note: RememberedPartner.user_id and partner_user_id are UUIDs, but PartnerConnection stores strings.
        # We must cast strings to UUIDs.
        
        # For Requester
        requester_uuid = uuid.UUID(str(connection.requester_user_id))
        recipient_uuid = uuid.UUID(str(recipient_id))
        
        # Check if already exists (idempotency)
        if not RememberedPartner.query.filter_by(user_id=requester_uuid, partner_user_id=recipient_uuid).first():
            rp1 = RememberedPartner(
                user_id=requester_uuid,
                partner_user_id=recipient_uuid,
                partner_name=connection.recipient_display_name or connection.recipient_email,
                partner_email=connection.recipient_email,
                last_played_at=datetime.now(timezone.utc)
            )
            db.session.add(rp1)
        
        # For Recipient
        # Fetch requester details for recipient's remembered partner entry
        requester = User.query.filter_by(id=requester_uuid).first()
        
        # Check if already exists (idempotency)
        if not RememberedPartner.query.filter_by(user_id=recipient_uuid, partner_user_id=requester_uuid).first():
            rp2 = RememberedPartner(
                user_id=recipient_uuid,
                partner_user_id=requester_uuid,
                partner_name=connection.requester_display_name or "Partner",
                partner_email=requester.email if requester else "Unknown",
                last_played_at=datetime.now(timezone.utc)
            )
            db.session.add(rp2)
            
        db.session.commit()

        # --- TRIGGER COMPATIBILITY CALCULATION ---
        try:
            # Fetch profiles for both users
            requester_profile = Profile.query.filter_by(user_id=requester_uuid).order_by(Profile.created_at.desc()).first()
            recipient_profile = Profile.query.filter_by(user_id=recipient_uuid).order_by(Profile.created_at.desc()).first()
            
            if requester_profile and recipient_profile:
                logger.info(f"Calculating compatibility for {requester_uuid} and {recipient_uuid}")
                
                # Prepare profile data for calculator
                profile_a_data = requester_profile.to_dict()
                profile_b_data = recipient_profile.to_dict()
                
                # Calculate scores
                result = calculate_compatibility(profile_a_data, profile_b_data)
                
                # Determine ordered IDs for storage (low ID first)
                if requester_profile.id < recipient_profile.id:
                    p1_id, p2_id = requester_profile.id, recipient_profile.id
                else:
                    p1_id, p2_id = recipient_profile.id, requester_profile.id
                
                # Check for existing record
                compat_record = Compatibility.query.filter_by(player_a_id=p1_id, player_b_id=p2_id).first()
                
                if not compat_record:
                    compat_record = Compatibility(
                        player_a_id=p1_id,
                        player_b_id=p2_id
                    )
                
                # Update record
                compat_record.overall_score = float(result['overall_compatibility']['score']) / 100.0
                compat_record.overall_percentage = int(result['overall_compatibility']['score'])
                compat_record.interpretation = result['overall_compatibility']['interpretation']
                compat_record.breakdown = result['breakdown']
                compat_record.mutual_activities = result['mutual_activities']
                compat_record.growth_opportunities = result['growth_opportunities']
                compat_record.mutual_truth_topics = result['mutual_truth_topics']
                compat_record.blocked_activities = result['blocked_activities']
                compat_record.boundary_conflicts = result['boundary_conflicts']
                compat_record.calculation_version = result['compatibility_version']
                compat_record.created_at = datetime.now(timezone.utc)
                
                db.session.add(compat_record)
                db.session.commit()
                logger.info(f"Compatibility calculated: {compat_record.overall_percentage}%")
                
            else:
                 logger.warning("Could not calculate compatibility: One or both profiles missing")

        except Exception as calc_error:
            # Don't fail the connection acceptance if calculation fails
            logger.error(f"Compatibility calculation failed: {calc_error}")
            db.session.rollback()  # Rollback only calculation part if needed, but connection was already committed above logic check.
            # Actually, `db.session.commit()` was called at line 236. So we are in a new transaction implicitly or need to manage it.
            # Best to keep it separate.

            # Best to keep it separate.
            
        # Send acceptance email
        if requester:
            accepted_by_name = "A user"
            # We need the acceptor's name (current user)
            acceptor = User.query.get(accepted_by_user_id)
            if acceptor:
                accepted_by_name = acceptor.display_name or acceptor.email
            
            send_partner_accepted(
                recipient_email=requester.email,
                partner_name=accepted_by_name,
                user_name=requester.display_name or "Love"
            )
            
            # Send push notification to requester
            try:
                push_result = NotificationService.send_invitation_accepted(
                    requester_user_id=str(requester_uuid),
                    acceptor_user_id=str(recipient_uuid),
                    acceptor_name=accepted_by_name
                )
                if push_result.get('success'):
                    logger.info(f"Acceptance push notification sent to user {requester_uuid}")
                else:
                    logger.info(f"Acceptance push notification skipped: {push_result.get('reason')}")
            except Exception as push_error:
                logger.warning(f"Push notification failed (non-fatal): {push_error}")
        return jsonify({
            'success': True,
            'connection': connection.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Accept connection failed: {str(e)}")
        return jsonify({'error': 'Failed to accept connection'}), 500


@partners_bp.route('/connections/<connection_id>/decline', methods=['POST'])
@token_required
def decline_connection(current_user_id, connection_id):
    """
    Decline a partner connection request (FR-57).
    """
    try:
        # Validate connection_id format (it's an integer in the DB model)
        try:
            connection_id_int = int(connection_id)
        except ValueError:
            return jsonify({'error': 'Invalid connection_id format'}), 400

        connection = PartnerConnection.query.filter_by(id=connection_id_int).first()
        
        if not connection:
            return jsonify({'error': 'Connection not found'}), 404
            
        # Security Check: Ensure current user is the actual recipient
        # The connection request must be addressed to either current_user_id OR current user's email
        # We need to fetch current user to check email
        user = User.query.get(current_user_id)
        if not user:
             return jsonify({'error': 'User not found'}), 404
             
        is_recipient = False
        if connection.recipient_user_id and str(connection.recipient_user_id) == str(current_user_id):
             is_recipient = True
        elif connection.recipient_email and connection.recipient_email == user.email:
             is_recipient = True
             
        if not is_recipient:
             return jsonify({'error': 'Unauthorized to decline this request'}), 403
        
        connection.status = 'declined'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'connection': connection.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Decline connection failed: {str(e)}")
        return jsonify({'error': 'Failed to decline connection'}), 500


@partners_bp.route('/connections', methods=['GET'])
@token_required
def get_connections(current_user_id):
    """
    Get partner connections for the authenticated user.
    """
    try:
        user_id = str(current_user_id)
        try:
             user_uuid = uuid.UUID(user_id)
        except ValueError:
             return jsonify({'error': 'Invalid user_id'}), 400

        user = User.query.get(user_uuid)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Find connections where:
        # 1. User is the requester
        # 2. User is the recipient (by email)
        # 3. User is the recipient (by ID - for accepted ones)
        # AND status is pending or accepted
        # Find connections where:
        # 1. User is the requester
        # 2. User is the recipient (by email)
        # 3. User is the recipient (by ID - for accepted ones)
        # AND status is pending or accepted
        connections = PartnerConnection.query.filter(
            or_(
                PartnerConnection.requester_user_id == user_uuid,
                PartnerConnection.recipient_email == user.email,
                PartnerConnection.recipient_user_id == user_uuid
            )
        ).filter(
            PartnerConnection.status.in_(['pending', 'accepted'])
        ).order_by(PartnerConnection.created_at.desc()).all()
        
        return jsonify({
            'connections': [c.to_dict() for c in connections]
        }), 200
        
    except Exception as e:
        logger.error(f"Get connections failed: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve connections',
            'connections': []
        }), 500



@partners_bp.route('/remembered', methods=['GET'])
@token_required
def get_remembered_partners(current_user_id):
    """
    Get list of remembered partners for authenticated user (FR-60).
    Returns up to 10 most recent partners.
    """
    try:
        user_uuid = uuid.UUID(str(current_user_id))

        partners = RememberedPartner.query\
            .filter_by(user_id=user_uuid)\
            .order_by(RememberedPartner.last_played_at.desc())\
            .limit(10)\
            .all()
        
        return jsonify({
            'partners': [p.to_dict() for p in partners]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve partners: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve partners',
            'partners': []
        }), 500


@partners_bp.route('/remembered/<partner_user_id>', methods=['DELETE'])
@token_required
def remove_remembered_partner(current_user_id, partner_user_id):
    """
    Remove a partner from remembered list (FR-61).
    """
    try:
        # Cast to UUIDs for RememberedPartner queries
        try:
            user_uuid = uuid.UUID(str(current_user_id)) # Authed User
            partner_uuid = uuid.UUID(str(partner_user_id))
        except ValueError:
            return jsonify({'error': 'Invalid ID format'}), 400

        # Find the entry where user_id remembers partner_user_id
        partner = RememberedPartner.query.filter_by(
            user_id=user_uuid,
            partner_user_id=partner_uuid
        ).first()
        
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
        
        # 1. Remove from Requester's list
        if partner:
            db.session.delete(partner)
            
        # 2. Reciprocal: Remove from Partner's list (if exists)
        reciprocal_partner = RememberedPartner.query.filter_by(
            user_id=partner_uuid,
            partner_user_id=user_uuid
        ).first()
        
        if reciprocal_partner:
            db.session.delete(reciprocal_partner)
            
        # 3. Update PartnerConnection status to 'disconnected'
        # PartnerConnection uses UUIDs now
        
        connection = PartnerConnection.query.filter(
            or_(
                (PartnerConnection.requester_user_id == user_uuid) & (PartnerConnection.recipient_user_id == partner_uuid),
                (PartnerConnection.requester_user_id == partner_uuid) & (PartnerConnection.recipient_user_id == user_uuid)
            )
        ).order_by(PartnerConnection.created_at.desc()).first()
        
        if connection:
            connection.status = 'disconnected'
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Partner removed and disconnected'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Remove partner failed: {str(e)}")
        return jsonify({'error': 'Failed to remove partner'}), 500




