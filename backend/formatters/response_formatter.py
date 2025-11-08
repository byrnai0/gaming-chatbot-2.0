#response formatter to human text
from backend.main import Response

def format_response(data: Response) -> str:
    """
    Convert the Pydantic Response object into a clean human-facing text output.
    Skips empty fields. Auto-places RAWG metadata at top only for metadata queries.
    SMART placement of HLTB game length.
    """

    lines = []

    # Auto place RAWG + length at top for metadata topic
    if data.topic == "metadata":
        if data.rawg_data:
            lines.append(data.rawg_data.strip())
        if data.game_length:
            lines.append(data.game_length.strip())

    # Summary at top if available
    if data.summary:
        lines.append(data.summary.strip())

    # Plot — No Spoilers
    if data.no_spoilers:
        lines.append(f"**Plot:**\n{data.no_spoilers.strip()}")

    # Plot — With Spoilers
    if data.spoilers:
        if data.warning:
            lines.append(f"**{data.warning}**")
        lines.append(f"**Full Plot:**\n{data.spoilers.strip()}")

    # Lore
    if data.lore:
        lines.append(f"**Lore:**\n{data.lore.strip()}")

    # Tips / Tricks
    if data.game_tips:
        lines.append(f"**Tips:**\n{data.game_tips.strip()}")

    # Wikipedia data (non-plot topics only)
    if data.wiki_data and data.topic not in ["plot", "spoilers"]:
        lines.append(f"**From Wiki:**\n{data.wiki_data.strip()}")

    # Non metadata topics for RAWG + length at bottom
    if data.topic != "metadata":
        # RAWG metadata at bottom
        if data.rawg_data:
            lines.append(f"**Info:** {data.rawg_data.strip()}")

        # SMART length placement:
        # Show only if relevant (non-plot topics)
        if data.game_length and data.topic not in ["plot", "spoilers"]:
            lines.append(data.game_length.strip())

    # Join non-empty lines
    final = "\n\n".join([x for x in lines if x.strip()])
    return final.strip()
