from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import disnake
from disnake.ext import commands, tasks

from pteero.bot.views.dashboard import DashboardView, build_dashboard_embed

if TYPE_CHECKING:
    from pteero.bot.bot import PteeroBot
    from pteero.core.repositories.dashboard import DashboardRecord

logger = logging.getLogger(__name__)


class DashboardCog(commands.Cog):
    """Cog for managing Pterodactyl server dashboards."""

    def __init__(self, bot: PteeroBot) -> None:
        """Initializes the class.

        Args:
            bot: The Discord bot instance.
        """
        self.bot: PteeroBot = bot
        self.update_dashboards.start()

    def cog_unload(self) -> None:
        """Cancels the update task, when cog is unloaded."""
        self.update_dashboards.cancel()

    async def _get_channel(self, channel_id: int) -> disnake.TextChannel | None:
        """Retrieves or fetches a text channel by its ID.

        Attempts to get the channel from the bot's internal cache. If it is not
        cached, it makes an API call to fetch it.

        Args:
            channel_id: The ID of the channel to retrieve.

        Returns:
            The text channel if found, otherwise `None`.
        """
        channel = self.bot.get_channel(channel_id)

        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except (disnake.NotFound, disnake.Forbidden):
                logger.warning(f"Channel '{channel_id}' not found or access denied.")
                return None

        return channel if isinstance(channel, disnake.TextChannel) else None

    async def _restore_dashboards(self) -> None:
        """Restores dashboard views from the database upon bot restart."""
        records = await self.bot.dashboards.get_all()

        restored_count = 0
        for record in records:
            view = DashboardView(self.bot, record.server_id)
            self.bot.add_view(view, message_id=record.message_id)

            restored_count += 1

        logger.info(
            f"The buttons for the {restored_count} control panels have been restored."
        )

    async def _process_single_dashboard(self, record: DashboardRecord) -> None:
        """Processes a single dashboard update concurrently.

        Args:
            record: The dashboard database record to update.
        """

        resources = await self.bot.ptero.get_server_resources(record.server_id)
        if not resources:
            return

        channel = await self._get_channel(record.channel_id)
        if not channel:
            logger.warning(
                f"Channel '{record.channel_id}' not found. Removing dashboard '{record.message_id}' from the database."
            )
            await self.bot.dashboards.remove(record.message_id)
            return

        try:
            embed = build_dashboard_embed(resources)
            message = channel.get_partial_message(record.message_id)
            await message.edit(embed=embed)
        except disnake.NotFound:
            logger.warning(
                f"Dashboard message '{record.message_id}' was deleted by a user. Removing from the database."
            )
            await self.bot.dashboards.remove(record.message_id)
        except disnake.HTTPException as e:
            logger.error(
                f"Discord API error editing dashboard '{record.message_id}': {e}"
            )

    @tasks.loop(seconds=60.0)
    async def update_dashboards(self) -> None:
        """Background task that updates server dashboards."""
        records = await self.bot.dashboards.get_all()

        try:
            async with asyncio.TaskGroup() as task_group:
                for record in records:
                    task_group.create_task(self._process_single_dashboard(record))
        except ExceptionGroup as e:
            logger.error(f"Multiple errors occurred during dashboard update cycle: {e}")

    @update_dashboards.before_loop
    async def before_update_dashboards(self) -> None:
        """Waits until the bot is fully ready before starting the update loop.

        This also triggers the restoration of the dashboard views to ensure
        interactivity survives a restart.
        """
        await self.bot.wait_until_ready()
        await self._restore_dashboards()

    @commands.is_owner()
    @commands.slash_command(
        name="dashboard",
        description="📊 Створює панель керування для вказаного сервера.",
    )
    async def spawn_dashboard(
        self, interaction: disnake.ApplicationCommandInteraction, server_id: str
    ) -> None:
        """Spawns an interactive dashboard for the specified server.

        Args:
            interaction: The interaction context from the slash command.
            server_id: The unique identifier for the Pterodactyl server.
        """
        await interaction.response.defer()

        resources = await self.bot.ptero.get_server_resources(server_id)

        if not resources:
            embed = disnake.Embed(
                title="⚠️ Помилка",
                description="Не вдалося під'єднатися до сервера.\nПеревірте ID сервера та спробуйте ще раз.",
                color=disnake.Color.yellow(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = build_dashboard_embed(resources)
        view = DashboardView(self.bot, server_id)
        await interaction.followup.send(embed=embed, view=view)

        message = await interaction.original_response()
        await self.bot.dashboards.add(server_id, interaction.channel_id, message.id)

        logger.info(f"Successfully saved dashboard for '{server_id}' to the database.")


def setup(bot: PteeroBot) -> None:
    """Loads the DashboardCog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    bot.add_cog(DashboardCog(bot))
