import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("COLLEGE_SCORECARD_API_KEY")

BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools.json"



def fetch_college_data():
    all_records = []

    page = 0
    per_page = 100
    expected_total = None

    while True:
        params = {
            "api_key": API_KEY,
            "page": page,
            "per_page": per_page,
            "fields": ",".join(
                [
                    "id",
                    "school.name",
                    "school.city",
                    "school.state",
                    "school.zip",
                    "school.ownership",
                    "school.locale",
                    "location.lat",
                    "location.lon",
                    "latest.student.size",
                    "latest.admissions.admission_rate.overall",
                    "latest.cost.avg_net_price.overall",
                    "latest.completion.rate_suppressed.overall",
                    "latest.earnings.10_yrs_after_entry.median",
                ]
            ),
        }

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        records = data.get("results", [])

        if expected_total is None:
            expected_total = data.get("metadata", {}).get("total")

            if not isinstance(expected_total, int):
                raise ValueError(
                    "API response is missing a valid metadata.total"
                )

            if expected_total <= 0:
                raise ValueError(
                    "API reported no records"
                )

            print(f"Expected records: {expected_total}")

        if not records:
            break

        all_records.extend(records)

        print(
            f"Fetched page {page}: {len(records)} records "
            f"(total: {len(all_records)}/{expected_total})"
        )

        if len(all_records) >= expected_total:
            break

        page += 1

    if len(all_records) != expected_total:
        raise ValueError(
            f"Incomplete API download: expected "
            f"{expected_total}, received {len(all_records)}"
        )
    school_ids = [record["id"] for record in all_records]

    if len(school_ids) != len(set(school_ids)):
        raise ValueError(
            "Duplicate school IDs detected during API ingestion. "
            "Pipeline stopped."
        )

    print("API pagination and school ID uniqueness verified.")

    print("API pagination verified successfully.")

    return {"results": all_records}

def save_raw_data(data):
    project_root = Path(__file__).resolve().parents[3]

    output_path = (
        project_root
        / "data"
        / "raw"
        / "college_scorecard_raw.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
        )

    print(f"Raw data saved to: {output_path}")


def main():
    if not API_KEY:
        raise ValueError(
            "COLLEGE_SCORECARD_API_KEY is missing. Check your .env file."
        )

    data = fetch_college_data()

    print(
        f"Records received: "
        f"{len(data.get('results', []))}"
    )

    save_raw_data(data)


if __name__ == "__main__":
    main()