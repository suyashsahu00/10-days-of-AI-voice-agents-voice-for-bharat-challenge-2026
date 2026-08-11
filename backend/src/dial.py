import argparse
import asyncio
import os
import sys
from uuid import uuid4

from dotenv import load_dotenv
from livekit import api


async def main():
    load_dotenv(".env.local")

    parser = argparse.ArgumentParser(
        description="Trigger an outbound SIP call to Sydney voice agent."
    )
    parser.add_argument(
        "--to",
        type=str,
        required=True,
        help="Phone number to call in E.164 format (e.g. +91XXXXXXXXXX)",
    )
    parser.add_argument(
        "--room",
        type=str,
        default=None,
        help="Optional specific room name to use",
    )
    args = parser.parse_args()

    phone_number = args.to.strip()
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

    missing = []
    if not livekit_url:
        missing.append("LIVEKIT_URL")
    if not api_key:
        missing.append("LIVEKIT_API_KEY")
    if not api_secret:
        missing.append("LIVEKIT_API_SECRET")
    if not sip_trunk_id:
        missing.append("SIP_OUTBOUND_TRUNK_ID")

    if missing:
        print(
            f"Error: Missing required environment variables in .env.local: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    room_name = args.room or f"outbound-call-{uuid4().hex[:8]}"

    print(f"Connecting to LiveKit server at {livekit_url}...")
    lk_api = api.LiveKitAPI(livekit_url, api_key, api_secret)

    twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

    try:
        # Create room with explicit dispatch to outbound-agent
        print(f"Creating room '{room_name}' with outbound-agent dispatch...")
        await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                agents=[api.RoomAgentDispatch(agent_name="outbound-agent")],
            )
        )

        # Trigger outbound SIP call
        print(f"Dispatching SIP call to {phone_number} via trunk {sip_trunk_id}...")
        kwargs = {
            "sip_trunk_id": sip_trunk_id,
            "sip_call_to": phone_number,
            "room_name": room_name,
            "participant_identity": phone_number,
            "participant_name": phone_number,
        }
        if twilio_phone_number:
            kwargs["sip_number"] = twilio_phone_number

        sip_request = api.CreateSIPParticipantRequest(**kwargs)
        participant = await lk_api.sip.create_sip_participant(sip_request)
        print("Call successfully initiated!")
        print(f"Participant ID: {participant.participant_id}")
        print(f"Room Name: {room_name}")
    except Exception as e:
        print(f"Failed to initiate SIP call: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await lk_api.aclose()


if __name__ == "__main__":
    asyncio.run(main())
