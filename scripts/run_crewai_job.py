import argparse
from crewai_layer.crew_orchestrator import run_crewai_check

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--claim", required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--company", default="")
    args = parser.parse_args()

    res = run_crewai_check(args.claim, args.url, args.company)
    print(res)
