USE localconnect_db;
-- Phase 3 uses the service_requests and request_status_history tables already created in Phase 1/2.
-- These indexes improve open-requirement and direct-request lookups. Run once on an existing Phase 2 database.
ALTER TABLE service_requests ADD INDEX idx_sr_type_status_service (request_type,status,service_id);
ALTER TABLE service_requests ADD INDEX idx_sr_business (business_id,status);
