# Pricing Rules SME Walkthrough

**Date:** 2026-05-16
**SME:** Jane Doe (Pricing team lead)
**Topic:** Tier discount + promotion stacking rules

## Key Understandings

1. **Tier discount** is applied first, based on customer tier (A/B/C).
2. **Promo code** is applied second, on top of the tier-discounted price.
3. The promo codes SUMMR and WINTR both give 5%.
4. VIP customers (tier A) also get an additional 10% via VIP10 code.
5. **Silent fallback**: unknown promo codes return 0% discount with no error.

## Confirmation

- The formula `final_price = round(base * qty * (1-tier) * (1-promo), 2)` matches the code.
- Promo code stacking is additive, not multiplicative.