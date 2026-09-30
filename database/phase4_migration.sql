USE localconnect_db;
-- Phase 4 uses reviews, favorites and notifications tables already created in the Phase 1 forward-compatible schema.
-- These indexes improve dashboard queries and are safe to run once.
ALTER TABLE favorites ADD INDEX idx_favorites_customer_created (customer_id, created_at);
ALTER TABLE reviews ADD INDEX idx_reviews_customer_created (customer_id, created_at);
ALTER TABLE notifications ADD INDEX idx_notifications_created (user_id, created_at);
