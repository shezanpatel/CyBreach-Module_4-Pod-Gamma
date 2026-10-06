CREATE TABLE IF NOT EXISTS badge_award (
    id BIGSERIAL PRIMARY KEY,
    badge_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    evidence_ref TEXT,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_badge_award_badge_tenant
        UNIQUE (badge_id, tenant_id)
);
