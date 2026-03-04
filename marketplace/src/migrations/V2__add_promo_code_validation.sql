-- V2__add_promo_code_validation.sql
-- Добавляет CHECK constraint для валидации формата промокода

-- Сначала удалим невалидные промокоды (если есть)
DELETE FROM promo_codes WHERE code !~ '^[A-Z0-9_]{4,20}$';

-- Добавим CHECK constraint
ALTER TABLE promo_codes 
ADD CONSTRAINT check_promo_code_format 
CHECK (code ~ '^[A-Z0-9_]{4,20}$');

-- Добавим комментарий
COMMENT ON CONSTRAINT check_promo_code_format ON promo_codes IS 
'Promo code must contain only uppercase letters (A-Z), numbers (0-9), and underscores (_), length 4-20 characters';