"""core_models

Revision ID: 0001
Revises: 0000
Create Date: 2026-05-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = "0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role_enum = postgresql.ENUM(
    "ADMIN", "MANAGER", "DISPATCHER", "DRIVER", "CUSTOMER",
    name="userrole",
    create_type=False,
)
user_status_enum = postgresql.ENUM(
    "ACTIVE", "INACTIVE",
    name="userstatus",
    create_type=False,
)
vehicle_status_enum = postgresql.ENUM(
    "ACTIVE", "INACTIVE",
    name="vehiclestatus",
    create_type=False,
)
trip_type_enum = postgresql.ENUM(
    "APP_REQUEST", "PHONE_REQUEST",
    name="triptype",
    create_type=False,
)
trip_status_enum = postgresql.ENUM(
    "PENDING", "ASSIGNED", "ACCEPTED", "ARRIVED",
    "STARTED", "COMPLETED", "CANCELLED", "DECLINED",
    name="tripstatus",
    create_type=False,
)


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'DISPATCHER', 'DRIVER', 'CUSTOMER');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userstatus AS ENUM ('ACTIVE', 'INACTIVE');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vehiclestatus AS ENUM ('ACTIVE', 'INACTIVE');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE triptype AS ENUM ('APP_REQUEST', 'PHONE_REQUEST');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tripstatus AS ENUM ('PENDING', 'ASSIGNED', 'ACCEPTED', 'ARRIVED', 'STARTED', 'COMPLETED', 'CANCELLED', 'DECLINED');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("status", user_status_enum, nullable=False, server_default="ACTIVE"),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "driver_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("profile_picture", sa.String(500), nullable=True),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("total_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "customer_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("total_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plate_number", sa.String(20), nullable=False),
        sa.Column("make", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
        sa.Column("status", vehicle_status_enum, nullable=False, server_default="ACTIVE"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plate_number"),
    )

    op.create_table(
        "driver_vehicle_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_user_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["driver_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "fare_matrix",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pickup_zone_id", sa.Integer(), nullable=False),
        sa.Column("dropoff_zone_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["dropoff_zone_id"], ["zones.id"]),
        sa.ForeignKeyConstraint(["pickup_zone_id"], ["zones.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pickup_zone_id", "dropoff_zone_id", name="uq_fare_matrix_zone_pair"),
    )

    op.create_table(
        "special_routes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pickup_area", sa.String(255), nullable=False),
        sa.Column("dropoff_area", sa.String(255), nullable=False),
        sa.Column("fixed_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_type", trip_type_enum, nullable=False),
        sa.Column("status", trip_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("customer_user_id", sa.Integer(), nullable=False),
        sa.Column("driver_user_id", sa.Integer(), nullable=True),
        sa.Column("dispatcher_user_id", sa.Integer(), nullable=True),
        sa.Column("pickup_address", sa.String(500), nullable=False),
        sa.Column("dropoff_address", sa.String(500), nullable=False),
        sa.Column("pickup_zone_id", sa.Integer(), nullable=True),
        sa.Column("dropoff_zone_id", sa.Integer(), nullable=True),
        sa.Column("suggested_fare", sa.Numeric(10, 2), nullable=False),
        sa.Column("final_fare", sa.Numeric(10, 2), nullable=True),
        sa.Column("fare_overridden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("stop_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("standby_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("distance_km", sa.Numeric(10, 3), nullable=True),
        sa.Column("declined_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("driver_rating", sa.SmallInteger(), nullable=True),
        sa.Column("customer_rating", sa.SmallInteger(), nullable=True),
        sa.CheckConstraint(
            "driver_rating >= 1 AND driver_rating <= 5",
            name="ck_trips_driver_rating_range",
        ),
        sa.CheckConstraint(
            "customer_rating >= 1 AND customer_rating <= 5",
            name="ck_trips_customer_rating_range",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["dispatcher_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["driver_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["dropoff_zone_id"], ["zones.id"]),
        sa.ForeignKeyConstraint(["pickup_zone_id"], ["zones.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "driver_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("driver_user_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["driver_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    op.create_foreign_key(
        "fk_users_updated_by_user_id",
        "users", "users",
        ["updated_by_user_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_updated_by_user_id", "users", type_="foreignkey")

    op.drop_table("password_reset_tokens")
    op.drop_table("driver_locations")
    op.drop_table("trips")
    op.drop_table("special_routes")
    op.drop_table("fare_matrix")
    op.drop_table("driver_vehicle_assignments")
    op.drop_table("vehicles")
    op.drop_table("customer_profiles")
    op.drop_table("driver_profiles")
    op.drop_table("zones")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS tripstatus")
    op.execute("DROP TYPE IF EXISTS triptype")
    op.execute("DROP TYPE IF EXISTS vehiclestatus")
    op.execute("DROP TYPE IF EXISTS userstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
