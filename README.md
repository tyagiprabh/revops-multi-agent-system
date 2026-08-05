# 🤖 RevOps Multi-Agent System

An autonomous, multi-agent RevOps workflow designed to audit CRM data hygiene and analyze conversational intelligence (call transcripts) for deal pipeline risk.

This project demonstrates how to move beyond basic LLM chatbots into **action-oriented AI agents** that can read relational data, enforce company standards, cross-reference datasets, and output structured operational intelligence.

## 🎯 The Use Case

Revenue Operations (RevOps) teams struggle with two major data problems:
1. **Dirty CRM Data:** Reps input poorly formatted data, use wrong abbreviations, or let deals go stale.
2. **"Happy Ears" Forecasting:** The CRM might say a deal is "80% likely to close," but the actual sales call transcript reveals massive budget objections.

This system solves both using a two-step AI agent architecture.

---

## 🧠 The Agents

### 1. The CRM Janitor (`crm_hygiene_agent.md`)
Acts as the gatekeeper for data quality.
* **Reads:** `dirty_crm_deals.csv` and `data_dictionary.md`
* **Action:** Standardizes formatting (casing, country codes), flags duplicates, and identifies deals that have gone stale based on activity SLA rules. 

### 2. The Pipeline Review Analyst (`pipeline_analyst_agent.md`)
Uncovers the "ground truth" of active sales deals.
* **Reads:** Clean CRM data and `gong_call_transcripts.json`.
* **Action:** Bypasses the CRM stage entirely, reads what the prospect *actually said* on the call, evaluates BANT (Budget, Authority, Need, Timeline), and flags high-risk deals for management review.

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Fake Data Generators Python] --> B(dirty_crm_deals.csv)
    A --> C(gong_call_transcripts.json)
    A --> D(dust_telemetry.json)
    
    B --> E[CRM Janitor Agent]
    F(data_dictionary.md) -.-> E
    E -->|Cleans & Flags| G[Clean CRM Data]
    
    G --> H[Pipeline Review Agent]
    C --> H
    H -->|Risk Assessment| I((Management Slack Alert))
