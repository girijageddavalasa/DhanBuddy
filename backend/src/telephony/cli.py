import argparse
import asyncio
from dataclasses import asdict

from dotenv import load_dotenv

from telephony.outbound import make_outbound_call


def parse_args():
    parser = argparse.ArgumentParser(description="Place one consented DhanBuddy outbound call.")
    parser.add_argument("--recipient", required=True, help="Controlled test number in E.164 format.")
    parser.add_argument("--purpose", choices=("financial_check_in", "document_follow_up"), required=True)
    parser.add_argument("--user-id", required=True, help="Anonymous DhanBuddy user ID.")
    parser.add_argument("--confirmed-opt-in", action="store_true")
    return parser.parse_args()


async def main() -> None:
    load_dotenv(".env.local")
    args = parse_args()
    result = await make_outbound_call(
        args.recipient, args.purpose, args.user_id,
        confirmed_opt_in=args.confirmed_opt_in,
    )
    print(asdict(result))


if __name__ == "__main__":
    asyncio.run(main())
