import os
import requests
import json
import argparse
from pathlib import Path

URL = (
    "https://app.aikido.dev/api/issues/listGroupedIssues"
    "?search_term=&focus_mode=all_issues_mode&page=0&per_page=20"
    "&exclude_containers=false&dont_pass_team_context=false&filter_notes=all&exclude_old_closed_prs=true"
)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "x-cph": "1",
    "x-group-id": "46528",
    # If you prefer, you can move cookies into a requests.cookies.RequestsCookieJar
    "cookie": f"_vwo_uuid_v2=D6DF8455B8C8B3B87144E617147EE815B|a15da2de3bb7e6e3a9dd0c5464c7f087; _vwo_uuid=D6DF8455B8C8B3B87144E617147EE815B; _vis_opt_s=1%7C; _vis_opt_test_cookie=1; cookieyes-consent=consentid:RmswVU1XUDlOd0pseHRxdXV3TVpVMzlOcDE0emhzYTM,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes; _ga=GA1.1.1979925571.1762355972; _gcl_au=1.1.488622821.1762355972; FPAU=1.1.488622821.1762355972; hubspotutk=f769b7c636515fcab9b02b99e4351019; __hssrc=1; dd_anonymous_id=12df1a17-be45-4d38-95d2-a19eccd54927; _fbp=fb.1.1762355975409.635644805347767514; intercom-id-j0dzii6j=ae25911c-62d6-4ae3-b9a2-12db92c36f36; intercom-device-id-j0dzii6j=24cb27b4-9ba3-403f-8fbf-2686de02bd67; _vwo_ds=3%241762355969%3A52.4954869%3A%3A%3A%3A%3A1762431967%3A1762355969%3A2; __hstc=115122392.f769b7c636515fcab9b02b99e4351019.1762355973047.1762355973047.1762431983920.2; _clck=cbgrjn%5E2%5Eg0s%5E0%5E2135; locale=en; auth={os.environ.get('AIKIDO_AUTH_TOKEN', '')}; _rdt_uuid=1762355974320.8a2ac296-44d4-4aaa-a240-adc094e36350; _uetsid=d610fd70ba5a11f08780a35efbb8d177; _uetvid=d610f8f0ba5a11f084d633f94b96e880; _clsk=1k1135k%5E1762432280252%5E3%5E1%5Ek.clarity.ms%2Fcollect; _ga_NCP2435BFQ=GS2.1.s1762431972$o2$g1$t1762432441$j60$l0$h1536963071; intercom-session-j0dzii6j=WEV4SUlEZ2Z0TXdBVGNJMUhmeStHWklxL2FCNzhzWXlXRjQyZUxkbHUrOTREeEo1aVpLNlZOd3VaeDhScEhyOGQxZm9GWnBjdndBZ01qWldUeTJCS1ZIQ1lUeHVBS3RMUkpKaWxacFlrc009LS1IbzFuWFg5U3h4bzJUMjRyRjJxVC9BPT0=--1c23b13ed023f4395df4f8881ef8bf7b04d07926; _dd_s=logs=1&id=527fe178-0823-4f5f-a7e0-bf6dd8402097&created=1762432052615&expire=1762435752624"
}

def fetch(url: str = URL, headers: dict = HEADERS, timeout: int = 20):

    resp.raise_for_status()
    return resp.json()

# new helper: recursively find any "id" values in the fetched list payload
def find_ids(obj):
    ids = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "id" and (isinstance(v, int) or (isinstance(v, str) and v.isdigit())):
                ids.append(int(v))
            else:
                ids.extend(find_ids(v))
    elif isinstance(obj, list):
        for item in obj:
            ids.extend(find_ids(item))
    return ids

# query string used in the curl examples
DETAIL_QS = (
    "filter_repo_id=-1&filter_cloud_id=-1&filter_cloud_repo_id=-1&filter_domain_id=-1"
    "&filter_team_id=-1&filter_my_teams=false&exclude_containers=false&filter_out_of_sla=false"
    "&filter_due_soon=false&filter_instance_group_id=-1&disable_toasts=true&filter_single_issue_id=-1"
    "&allow_performance_filtering=true&exclude_old_closed_prs=true&filter_new_issues=false"
)

# template with placeholder for the id exactly where requested
DETAIL_URL_TEMPLATE = "https://app.aikido.dev/api/issues/{id}/detailGroupedIssues?"

def main():
    parser = argparse.ArgumentParser(description="Fetch Aikido grouped issues and per-id details.")
    parser.add_argument("-o", "--output", help="Write pretty JSON to file (default: aikido.json)", type=Path)
    args = parser.parse_args()

    # fetch the list response
    list_data = fetch()
    # collect ids (deduplicated, keep order)
    raw_ids = find_ids(list_data)
    seen = set()
    ids = []
    for i in raw_ids:
        if i not in seen:
            ids.append(i)
            seen.add(i)

    if not ids:
        print("No ids found in list response; aborting.")
        return

    results = {}
    for id_ in ids:
        # ensure we insert the id into the path exactly as in the curl:
        detail_url = DETAIL_URL_TEMPLATE.format(id=int(id_)) + DETAIL_QS
        try:
            detail = fetch(url=detail_url)
            results[str(id_)] = detail
            print(f"fetched detail for id={id_}")
        except requests.HTTPError as e:
            print(f"failed id={id_}: {e}")

    out_path = args.output or Path(__file__).parent / "aikido.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote details for {len(results)} ids to {out_path}")

if __name__ == "__main__":
    main()