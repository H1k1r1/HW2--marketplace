DELETE FROM promo_codes WHERE code !~ '^[A-Z0-9_]{4,20}$';

ALTER TABLE promo_codes 
ADD CONSTRAINT check_promo_code_format 
CHECK (code ~ '^[A-Z0-9_]{4,20}$');

COMMENT ON CONSTRAINT check_promo_code_format ON promo_codes IS 

'Promo code must contain only uppercase letters (A-Z), numbers (0-9), and underscores (_), length 4-20 characters';
