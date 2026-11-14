# Capital-gains rules used by artha-tax (FY 2026-27)

Verified November 2026: Budget 2026 left these rates unchanged. Re-check after each Union Budget.

| Type | Long term after | Long-term rate | Short-term rate |
|---|---|---|---|
| `equity` (equity MF, index fund, equity FoF) | more than 12 months | 12.5% above ₹1.25 lakh per FY | 20% |
| `elss` | more than 12 months, plus a **3-year lock-in per lot** | same as equity | same as equity |
| `listed_share` (NSE/BSE shares, equity ETFs) | more than 12 months | 12.5% above ₹1.25 lakh per FY | 20% |
| `other_listed` (gold, silver, international ETFs) | more than 12 months | 12.5%, no exemption | slab rate |
| `other_unlisted` (gold, silver, international FoFs) | more than 24 months | 12.5%, no exemption | slab rate |
| `foreign_share` (US or other foreign shares, vested RSUs) | more than 24 months | 12.5% | slab rate |
| `specified_debt` (more than 65% debt) | bought before 1 Apr 2023: more than 24 months; on or after: never | 12.5% | slab rate |

## Details

- The ₹1.25 lakh exemption is **one per financial year**, shared by all equity long-term gains (funds and shares). Subtract long-term gains already realised this year first.
- Add 4% cess to the tax. Surcharge is not included.
- Losses: a short-term loss sets off against short-term or long-term gains of any asset; a long-term loss only against long-term gains. Say when you net them.
- Grandfathering: for equity bought before 1 Feb 2018, cost = the higher of actual cost and the lower of (31 Jan 2018 value, sale value).
- Long term means held **more than** the period: the first long-term day is the day after the anniversary (a purchase on 10 Mar 2026 is long term from 11 Mar 2027 for 12 months, 11 Mar 2028 for 24 months).
- ELSS lock-in is 3 years from each instalment's purchase date; a 2021 lot can be free while a 2024 lot in the same fund is locked.
- Redemptions are **FIFO** per folio. A switch between funds is a taxable redemption.
- RSU cost basis = market value on the vest date (convert at the rate for that date).

## Worked example (use it to check your method)

Lots from `lots.example.json`, slab 30%, nothing realised yet, as of 14 Nov 2026:

| Lot | Gain | Term | Note |
|---|---|---|---|
| ELSS, bought 2021-06-10 | +9,000 | long | free to sell |
| ELSS, bought 2024-03-10 | −5,400 | long | locked until 2027-03-10 |
| ELSS, bought 2026-01-10 | −200 | short | locked until 2029-01-10 |
| Equity fund, bought 2025-06-01 | +20,000 | long | |
| Gold FoF, bought 2025-02-01 | −1,500 | short | long term from 2027-02-02 |
| US stock (RSU), bought 2026-03-10 | +7,000 | short | long term from 2028-03-11 |

Equity long-term gains if all sold: 9,000 − 5,400 + 20,000 = 23,600, below the ₹1.25 lakh exemption, so no tax. Only the US stock's short-term gain of 7,000 is taxed, at 30% slab: 2,100, plus 4% cess = ₹2,184. (In practice the locked ELSS lots cannot be sold yet.)
