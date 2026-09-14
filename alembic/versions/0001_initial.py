from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"))

    specs = {
        "connectors": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("external_ref", sa.String(100)), ("name", sa.String(150)), ("phone", sa.String(30)),
            ("email", sa.String(150)), ("status", sa.String(30)), ("tier", sa.String(30))],
        "customers": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("connector_id", postgresql.UUID(as_uuid=True)), ("name", sa.String(150)),
            ("phone", sa.String(30)), ("email", sa.String(150)), ("city", sa.String(100)),
            ("occupation", sa.String(100)), ("status", sa.String(30))],
        "leads": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("connector_id", postgresql.UUID(as_uuid=True)), ("customer_id", postgresql.UUID(as_uuid=True)),
            ("product_code", sa.String(50)), ("requested_amount", sa.Numeric(18,2)),
            ("stage", sa.String(40)), ("status", sa.String(40)), ("source", sa.String(50)),
            ("submitted_at", sa.DateTime())],
        "payouts": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("connector_id", postgresql.UUID(as_uuid=True)), ("lead_id", postgresql.UUID(as_uuid=True)),
            ("amount", sa.Numeric(18,2)), ("status", sa.String(30)), ("payout_date", sa.DateTime())],
        "marketplace_listings": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("connector_id", postgresql.UUID(as_uuid=True)), ("name", sa.String(150)),
            ("profession", sa.String(100)), ("city", sa.String(100)), ("description", sa.Text()),
            ("status", sa.String(30))],
        "calendar_tasks": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("connector_id", postgresql.UUID(as_uuid=True)), ("title", sa.String(200)),
            ("notes", sa.Text()), ("due_at", sa.DateTime()), ("status", sa.String(30))],
        "audit_events": [
            ("id", postgresql.UUID(as_uuid=True)), ("tenant_id", postgresql.UUID(as_uuid=True)),
            ("actor_id", postgresql.UUID(as_uuid=True)), ("action", sa.String(100)),
            ("entity_type", sa.String(100)), ("entity_id", sa.String(100)), ("payload", sa.Text()),
            ("created_at", sa.DateTime())]
    }
    for table, cols in specs.items():
        columns = [sa.Column(n, t, primary_key=(n=="id"), nullable=(n in {"id","tenant_id"})) for n,t in cols]
        if table == "connectors":
            columns += [sa.Column("status_default", sa.String(1), nullable=True)]
        op.create_table(table, *columns)
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            "CREATE POLICY %s_tenant_isolation ON %s USING "
            "(tenant_id::text = current_setting('app.tenant_id', true))"
            % (table, table)
        )

def downgrade():
    for table in ["audit_events","calendar_tasks","marketplace_listings","payouts","leads","customers","connectors"]:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.drop_table(table)
    op.drop_table("tenants")
