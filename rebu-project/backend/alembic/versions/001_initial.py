"""Initial migration - Create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-27 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('profile_image_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('fcm_token', sa.String(), nullable=True),
        sa.Column('rating', sa.Float(), default=5.0),
        sa.Column('total_trips', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)
    
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('tier', sa.Enum('FREE', 'PRO', 'PREMIUM', name='subscriptiontier'), nullable=False),
        sa.Column('monthly_price', sa.Float(), nullable=False),
        sa.Column('commission_rate', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'CANCELLED', name='subscriptionstatus'), default='ACTIVE'),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('auto_renew', sa.Boolean(), default=False),
        sa.Column('last_payment_date', sa.DateTime(timezone=True)),
        sa.Column('next_payment_date', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create drivers table
    op.create_table(
        'drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('profile_image_url', sa.String()),
        sa.Column('license_number', sa.String(), nullable=False),
        sa.Column('license_expiry_date', sa.DateTime(), nullable=False),
        sa.Column('license_image_url', sa.String()),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'OFFLINE', 'BUSY', 'LIMITED', 'SUSPENDED', 'BLOCKED', name='driverstatus'), default='PENDING'),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('current_subscription_id', sa.Integer()),
        sa.Column('wallet_balance', sa.Float(), default=0.0, nullable=False),
        sa.Column('last_known_lat', sa.Float()),
        sa.Column('last_known_lon', sa.Float()),
        sa.Column('last_location_update', sa.DateTime(timezone=True)),
        sa.Column('fcm_token', sa.String()),
        sa.Column('rating', sa.Float(), default=5.0),
        sa.Column('total_trips', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['current_subscription_id'], ['subscriptions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_drivers_email', 'drivers', ['email'], unique=True)
    op.create_index('ix_drivers_phone', 'drivers', ['phone'], unique=True)
    op.create_index('ix_drivers_license_number', 'drivers', ['license_number'], unique=True)
    op.create_index('ix_drivers_status', 'drivers', ['status'])
    
    # Create vehicles table
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_type', sa.Enum('PICKUP', 'VAN', 'SMALL_TRUCK', 'MEDIUM_TRUCK', 'LARGE_TRUCK', name='vehicletype'), nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(), nullable=False),
        sa.Column('license_plate', sa.String(), nullable=False),
        sa.Column('max_weight_kg', sa.Float(), nullable=False),
        sa.Column('max_volume_m3', sa.Float()),
        sa.Column('front_image_url', sa.String()),
        sa.Column('side_image_url', sa.String()),
        sa.Column('license_plate_image_url', sa.String()),
        sa.Column('insurance_policy_number', sa.String()),
        sa.Column('insurance_expiry_date', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_vehicles_license_plate', 'vehicles', ['license_plate'], unique=True)
    op.create_index('ix_vehicles_driver_id', 'vehicles', ['driver_id'])
    
    # Create trip_requests table
    op.create_table(
        'trip_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.Enum('ON_DEMAND', 'SCHEDULED', name='tripmode'), nullable=False),
        sa.Column('pickup_address', sa.String(), nullable=False),
        sa.Column('pickup_lat', sa.Float(), nullable=False),
        sa.Column('pickup_lon', sa.Float(), nullable=False),
        sa.Column('dropoff_address', sa.String(), nullable=False),
        sa.Column('dropoff_lat', sa.Float(), nullable=False),
        sa.Column('dropoff_lon', sa.Float(), nullable=False),
        sa.Column('estimated_distance_km', sa.Float()),
        sa.Column('estimated_duration_minutes', sa.Integer()),
        sa.Column('estimated_fare', sa.Float(), nullable=False),
        sa.Column('required_vehicle_type', sa.String()),
        sa.Column('cargo_description', sa.Text()),
        sa.Column('cargo_weight_kg', sa.Float()),
        sa.Column('cargo_images_urls', sa.Text()),
        sa.Column('scheduled_start_at', sa.DateTime(timezone=True)),
        sa.Column('scheduled_end_at', sa.DateTime(timezone=True)),
        sa.Column('pre_assigned_driver_id', sa.Integer()),
        sa.Column('reminder_60min_sent', sa.Boolean(), default=False),
        sa.Column('reminder_15min_sent', sa.Boolean(), default=False),
        sa.Column('status', sa.Enum('PENDING', 'MATCHED', 'EXPIRED', 'CANCELLED', name='triprequeststatus'), default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('matched_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['pre_assigned_driver_id'], ['drivers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trip_requests_user_id', 'trip_requests', ['user_id'])
    op.create_index('ix_trip_requests_mode', 'trip_requests', ['mode'])
    op.create_index('ix_trip_requests_status', 'trip_requests', ['status'])
    op.create_index('ix_trip_requests_scheduled_start_at', 'trip_requests', ['scheduled_start_at'])
    
    # Create trip_offers table
    op.create_table(
        'trip_offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trip_request_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('offered_fare', sa.Float(), nullable=False),
        sa.Column('estimated_arrival_minutes', sa.Integer()),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'EXPIRED', name='offerstatus'), default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['trip_request_id'], ['trip_requests.id']),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trip_offers_trip_request_id', 'trip_offers', ['trip_request_id'])
    op.create_index('ix_trip_offers_driver_id', 'trip_offers', ['driver_id'])
    op.create_index('ix_trip_offers_status', 'trip_offers', ['status'])
    
    # Create trips table
    op.create_table(
        'trips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trip_request_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('pickup_address', sa.String(), nullable=False),
        sa.Column('pickup_lat', sa.Float(), nullable=False),
        sa.Column('pickup_lon', sa.Float(), nullable=False),
        sa.Column('dropoff_address', sa.String(), nullable=False),
        sa.Column('dropoff_lat', sa.Float(), nullable=False),
        sa.Column('dropoff_lon', sa.Float(), nullable=False),
        sa.Column('actual_distance_km', sa.Float()),
        sa.Column('actual_duration_minutes', sa.Integer()),
        sa.Column('estimated_fare', sa.Float(), nullable=False),
        sa.Column('final_fare', sa.Float()),
        sa.Column('payment_method', sa.String(), default='CASH'),
        sa.Column('is_paid', sa.Boolean(), default=False),
        sa.Column('commission_rate', sa.Float(), nullable=False),
        sa.Column('commission_amount', sa.Float()),
        sa.Column('commission_charged', sa.Boolean(), default=False),
        sa.Column('status', sa.Enum('CONFIRMED', 'DRIVER_ARRIVING', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='tripstatus'), default='CONFIRMED'),
        sa.Column('user_rating', sa.Float()),
        sa.Column('driver_rating', sa.Float()),
        sa.Column('user_feedback', sa.Text()),
        sa.Column('driver_feedback', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('arrived_at_pickup_at', sa.DateTime(timezone=True)),
        sa.Column('picked_up_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_by', sa.String()),
        sa.Column('cancellation_reason', sa.Text()),
        sa.ForeignKeyConstraint(['trip_request_id'], ['trip_requests.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trips_trip_request_id', 'trips', ['trip_request_id'], unique=True)
    op.create_index('ix_trips_user_id', 'trips', ['user_id'])
    op.create_index('ix_trips_driver_id', 'trips', ['driver_id'])
    op.create_index('ix_trips_status', 'trips', ['status'])
    
    # Create wallet_transactions table
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('TRIP_COMMISSION', 'PAYMENT', 'REFUND', 'ADJUSTMENT', 'BONUS', 'PENALTY', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('balance_after', sa.Float(), nullable=False),
        sa.Column('trip_id', sa.Integer()),
        sa.Column('description', sa.Text()),
        sa.Column('reference', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallet_transactions_driver_id', 'wallet_transactions', ['driver_id'])
    op.create_index('ix_wallet_transactions_type', 'wallet_transactions', ['type'])
    op.create_index('ix_wallet_transactions_created_at', 'wallet_transactions', ['created_at'])
    
    # Create driver_availability_blocks table
    op.create_table(
        'driver_availability_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('trip_request_id', sa.Integer()),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id']),
        sa.ForeignKeyConstraint(['trip_request_id'], ['trip_requests.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_driver_availability_blocks_driver_id', 'driver_availability_blocks', ['driver_id'])
    op.create_index('ix_driver_availability_blocks_start_time', 'driver_availability_blocks', ['start_time'])
    op.create_index('ix_driver_availability_blocks_end_time', 'driver_availability_blocks', ['end_time'])


def downgrade():
    op.drop_table('driver_availability_blocks')
    op.drop_table('wallet_transactions')
    op.drop_table('trips')
    op.drop_table('trip_offers')
    op.drop_table('trip_requests')
    op.drop_table('vehicles')
    op.drop_table('drivers')
    op.drop_table('subscriptions')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS tripstatus')
    op.execute('DROP TYPE IF EXISTS offerstatus')
    op.execute('DROP TYPE IF EXISTS triprequeststatus')
    op.execute('DROP TYPE IF EXISTS vehicletype')
    op.execute('DROP TYPE IF EXISTS driverstatus')
    op.execute('DROP TYPE IF EXISTS transactiontype')
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS tripmode')
