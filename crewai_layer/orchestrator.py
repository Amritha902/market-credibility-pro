# crewai_layer/orchestrator.py

from crewai_layer.agents.entity_solver_agent import EntitySolverAgent
from crewai_layer.agents.exchange_history_agent import ExchangeHistoryAgent
from crewai_layer.agents.news_agent import NewsAgent
from crewai_layer.agents.regulator_scraper_agent import RegulatorScraperAgent
from crewai_layer.agents.document_forensics_agent import DocumentForensicsAgent
from crewai_layer.agents.registry_lookup_agent import RegistryLookupAgent
from crewai_layer.agents.llm_explainer_agent import LLMExplainerAgent
from crewai_layer.agents.risk_pattern_agent import RiskPatternAgent
from crewai_layer.agents.guidance_agent import GuidanceAgent
from crewai_layer.agents.nse_scraper_agent import NSEScraperAgent
from crewai_layer.agents.bse_scraper_agent import BSEScraperAgent
from crewai_layer.agents.sebi_scraper_agent import SEBIScraperAgent
from crewai_layer.agents.pdf_ingest_agent import PDFIngestAgent
from crewai_layer.agents.csv_ingest_agent import CSVIngestAgent

def run_credibility_crew(claim: str, lookup: dict | None = None, strict: bool = False) -> dict:
    """
    Orchestrates all agents to evaluate a claim.
    Always runs EntitySolver first, then scrapers, registry, risk, guidance, etc.
    Returns a unified dict suitable for chat.py
    """
    agents = [
        EntitySolverAgent(),       # must run first
        ExchangeHistoryAgent(),
        NewsAgent(),
        RegulatorScraperAgent(),
        DocumentForensicsAgent(),
        RegistryLookupAgent(),
        NSEScraperAgent(),
        BSEScraperAgent(),
        SEBIScraperAgent(),
        PDFIngestAgent(),
        CSVIngestAgent(),
        RiskPatternAgent(),
        GuidanceAgent(),
        LLMExplainerAgent(),       # explanation last
    ]

    # initialize
    merged = {
        "verdict_text": "unknown",
        "reasons": [],
        "references": [],
        "confirmed_by": [],
        "silent_or_missing": [],
        "entity_info": {},
        "history_flags": {},
        "guidance": [],
        "agent_errors": {}
    }

    # run agents
    for agent in agents:
        try:
            res = agent.run(claim, lookup=lookup or {})
            if not isinstance(res, dict):
                continue

            # --- Merge rules ---
            if "entity" in res and not merged["entity_info"]:
                merged["entity_info"] = res["entity"]

            if "verdict" in res:
                if strict or merged["verdict_text"] in ("unknown", "unverified", "needs_official_link"):
                    merged["verdict_text"] = res["verdict"]

            if "reasons" in res:
                merged["reasons"].extend(res["reasons"])

            if "references" in res:
                merged["references"].extend(res["references"])

            if "confirmed_by" in res:
                merged["confirmed_by"].extend(res["confirmed_by"])

            if "silent_or_missing" in res:
                merged["silent_or_missing"].extend(res["silent_or_missing"])

            if "history_flags" in res and res["history_flags"]:
                merged["history_flags"].update(res["history_flags"])

            if "guidance" in res:
                merged["guidance"].extend(res["guidance"])

            if "ai_explainer" in res:   # from LLMExplainerAgent
                merged["ai_explainer"] = res["ai_explainer"]

        except Exception as e:
            merged["agent_errors"][agent.__class__.__name__] = str(e)

    # deduplicate
    merged["reasons"] = list(dict.fromkeys(merged["reasons"]))
    merged["references"] = list(dict.fromkeys(merged["references"]))
    merged["confirmed_by"] = list(dict.fromkeys(merged["confirmed_by"]))
    merged["silent_or_missing"] = list(dict.fromkeys(merged["silent_or_missing"]))
    merged["guidance"] = list(dict.fromkeys(merged["guidance"]))

    return merged
