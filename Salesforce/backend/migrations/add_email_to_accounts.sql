-- Migration: Add email column to accounts table
-- Date: 2026-02-13

ALTER TABLE accounts ADD COLUMN email VARCHAR(255);

CREATE INDEX ix_accounts_email ON accounts(email);
