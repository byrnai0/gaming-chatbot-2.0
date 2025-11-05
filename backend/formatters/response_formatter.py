# filename: backend/formatters/response_formatter.py

from backend.main import Response

def format_response(data: Response) -> str:
    """
    Convert the Pydantic Response object into a clean human-facing text output.
    Skips empty fields. Auto-places RAWG metadata at top only for metadata queries.
    SMART placement of HLTB game length.
    No emojis. Semi-chatty, clean tone.
    """

    lines = []

    # -------------------------
    # AUTO-PLACE RAWG METADATA + LENGTH (RL order) for METADATA TOPIC
    # -------------------------
    if data.topic == "metadata":
        if data.rawg_data:
            lines.append(data.rawg_data.strip())
        if data.game_length:
            lines.append(data.game_length.strip())

    # -------------------------
    # SUMMARY (general overview)
    # -------------------------
    if data.summary:
        lines.append(data.summary.strip())

    # -------------------------
    # PLOT — SPOILER-FREE
    # -------------------------
    if data.no_spoilers:
        lines.append(f"**Plot:**\n{data.no_spoilers.strip()}")

    # -------------------------
    # PLOT — SPOILERS
    # -------------------------
    if data.spoilers:
        if data.warning:
            lines.append(f"**{data.warning}**")
        lines.append(f"**Full Plot:**\n{data.spoilers.strip()}")

    # -------------------------
    # LORE
    # -------------------------
    if data.lore:
        lines.append(f"**Lore:**\n{data.lore.strip()}")

    # -------------------------
    # TIPS
    # -------------------------
    if data.game_tips:
        lines.append(f"**Tips:**\n{data.game_tips.strip()}")

    # -------------------------
    # WIKIPEDIA RAW EXTRACT (rarely shown)
    # Only show if LLM stored some text here
    # -------------------------
    if data.wiki_data and data.topic not in ["plot", "spoilers"]:
        lines.append(f"**From Wiki:**\n{data.wiki_data.strip()}")

    # -------------------------
    # NON-METADATA TOPICS — Add RAWG + SMART LENGTH at bottom
    # -------------------------
    if data.topic != "metadata":
        # RAWG metadata at bottom
        if data.rawg_data:
            lines.append(f"**Info:** {data.rawg_data.strip()}")

        # SMART length placement:
        # Show only if relevant (non-plot topics)
        if data.game_length and data.topic not in ["plot", "spoilers"]:
            lines.append(data.game_length.strip())

    # -------------------------
    # Join and return
    # -------------------------
    final = "\n\n".join([x for x in lines if x.strip()])
    return final.strip()
