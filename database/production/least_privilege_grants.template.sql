-- TEMPLATE ONLY. Replace placeholders outside the web root and execute as a DBA.
-- Use a separate migration/DBA account for CREATE/ALTER/DROP. The web application
-- should receive only normal data-access privileges.
CREATE USER 'localconnect_app'@'APP_HOST' IDENTIFIED BY 'REPLACE_WITH_RANDOM_SECRET';
GRANT SELECT, INSERT, UPDATE, DELETE ON localconnect_db.* TO 'localconnect_app'@'APP_HOST';
-- Do not grant FILE, PROCESS, SUPER, CREATE USER, GRANT OPTION, DROP, ALTER or CREATE.
