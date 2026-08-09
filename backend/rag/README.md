# DhanBuddy approved knowledge library

This folder contains the small, reviewed knowledge collection used by DhanBuddy.
It is separate from caller memory:

- SQLite answers: **What did this caller permit DhanBuddy to remember?**
- This RAG folder answers: **What approved general financial-literacy information can DhanBuddy explain?**

Only institution-neutral educational information from official Indian sources is
included. DhanBuddy must not use these documents for product recommendations,
returns, scheme eligibility, approvals, or personalised financial advice.

## Sources

1. [SEBI Investor, *Financial Education Booklet*](https://investor.sebi.gov.in/pdf/downloadable-documents/Financial%20Education%20Booklet%20-%20English.pdf)
2. [SEBI Investor, *Money Matters: Let's Understand*](https://investor.sebi.gov.in/moneymatters.html)
3. [RBI, *Financial Literacy Material / FAME*](https://www.rbi.org.in/commonperson/English/Scripts/PressReleases.aspx?Id=2123)

`approved_knowledge.json` contains short, reviewed paraphrases rather than copied
documents. Update `reviewed_on` whenever a source is checked again.
