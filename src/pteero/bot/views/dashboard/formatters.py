import disnake

from pteero.services.pterodactyl.schemas import (
    ServerResourceResponse,
    ServerState,
)

STATE_EMOJIS = {
    ServerState.RUNNING: "🟢",
    ServerState.STARTING: "🟡",
    ServerState.STOPPING: "🔴",
    ServerState.OFFLINE: "🔴",
}


def _format_bytes(bytes_val: int) -> str:
    """Converts a value in bytes to a human-readable string.

    Args:
        bytes_val: The size in bytes to convert.

    Returns:
        A formatted string representing the size in megabytes or gigabytes.
    """
    mb = bytes_val / (1024 * 1024)

    if mb >= 1024:
        return f"{mb / 1024:.2f} GB"

    return f"{mb:.2f} MB"


def _format_uptime(uptime_ms: int) -> str:
    """Converts milliseconds into a readable uptime string.

    Calculates the days, hours, and minutes from the provided millisecond
    value and formats it into a compact string (e.g., '1d 5h 30m').

    Args:
        uptime_ms: The total uptime duration in milliseconds.

    Returns:
        A formatted string representing the duration.
    """
    total_seconds = uptime_ms // 1000
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}m")

    return " ".join(parts)


def build_dashboard_embed(
    resources: ServerResourceResponse, server_name: str | None = None
) -> disnake.Embed:
    """Builds a server dashboard embed.

    Args:
        resources: The server resource data returned from the Pterodactyl API.
        server_name (optional): The human-readable name of the server.

    Returns:
        A `disnake.Embed` object.
    """
    state = resources.attributes.current_state
    stats = resources.attributes.resources
    state_emoji = STATE_EMOJIS.get(state, "⚪")

    embed = disnake.Embed(
        title=(
            f"🎮 Панель керування - {server_name}"
            if server_name
            else "🎮 Панель керування"
        ),
        color=disnake.Color.blurple(),
    )
    embed.add_field(
        name=f"{state_emoji} Стан", value=f"{state.value.upper()}", inline=False
    )

    if stats and state in {ServerState.STARTING, ServerState.RUNNING}:
        embed.add_field(name="💻 ЦПУ", value=f"{stats.cpu_absolute:.2f}%")
        embed.add_field(name="🧠 ОЗУ", value=f"{_format_bytes(stats.memory_bytes)}")
        embed.add_field(name="💽 Диск", value=f"{_format_bytes(stats.disk_bytes)}")
        embed.add_field(
            name="⬇️ Мережа (Вхід)", value=f"{_format_bytes(stats.network_rx_bytes)}"
        )
        embed.add_field(
            name="⬆️ Мережа (Вихід)", value=f"{_format_bytes(stats.network_tx_bytes)}"
        )
        embed.add_field(name="⏳ Час роботи", value=f"{_format_uptime(stats.uptime)}")

    embed.set_footer(text="Автоматично оновлюється щохвилини.")

    return embed
