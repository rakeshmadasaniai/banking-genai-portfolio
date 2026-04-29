# Banking & Finance RAG — Evaluation Query Set

**120 domain test queries across OpenAI, Fine-Tuned, and Auto modes**

Covers: KYC · AML · Basel III · FDIC · RBI · CECL · Regulation E · Credit Risk · Monetary Policy · Payments · Financial Ratios

---

## Mode 1 — OpenAI (40 queries)

Best for: grounded factual answers, cross-jurisdictional comparisons, definitions with precise regulatory language.

### KYC
1. What are the four main components of KYC under FinCEN guidelines?
2. What documents are accepted as proof of identity for individual KYC in India?
3. What is the KYC re-verification frequency for high-risk customers under RBI guidelines?
4. What is Video-based Customer Identification Process and when was it introduced?
5. What is the Central KYC Registry and who maintains it in India?
6. Who qualifies as a Politically Exposed Person and what additional scrutiny applies?
7. What is the difference between Customer Due Diligence and Enhanced Due Diligence?
8. What documents are required for KYC of a corporate entity in the United States?

### AML
9. What are the three stages of money laundering?
10. What is the Cash Transaction Report threshold in India and who receives it?
11. Within how many days must a Suspicious Transaction Report be filed under PMLA?
12. What is structuring and why is it considered an AML red flag?
13. What is FATF and what is India's relationship with it?
14. What is hawala and why is it associated with money laundering?
15. What is FIU-IND and what is its role in the AML framework?
16. What is the Cross Border Wire Transfer reporting threshold in India?

### Basel III
17. What is the minimum Common Equity Tier 1 ratio under Basel III?
18. What is the Capital Conservation Buffer and when must it be drawn down?
19. What is the Liquidity Coverage Ratio and what does it require banks to hold?
20. What is the Net Stable Funding Ratio and what time horizon does it cover?
21. What is the minimum Leverage Ratio under Basel III?
22. What is the Countercyclical Buffer and when is it activated?
23. What is the difference between Tier 1 and Tier 2 capital?
24. Why was Basel III introduced and what weakness in Basel II did it address?

### FDIC & U.S. Banking
25. What is the FDIC deposit insurance limit per depositor per insured bank?
26. Which account types are covered by FDIC insurance?
27. What is Regulation E and what does it govern?
28. What is the liability limit for unauthorized electronic transfers under Regulation E if reported within 2 days?
29. What is CECL and how does it differ from the incurred loss model?
30. What is the Bank Secrecy Act and what does it require of financial institutions?
31. What is FinCEN's Beneficial Ownership Rule and what is the ownership threshold?
32. What is the difference between NEFT, RTGS, and IMPS in terms of settlement speed and availability?

### RBI & Indian Banking
33. What is the Repo Rate and what is its role in monetary policy?
34. What is the Cash Reserve Ratio and what is the current rate?
35. What is the Statutory Liquidity Ratio and which assets qualify?
36. What is Priority Sector Lending and what percentage is mandated for banks?
37. When is a loan classified as a Non-Performing Asset under RBI norms?
38. What are the three sub-categories of NPAs and their provisioning requirements?
39. What is the DICGC deposit insurance limit in India?
40. What is MCLR and how does it differ from the External Benchmark Lending Rate?

---

## Mode 2 — Fine-Tuned (40 queries)

Best for: domain-specific compliance language, procedural questions, India-specific regulations, edge cases where precise terminology matters.

### KYC Procedures
41. A bank onboards a new customer who is a foreign national and a known PEP. Walk through every KYC and AML step the bank must follow.
42. A customer refuses to provide source of funds documentation. What options does the bank have under KYC guidelines?
43. A corporate customer has a beneficial owner who owns exactly 25% of the entity. Does this trigger Beneficial Ownership disclosure under FinCEN rules?
44. A customer's KYC was last verified 9 years ago and they are classified as low-risk. Is re-verification required?
45. What is the difference between periodic KYC re-verification and event-based KYC triggers?
46. A bank uses V-CIP to onboard a customer remotely. What are the minimum requirements for a valid V-CIP session under RBI guidelines?
47. A customer claims Aadhaar-based KYC is sufficient for opening a current account. Is this correct under RBI norms?
48. What is the obligation of a bank when a customer previously classified as low-risk is elected to a public office?

### AML Compliance Scenarios
49. A customer deposits Rs. 9.8 lakhs in cash on three consecutive days. What AML steps must the bank take?
50. A small business receives multiple international wire transfers from high-risk jurisdictions with no clear business purpose. What should the bank do?
51. What is the difference between a Suspicious Transaction Report and a Cash Transaction Report in terms of threshold, trigger, and timeline?
52. A bank employee notices a colleague is helping a customer split transactions to avoid CTR reporting. What is the correct procedure?
53. A new account receives a large wire transfer immediately followed by multiple smaller outgoing transfers. Which money laundering stage does this represent?
54. What is the PMLA obligation for a bank when a customer is found on the UN Security Council sanctions list?
55. A non-profit organization deposits Rs. 12 lakhs in cash. What reporting obligation does this trigger?
56. What is the difference between AML and CFT and how do they overlap in banking compliance?

### Credit Risk & Lending
57. A borrower's DSCR is 1.1. Should the bank approve the loan and what conditions might apply?
58. A loan that was restructured 6 months ago has defaulted again. How should it be classified and provisioned?
59. What is the difference between a substandard asset and a doubtful asset under RBI NPA classification?
60. A bank has gross NPAs of Rs. 300 crore and provisions of Rs. 240 crore. Calculate the Provision Coverage Ratio and assess it against RBI's recommendation.
61. What happens to a bank's NIM when the repo rate rises but deposit rates are slow to reprice?
62. A customer applies for a home loan of Rs. 40 lakhs on a property valued at Rs. 50 lakhs. What is the maximum LTV and how much must the customer contribute?
63. What is the Expected Loss formula and calculate it for PD 4%, LGD 35%, EAD Rs. 20 crore.
64. A bank's loan moves from the doubtful category under 1 year to doubtful over 3 years. How does the provisioning requirement change?

### Basel III Application
65. A bank has CET1 of Rs. 400 crore, Additional Tier 1 of Rs. 80 crore, Tier 2 of Rs. 120 crore, and RWA of Rs. 5,500 crore. Calculate CAR and check against India's minimum.
66. Why does Basel III require a Leverage Ratio in addition to risk-based capital requirements?
67. A bank's LCR falls to 85% during a stress period. What does this mean and what action is required?
68. What is the difference between the Capital Conservation Buffer and the Countercyclical Buffer in terms of when each applies?
69. Under what conditions can a regulator release the Countercyclical Buffer?
70. A bank has HQLA of Rs. 2,000 crore and net cash outflows of Rs. 1,600 crore over 30 days. Does it meet the LCR requirement?
71. What was the fundamental flaw in Basel II's treatment of off-balance-sheet exposures that Basel III addressed?
72. How does the NSFR differ from the LCR in terms of time horizon and what it measures?

### Payments & Products
73. A customer needs to transfer Rs. 1.5 lakhs instantly at 11 PM. Which payment system should they use and why?
74. A customer's debit card is used fraudulently and they report it 4 days after noticing. What is their liability under Regulation E?
75. What is a Letter of Credit and how does it reduce counterparty risk in trade transactions?
76. What is the difference between a Cash Credit facility and an Overdraft facility?
77. A customer wants to know if their Rs. 6 lakh fixed deposit is protected under DICGC insurance. What is the answer and why?
78. What is UPI and how does it differ from IMPS in terms of the underlying infrastructure?
79. What is a Demat account and which two depositories manage them in India?
80. What is the difference between a Recurring Deposit and a Fixed Deposit?

---

## Mode 3 — Auto (40 queries)

Best for: questions where both model paths compete — Auto selects the stronger answer based on groundedness, completeness, and latency.

### Cross-Jurisdictional Comparisons
81. Compare the AML reporting obligations of banks in the United States and India — thresholds, timelines, and receiving authorities.
82. Compare KYC re-verification requirements under FinCEN rules and RBI Master Direction on KYC.
83. What is the difference between the U.S. Bank Secrecy Act and India's Prevention of Money Laundering Act in terms of scope and obligations?
84. How does Basel III capital adequacy implementation differ between India and the global BIS standard?
85. Compare FDIC deposit insurance in the U.S. with DICGC deposit insurance in India — limits, coverage, and exclusions.
86. How do suspicious transaction reporting timelines compare between the U.S. and India?
87. Compare the Beneficial Ownership rules in the U.S. and India — thresholds and disclosure requirements.
88. What are the key differences between the U.S. CECL model and India's NPA provisioning framework?

### Multi-Concept Integration
89. A bank is onboarding a high-net-worth individual from a high-risk jurisdiction who is also a PEP and wants to make a large cash deposit. Walk through every KYC, AML, and reporting obligation.
90. How do CRR, SLR, and the repo rate interact to determine how much a bank can lend?
91. A bank's CASA ratio drops while its NPA ratio rises at the same time. What does this combination signal about the bank's financial health?
92. How does the Capital Conservation Buffer interact with the minimum CET1 requirement when a bank is under stress?
93. A bank wants to improve both its LCR and its NSFR simultaneously. What changes to its balance sheet would achieve both?
94. How does loan restructuring affect NPA classification, provisioning requirements, and the bank's CAR simultaneously?
95. A central bank raises the repo rate by 50 basis points. Trace the full effect on MCLR, EBLR-linked loans, deposit rates, NIM, and credit demand.
96. How do FATF grey-listing and Basel III capital requirements interact for a bank operating in a grey-listed jurisdiction?

### Scenario Analysis
97. A bank's Net NPA ratio is 3.2% and its PCR is 58%. What does this tell you about the bank's risk position and what should it do?
98. A fintech company applies for a banking license. What KYC, AML, and capital adequacy requirements would it need to meet from day one?
99. A bank discovers that a long-standing corporate customer has been using shell companies for layering. What is the bank's legal obligation under PMLA and BSA?
100. Interest rates are rising and a bank has a large portfolio of fixed-rate loans. How does this affect NIM, and what hedging strategies are available?

### Calculation-Heavy Questions
101. A bank has total deposits of Rs. 80,000 crore. Calculate the amounts locked in CRR and SLR and the funds available for lending.
102. Calculate the Expected Loss for a commercial loan portfolio: PD 6%, LGD 45%, EAD Rs. 50 crore.
103. A bank reports net income of Rs. 900 crore, total assets of Rs. 75,000 crore, and shareholders equity of Rs. 8,000 crore. Calculate ROA and ROE and assess both.
104. A bank has interest income of Rs. 1,200 crore, interest expense of Rs. 750 crore, and average earning assets of Rs. 18,000 crore. Calculate NIM.
105. A bank's Cost-to-Income ratio is 62%. What does this mean and what would need to change to bring it below 50%?
106. A bank has CASA deposits of Rs. 25,000 crore out of total deposits of Rs. 60,000 crore. Calculate the CASA ratio and explain its significance.
107. A bank's gross advances are Rs. 90,000 crore and total deposits are Rs. 1,10,000 crore. Calculate the Credit-Deposit ratio and assess the liquidity implication.
108. A bank has Tier 1 capital of Rs. 700 crore and total exposure of Rs. 22,000 crore. Does it meet the Basel III Leverage Ratio requirement?

### Regulatory Edge Cases
109. A customer asks whether their joint account with a spouse and their individual savings account at the same bank are each insured up to the FDIC limit separately.
110. A bank employee is approached by a customer offering a bribe to approve a loan without proper KYC. What are the bank's obligations under AML and whistleblower rules?
111. A customer insists their transaction is legitimate but refuses to explain the source of funds. Can the bank file an STR without informing the customer?
112. A corporate customer changes its beneficial ownership structure so that no individual now owns more than 24%. Does this remove the CDD obligation?
113. A bank in India receives a request for customer data from a foreign regulator. What is the correct procedure under RBI guidelines?
114. A payment of Rs. 4.8 lakhs is made via wire transfer to an account in a FATF non-compliant jurisdiction. Does this trigger a reporting obligation?
115. A customer claims that splitting a Rs. 15 lakh transaction into three parts over three branches on the same day is legal. Is it and what should the bank do?
116. A customer's loan was written off two years ago. They now want to open a new account. What is the bank's obligation?

### Product & Concept Clarity
117. Explain the difference between a Non-Performing Asset, a Stressed Asset, and a Written-Off Asset.
118. What is the difference between the Marginal Standing Facility and the Liquidity Adjustment Facility?
119. A customer asks why their EBLR-linked home loan EMI increased even though they did not miss any payments. Explain what happened.
120. What is the difference between Gross NPA ratio and Net NPA ratio and why do analysts look at both?

---

## How to run this evaluation

```python
results = []

for query, mode in zip(queries, modes):
    result = run_query(query, mode=mode)
    results.append({
        "query": query,
        "mode": mode,
        "answer": result["answer"],
        "chunks_retrieved": result["retrieved_chunks"],
        "latency_ms": result["latency_ms"],
        "confidence": result["confidence"],
        "grounded": result["grounded"],
    })
```

For each query, record:
- Which source chunks were retrieved (rank 1 to 5)
- Whether the answer referenced the retrieved content (groundedness)
- Whether the answer fully addressed the question (completeness)
- Response latency in milliseconds
- For Auto mode: which model was selected and the score difference

---

*Evaluation set for [banking-genai-portfolio](https://github.com/rakeshmadasaniai/banking-genai-portfolio) by Ram (Rakesh) Madasani*
