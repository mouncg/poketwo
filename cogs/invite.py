import logging
import os
import random
from datetime import datetime
from functools import cached_property

import dbl
import discord
from discord.ext import commands, flags

from .database import Database
from .helpers import checks, constants, converters, models, mongo


def setup(bot: commands.Bot):
    bot.add_cog(Invite(bot))


class Invite(commands.Cog):
    """For basic bot operation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self) -> Database:
        return self.bot.get_cog("Database")

    @commands.command()
    async def invitetop(self, ctx: commands.Context):
        if ctx.guild.id != self.bot.guild.id:
            return

        top = await mongo.db.member.aggregate(
            [{"$project": {"invites": 1}}, {"$sort": {"invites": -1}}, {"$limit": 10}]
        ).to_list(None)
        print(top)
        top = [(self.bot.guild.get_member(x["_id"]), x["invites"]) for x in top]

        embed = discord.Embed()
        embed.color = 0xF44336
        embed.title = "Top Inviters"

        embed.description = "\n".join(f"**{member}** • {invites} users" for member, invites in top)

        await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.command()
    async def invreward(
        self, ctx: commands.Context, member: discord.Member, invreward: int
    ):
        update = {"$inc": {}}
        species = None

        msg = None

        if invreward - 1 == 0:
            update["$inc"]["balance"] = 1000
            msg = "You received **1,000 Pokécoins**!"
        elif invreward - 1 == 2:
            update["$inc"]["balance"] = 3000
            msg = "You received **3,000 Pokécoins**!"
        elif invreward - 1 == 5:
            species = random.randint(144, 146)
            msg = f"You received **{models.GameData.species_by_number(species)}**!"
        elif invreward - 1 == 8:
            species = 10094
            msg = f"You received **{models.GameData.species_by_number(species)}** and **6,000 Pokécoins**!"
            update["$inc"]["balance"] = 6000
        elif invreward - 1 == 11:
            species = random.randint(380, 381)
            update["$inc"]["balance"] = 10000
            msg = f"You received **{models.GameData.species_by_number(species)}** and **10,000 Pokécoins**!"
        elif invreward - 1 == 14:
            update["$inc"]["redeems"] = 1
            msg = f"You received **1 redeem**! Type `p!redeem` for more information!"
        elif invreward - 1 == 19:
            species = random.choice((151, 251, 385, 386))
            msg = f"You received **{models.GameData.species_by_number(species)}**!"
        elif invreward - 1 == 24:
            species = random.choice((10080, 10081, 10082, 10083, 10084))
            msg = f"You received **{models.GameData.species_by_number(species)}**!"
        elif invreward - 1 == 29:
            update["$inc"]["balance"] = 15000
            msg = "You received **15,000 Pokécoins**!"

        if len(update["$inc"]) == 0:
            del update["$inc"]

        if species is not None:
            update["$push"] = {
                "pokemon": {
                    "species_id": species,
                    "level": 1,
                    "xp": 0,
                    "nature": mongo.random_nature(),
                    "iv_hp": mongo.random_iv(),
                    "iv_atk": mongo.random_iv(),
                    "iv_defn": mongo.random_iv(),
                    "iv_satk": mongo.random_iv(),
                    "iv_sdef": mongo.random_iv(),
                    "iv_spd": mongo.random_iv(),
                    "shiny": random.randint(1, 4096) == 1,
                }
            }

        await self.db.update_member(member, update)

        if msg is not None:
            await member.send(
                f"Thanks for inviting **{invreward} user{'' if invreward == 1 else 's'}** to our official server! {msg}"
            )

            await ctx.send("Done")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()

        self.bot.guild = self.bot.get_guild(716390832034414685)
        self.bot.invites = {x.code: x for x in await self.bot.guild.invites()}
        self.bot.invited_ids = set()

    async def add_invites(self, member):
        data = await self.db.fetch_member_info(member)

        if data is None:
            return

        update = {"$inc": {"invites": 1}}

        species = None

        msg = None

        if data.invites == 0:
            update["$inc"]["balance"] = 1000
            msg = "You received **1,000 Pokécoins**!"
        elif data.invites == 2:
            update["$inc"]["balance"] = 3000
            msg = "You received **3,000 Pokécoins**!"
        elif data.invites == 5:
            species = random.randint(144, 146)
            msg = f"You received **{models.GameData.species_by_number(species)}**!"
        elif data.invites == 8:
            species = 10094
            msg = f"You received **{models.GameData.species_by_number(species)}** and **6,000 Pokécoins**!"
            update["$inc"]["balance"] = 6000
        elif data.invites == 11:
            species = random.randint(380, 381)
            update["$inc"]["balance"] = 10000
            msg = f"You received **{models.GameData.species_by_number(species)}** and **10,000 Pokécoins**!"
        elif data.invites == 14:
            update["$inc"]["redeems"] = 1
            msg = f"You received **1 redeem**! Type `p!redeem` for more information!"
        elif data.invites == 19:
            species = random.choice((151, 251, 385, 386))
            msg = f"You received **{models.GameData.species_by_number(species)}**!"
        elif data.invites == 24:
            species = random.choice((10080, 10081, 10082, 10083, 10084))
            msg = f"You received **{models.GameData.species_by_number(species)}**!"
        elif data.invites == 29:
            update["$inc"]["balance"] = 15000
            msg = "You received **15,000 Pokécoins**!"

        if species is not None:
            update["$push"] = {
                "pokemon": {
                    "species_id": species,
                    "level": 1,
                    "xp": 0,
                    "nature": mongo.random_nature(),
                    "iv_hp": mongo.random_iv(),
                    "iv_atk": mongo.random_iv(),
                    "iv_defn": mongo.random_iv(),
                    "iv_satk": mongo.random_iv(),
                    "iv_sdef": mongo.random_iv(),
                    "iv_spd": mongo.random_iv(),
                    "shiny": random.randint(1, 4096) == 1,
                }
            }

        await self.db.update_member(member, update)

        if msg is not None:
            await member.send(
                f"Thanks for inviting **{data.invites + 1} user{'' if data.invites == 0 else 's'}** to our official server! {msg}"
            )

    @commands.is_owner()
    @commands.command()
    async def addinv(self, ctx: commands.Context, member: discord.Member, amt: int):
        if amt > 10:
            return await ctx.send("Too much!")

        for i in range(amt):
            await self.add_invites(member)

        return await ctx.send("Done")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != self.bot.guild.id:
            return

        oldinvites = self.bot.invites
        newinvites = {x.code: x for x in await self.bot.guild.invites()}
        self.bot.invites = newinvites

        if member.id in self.bot.invited_ids:
            return

        if member.created_at > datetime(2020, 6, 14, 0, 0):
            return

        self.bot.invited_ids.add(member.id)

        inv = next(
            x
            for x in newinvites.values()
            if (x.code not in oldinvites and x.uses > 0)
            or (x.code in oldinvites and x.uses - oldinvites[x.code].uses > 0)
        )

        logging.info(f"NEW INVITE: {inv.inviter.id} invited {member.id}")

        await self.add_invites(inv.inviter)