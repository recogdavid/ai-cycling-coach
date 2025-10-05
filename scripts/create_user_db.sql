-- Create database and user for ai-cycling-coach
CREATE USER aicoach_user WITH PASSWORD 'D4bosch!609';
CREATE DATABASE aicoach_db OWNER aicoach_user;
GRANT ALL PRIVILEGES ON DATABASE aicoach_db TO aicoach_user;

